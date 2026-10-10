"""
Train the Variational Autoencoder (VAE) for anomaly detection.

Key improvements over the original autoencoder training:
- VAE loss (reconstruction + KL divergence) with beta annealing
- Multi-scale reconstruction loss
- Adaptive per-class threshold computation (F1-optimised)
- Cosine annealing LR scheduler
- Gradient clipping for stability
- Comprehensive evaluation metrics
- Tighter bottleneck (latent_dim=8) for better anomaly separation
- Gaussian noise injection (denoising VAE) with annealing schedule
"""
import os
import json
import torch
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import joblib
from tqdm import tqdm

from models.autoencoder import VariationalAutoencoder, vae_loss
from models.ensemble import compute_per_class_thresholds
from utils.preprocess import (
    load_and_split, APIRequestDataset, compute_normal_statistics
)
from utils.feature_extraction import NUM_FEATURES
from sklearn.preprocessing import RobustScaler
from torch.utils.data import DataLoader


def train_autoencoder():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    os.makedirs("saved_models", exist_ok=True)
    os.makedirs("plots", exist_ok=True)

    # ── Load data ────────────────────────────────────────────
    print("Loading dataset...")
    dataset_priority = [
        'data/combined_dataset.csv',
        'data/synthetic_v3_dataset.csv',
        'data/synthetic_dataset.csv',
    ]
    dataset_path = None
    for candidate in dataset_priority:
        if os.path.exists(candidate):
            dataset_path = candidate
            break
    if dataset_path is None:
        print("ERROR: No dataset found! Run data/combine_datasets.py first.")
        return
    print(f"  Using: {dataset_path}")

    X_train, X_val, X_test, y_train, y_val, y_test = load_and_split(
        dataset_path, test_size=0.15, val_size=0.15
    )
    input_dim = X_train.shape[1]
    print(f"  Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    print(f"  Input dim: {input_dim}")

    # Filter to ONLY normal traffic (label=0) for training the autoencoder
    train_normal_mask = (y_train == 0)
    X_train_normal = X_train[train_normal_mask]
    y_train_normal = y_train[train_normal_mask]
    print(f"  Normal training samples: {len(X_train_normal)}")

    # Normalize — fit scaler on normal training data only
    scaler = RobustScaler()
    X_train_norm = scaler.fit_transform(X_train_normal)
    X_val_norm = scaler.transform(X_val)
    X_test_norm = scaler.transform(X_test)

    # Compute and save normal mean for XAI (on scaled normal data)
    normal_mean = X_train_norm.mean(axis=0)
    np.save('saved_models/normal_mean.npy', normal_mean)

    # Also compute raw normal mean for XAI
    raw_normal_mean = compute_normal_statistics(X_train, y_train)
    np.save('saved_models/raw_normal_mean.npy', raw_normal_mean)

    # Create dataloaders
    train_dataset = APIRequestDataset(X_train_norm, y_train_normal)
    val_dataset = APIRequestDataset(X_val_norm, y_val)
    train_loader = DataLoader(train_dataset, batch_size=128, shuffle=True, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=128, shuffle=False, pin_memory=True)

    # ── Model ────────────────────────────────────────────────
    # Tighter bottleneck (latent_dim=8 instead of 16) forces the encoder
    # to compress harder, making it impossible to faithfully reconstruct
    # out-of-distribution attack traffic → larger anomaly scores for attacks.
    latent_dim = 8
    model = VariationalAutoencoder(input_dim=input_dim, latent_dim=latent_dim, dropout=0.2).to(device)
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = CosineAnnealingWarmRestarts(optimizer, T_0=20, T_mult=2, eta_min=1e-6)

    epochs = 200
    patience = 25
    best_val_loss = float('inf')
    epochs_no_improve = 0

    train_losses, val_losses = [], []
    kl_losses = []

    # Beta annealing: start at 0.0 and linearly increase to 1.0 over warmup_epochs
    beta_warmup = 30

    # Noise injection schedule: start at 0.1, ramp up to 0.3, then decay
    noise_peak = 0.3
    noise_warmup = 20
    noise_decay_start = 120

    print(f"\nTraining VAE ({input_dim} features, latent_dim={latent_dim})...")
    print(f"  Beta warmup: {beta_warmup} epochs")
    print(f"  Noise injection: peak={noise_peak}, warmup={noise_warmup}, decay_start={noise_decay_start}")
    print("-" * 70)

    for epoch in range(epochs):
        # Beta annealing schedule
        beta = min(1.0, epoch / beta_warmup)

        # Noise schedule: ramp up → plateau → decay
        if epoch < noise_warmup:
            noise_std = noise_peak * (epoch / noise_warmup)
        elif epoch < noise_decay_start:
            noise_std = noise_peak
        else:
            decay_progress = (epoch - noise_decay_start) / max(epochs - noise_decay_start, 1)
            noise_std = noise_peak * (1.0 - decay_progress)

        model.train()
        running_loss = 0.0
        running_kl = 0.0

        for X_batch, _ in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}", leave=False):
            X_batch = X_batch.to(device)
            optimizer.zero_grad()

            reconstruction, mu, logvar, ms_64, ms_128 = model(X_batch, noise_std=noise_std)
            # Reconstruction target is always the clean input
            loss, recon_loss, kl_loss = vae_loss(
                reconstruction, X_batch, mu, logvar, ms_64, ms_128, beta=beta
            )

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            running_loss += loss.item() * X_batch.size(0)
            running_kl += kl_loss.item() * X_batch.size(0)

        scheduler.step()

        train_loss = running_loss / len(train_loader.dataset)
        train_kl = running_kl / len(train_loader.dataset)
        train_losses.append(train_loss)

        # Validate on normal samples only
        model.eval()
        val_loss = 0.0
        val_normal_count = 0
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch = X_batch.to(device)
                mask = (y_batch == 0)
                if mask.sum() > 0:
                    reconstruction, mu, logvar, ms_64, ms_128 = model(X_batch[mask])
                    loss, _, _ = vae_loss(
                        reconstruction, X_batch[mask], mu, logvar, ms_64, ms_128, beta=beta
                    )
                    val_loss += loss.item() * mask.sum().item()
                    val_normal_count += mask.sum().item()

        val_loss = val_loss / max(val_normal_count, 1)
        val_losses.append(val_loss)

        lr = optimizer.param_groups[0]['lr']
        print(f"Epoch {epoch+1:3d}/{epochs} — Loss: {train_loss:.6f} | Val: {val_loss:.6f} | "
              f"KL: {train_kl:.4f} | β: {beta:.3f} | σ: {noise_std:.3f} | LR: {lr:.2e}")

        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            torch.save(model.state_dict(), 'saved_models/autoencoder.pth')
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"\nEarly stopping at epoch {epoch+1}")
                break

    # ── Load best model ──────────────────────────────────────
    model.load_state_dict(torch.load('saved_models/autoencoder.pth', weights_only=True))
    print("\nBest model loaded.")

    # Save scaler
    joblib.dump(scaler, 'saved_models/scaler.joblib')
    print("Scaler saved to saved_models/scaler.joblib")

    # ── Compute anomaly scores on validation set ─────────────
    model.eval()
    errors = []
    labels = []
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            X_batch = X_batch.to(device)
            err = model.get_reconstruction_error(X_batch).cpu().numpy()
            errors.extend(err)
            labels.extend(y_batch.numpy())

    errors = np.array(errors)
    labels = np.array(labels)

    normal_errors = errors[labels == 0]
    anomalous_errors = errors[labels != 0]

    print(f"\nReconstruction Error Statistics:")
    print(f"  Normal    — Mean: {normal_errors.mean():.6f}, Std: {normal_errors.std():.6f}, "
          f"Median: {np.median(normal_errors):.6f}")
    if len(anomalous_errors) > 0:
        print(f"  Anomalous — Mean: {anomalous_errors.mean():.6f}, Std: {anomalous_errors.std():.6f}, "
              f"Median: {np.median(anomalous_errors):.6f}")
        # Separation ratio — higher is better
        sep_ratio = anomalous_errors.mean() / max(normal_errors.mean(), 1e-8)
        print(f"  Separation ratio (anomalous/normal mean): {sep_ratio:.2f}x")

    # Global threshold (95th percentile of normal errors)
    global_threshold = float(np.percentile(normal_errors, 95))
    print(f"\nGlobal Threshold (P95 normal): {global_threshold:.6f}")

    # Per-class thresholds (F1-optimised)
    per_class_thresholds = compute_per_class_thresholds(errors, labels, percentile=95.0)
    print(f"Per-class thresholds:")
    label_names = {0: 'Normal', 1: 'SQLi', 2: 'XSS', 3: 'PathTraversal', 4: 'CmdInjection', 5: 'SSRF'}
    for lbl, thresh in sorted(per_class_thresholds.items()):
        name = label_names.get(lbl, f"Class_{lbl}")
        print(f"  {lbl} ({name}): {thresh:.6f}")

    # Detection rates per class
    unique_labels = np.unique(labels)
    print("\nDetection Rates (using global threshold):")
    for lbl in unique_labels:
        if lbl == 0:
            continue
        class_errors = errors[labels == lbl]
        detected = (class_errors > global_threshold).sum()
        print(f"  Class {int(lbl)} ({label_names.get(int(lbl), '?')}): "
              f"{detected}/{len(class_errors)} ({detected/len(class_errors)*100:.1f}%)")

    print("\nDetection Rates (using per-class thresholds):")
    for lbl in unique_labels:
        if lbl == 0:
            continue
        class_errors = errors[labels == lbl]
        thresh = per_class_thresholds.get(int(lbl), global_threshold)
        detected = (class_errors > thresh).sum()
        print(f"  Class {int(lbl)} ({label_names.get(int(lbl), '?')}): "
              f"{detected}/{len(class_errors)} ({detected/len(class_errors)*100:.1f}%)")

    # Save thresholds
    threshold_data = {
        'threshold': global_threshold,
        'per_class_thresholds': {str(k): v for k, v in per_class_thresholds.items()},
    }
    with open('saved_models/anomaly_threshold.json', 'w') as f:
        json.dump(threshold_data, f, indent=2)
    print("Thresholds saved to saved_models/anomaly_threshold.json")

    # ── Plots ────────────────────────────────────────────────
    # Training loss curve
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='Train Loss', linewidth=2)
    plt.plot(val_losses, label='Val Loss (Normal)', linewidth=2)
    plt.xlabel('Epoch')
    plt.ylabel('VAE Loss')
    plt.legend()
    plt.title('VAE Training Curve')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('plots/vae_loss.png', dpi=150)
    plt.close()

    # Anomaly distribution
    plt.figure(figsize=(12, 5))
    plt.hist(normal_errors, bins=80, alpha=0.6, label='Normal', density=True, color='#2ecc71')
    if len(anomalous_errors) > 0:
        plt.hist(anomalous_errors, bins=80, alpha=0.6, label='Anomalous', density=True, color='#e74c3c')
    plt.axvline(global_threshold, color='r', linestyle='dashed', linewidth=2,
                label=f'Threshold ({global_threshold:.4f})')
    plt.xlabel('Anomaly Score')
    plt.ylabel('Density')
    plt.legend()
    plt.title('VAE Anomaly Score Distribution: Normal vs Attack')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('plots/vae_anomaly_distribution.png', dpi=150)
    plt.close()

    # Per-class error distribution
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    colors = ['#2ecc71', '#e74c3c', '#3498db', '#f39c12', '#9b59b6', '#1abc9c']
    for idx, (lbl, name) in enumerate(label_names.items()):
        ax = axes[idx // 3][idx % 3]
        class_errors = errors[labels == lbl]
        if len(class_errors) > 0:
            ax.hist(class_errors, bins=50, alpha=0.7, color=colors[idx], density=True)
            ax.axvline(global_threshold, color='r', linestyle='dashed', linewidth=1.5)
            per_thresh = per_class_thresholds.get(lbl, global_threshold)
            if per_thresh != global_threshold:
                ax.axvline(per_thresh, color='orange', linestyle='dotted', linewidth=1.5,
                          label=f'Per-class ({per_thresh:.4f})')
                ax.legend(fontsize=8)
            ax.set_title(f'{name} (n={len(class_errors)})')
            ax.set_xlabel('Anomaly Score')
        else:
            ax.set_title(f'{name} (no samples)')
    plt.suptitle('Per-Class Anomaly Score Distribution', fontsize=14)
    plt.tight_layout()
    plt.savefig('plots/vae_per_class_distribution.png', dpi=150)
    plt.close()

    print("\nPlots saved to plots/")
    print("\n" + "=" * 60)
    print("VAE training complete!")
    print(f"  Latent dim: {latent_dim}")
    print(f"  Separation ratio: {sep_ratio:.2f}x" if len(anomalous_errors) > 0 else "")
    print("=" * 60)


if __name__ == "__main__":
    train_autoencoder()
