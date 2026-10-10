"""
Train the Deep Residual Classifier for API threat type classification.

Key improvements over the original classifier training:
- Focal Loss with label smoothing for class imbalance
- Mixup data augmentation for better generalisation
- Cosine annealing with warm restarts
- Gradient clipping
- Temperature calibration on validation set
- Saves raw logits for post-hoc calibration
- 6-class classification (added SSRF)
- WeightedRandomSampler for balanced batches
- Scaler fitted on normal data only (consistent with autoencoder & inference)
- Stochastic Weight Averaging (SWA) for better generalisation
"""
import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
from torch.optim.swa_utils import AveragedModel, SWALR
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
from sklearn.metrics import classification_report, confusion_matrix, f1_score
import seaborn as sns
import joblib

from models.classifier import DeepResidualClassifier, FocalLoss
from models.ensemble import TemperatureScaling
from utils.preprocess import (
    load_and_split, fit_scaler_on_normal, create_dataloaders, compute_class_weights
)


NUM_CLASSES = 6  # Normal, SQLi, XSS, PathTraversal, CmdInjection, SSRF

LABEL_MAPPING = {
    "0": "Normal",
    "1": "SQLi",
    "2": "XSS",
    "3": "PathTraversal",
    "4": "CommandInjection",
    "5": "SSRF",
}

# Dataset priority: combined (real) > synthetic_v3 > synthetic
DATASET_PRIORITY = [
    'data/combined_dataset.csv',
    'data/synthetic_v3_dataset.csv',
    'data/synthetic_dataset.csv',
]


def mixup_data(x, y, alpha=0.2):
    """Mixup augmentation: creates convex combinations of training pairs."""
    if alpha > 0:
        lam = np.random.beta(alpha, alpha)
    else:
        lam = 1.0

    batch_size = x.size(0)
    index = torch.randperm(batch_size, device=x.device)

    mixed_x = lam * x + (1 - lam) * x[index]
    y_a, y_b = y, y[index]
    return mixed_x, y_a, y_b, lam


def mixup_criterion(criterion, pred, y_a, y_b, lam):
    """Compute loss for mixup samples."""
    return lam * criterion(pred, y_a) + (1 - lam) * criterion(pred, y_b)


def train_classifier():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    os.makedirs("saved_models", exist_ok=True)
    os.makedirs("plots", exist_ok=True)

    # ── Load data ────────────────────────────────────────────
    print("Loading dataset...")
    dataset_path = None
    for candidate in DATASET_PRIORITY:
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

    # Determine number of classes from data
    num_classes = len(np.unique(np.concatenate([y_train, y_val, y_test])))
    num_classes = max(num_classes, NUM_CLASSES)

    print(f"  Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    print(f"  Input dim: {input_dim}, Classes: {num_classes}")

    # Print class distribution
    classes, counts = np.unique(y_train, return_counts=True)
    for cls, cnt in zip(classes, counts):
        name = LABEL_MAPPING.get(str(int(cls)), f"Class_{int(cls)}")
        print(f"    {int(cls)} ({name}): {cnt} ({cnt/len(y_train)*100:.1f}%)")

    # ── Normalize features ───────────────────────────────────
    # FIT SCALER ON NORMAL DATA ONLY — this is critical for consistency
    # with the autoencoder and the inference pipeline, which both use
    # a normal-data-only scaler.  The old code fitted on ALL data,
    # causing a distribution shift at inference time.
    scaler = fit_scaler_on_normal(X_train, y_train, robust=True)
    X_train_norm = scaler.transform(X_train)
    X_val_norm = scaler.transform(X_val)
    X_test_norm = scaler.transform(X_test)

    # Save the classifier's scaler (should match autoencoder's scaler)
    joblib.dump(scaler, 'saved_models/classifier_scaler.joblib')
    print("  Classifier scaler saved (fitted on normal data only).")

    # Create dataloaders with weighted sampling for class balance
    train_loader, val_loader, test_loader = create_dataloaders(
        X_train_norm, y_train, X_val_norm, y_val, X_test_norm, y_test,
        batch_size=256, shuffle=True, use_weighted_sampling=True
    )

    # ── Model & Loss ─────────────────────────────────────────
    # Compute class weights for Focal Loss
    class_weights = compute_class_weights(y_train, num_classes)
    class_weights_tensor = torch.tensor(class_weights, dtype=torch.float32).to(device)
    print(f"  Class weights: {[f'{w:.3f}' for w in class_weights]}")

    model = DeepResidualClassifier(
        input_dim=input_dim, num_classes=num_classes, dropout=0.3
    ).to(device)

    criterion = FocalLoss(
        alpha=class_weights_tensor, gamma=2.0, label_smoothing=0.05
    )
    optimizer = optim.AdamW(model.parameters(), lr=5e-4, weight_decay=1e-4)
    scheduler = CosineAnnealingWarmRestarts(optimizer, T_0=15, T_mult=2, eta_min=1e-6)

    # SWA (Stochastic Weight Averaging) for better generalisation
    swa_model = AveragedModel(model)
    swa_scheduler = SWALR(optimizer, swa_lr=1e-4)
    swa_start_epoch = 100  # Start SWA after 100 epochs

    epochs = 200
    patience = 30
    best_val_f1 = 0.0  # Track best F1 instead of loss
    best_val_loss = float('inf')
    epochs_no_improve = 0

    train_losses, val_losses = [], []
    train_accs, val_accs = [], []
    train_f1s, val_f1s = [], []

    use_mixup = True
    mixup_alpha = 0.2

    print(f"\nTraining Deep Residual Classifier ({input_dim} features, {num_classes} classes)...")
    print(f"  Focal Loss (γ=2.0, label_smoothing=0.05), Mixup (α={mixup_alpha})")
    print(f"  WeightedRandomSampler: ON, SWA starts at epoch {swa_start_epoch}")
    print("-" * 80)

    for epoch in range(epochs):
        # Disable mixup for last 10% of epochs (fine-tuning)
        epoch_mixup = use_mixup and epoch < int(epochs * 0.9)
        using_swa = epoch >= swa_start_epoch

        model.train()
        running_loss = 0.0
        all_preds, all_labels = [], []

        for X_batch, y_batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}", leave=False):
            X_batch, y_batch = X_batch.to(device), y_batch.to(device).long()

            optimizer.zero_grad()

            if epoch_mixup:
                mixed_x, y_a, y_b, lam = mixup_data(X_batch, y_batch, mixup_alpha)
                logits = model(mixed_x)
                loss = mixup_criterion(criterion, logits, y_a, y_b, lam)
                # For accuracy tracking, use original inputs
                with torch.no_grad():
                    orig_logits = model(X_batch)
                    preds = torch.argmax(orig_logits, dim=1)
            else:
                logits = model(X_batch)
                loss = criterion(logits, y_batch)
                preds = torch.argmax(logits, dim=1)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            running_loss += loss.item() * X_batch.size(0)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(y_batch.cpu().numpy())

        # LR scheduling
        if using_swa:
            swa_model.update_parameters(model)
            swa_scheduler.step()
        else:
            scheduler.step()

        train_loss = running_loss / len(train_loader.dataset)
        train_acc = np.mean(np.array(all_preds) == np.array(all_labels))
        train_f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)
        train_losses.append(train_loss)
        train_accs.append(train_acc)
        train_f1s.append(train_f1)

        # Validation
        model.eval()
        val_loss = 0.0
        all_preds, all_labels = [], []
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device).long()
                logits = model(X_batch)
                loss = criterion(logits, y_batch)

                val_loss += loss.item() * X_batch.size(0)
                preds = torch.argmax(logits, dim=1)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(y_batch.cpu().numpy())

        val_loss = val_loss / len(val_loader.dataset)
        val_acc = np.mean(np.array(all_preds) == np.array(all_labels))
        val_f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)
        val_losses.append(val_loss)
        val_accs.append(val_acc)
        val_f1s.append(val_f1)

        lr = optimizer.param_groups[0]['lr']
        swa_tag = " [SWA]" if using_swa else ""
        print(f"Epoch {epoch+1:3d}/{epochs} — "
              f"Train [L:{train_loss:.4f} A:{train_acc:.4f} F1:{train_f1:.4f}] | "
              f"Val [L:{val_loss:.4f} A:{val_acc:.4f} F1:{val_f1:.4f}] | "
              f"LR: {lr:.2e}{swa_tag}")

        # Early stopping on macro F1
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_val_loss = val_loss
            epochs_no_improve = 0
            torch.save(model.state_dict(), 'saved_models/classifier.pth')
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"\nEarly stopping at epoch {epoch+1}")
                break

    # ── Finalise SWA model ───────────────────────────────────
    if swa_start_epoch < epochs:
        # Update batch norm stats for the SWA model
        torch.optim.swa_utils.update_bn(train_loader, swa_model, device=device)

        # Evaluate SWA model on validation set
        swa_model.eval()
        swa_preds, swa_labels = [], []
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch = X_batch.to(device)
                logits = swa_model(X_batch)
                preds = torch.argmax(logits, dim=1)
                swa_preds.extend(preds.cpu().numpy())
                swa_labels.extend(y_batch.numpy())

        swa_f1 = f1_score(swa_labels, swa_preds, average='macro', zero_division=0)
        print(f"\nSWA model Val F1: {swa_f1:.4f} (vs best checkpoint F1: {best_val_f1:.4f})")

        # Use SWA model if it's better
        if swa_f1 > best_val_f1:
            print("  → SWA model is better, saving it as the final model.")
            torch.save(swa_model.module.state_dict(), 'saved_models/classifier.pth')
            best_val_f1 = swa_f1
        else:
            print("  → Checkpoint model is better, keeping it.")

    # ── Load best model ──────────────────────────────────────
    model.load_state_dict(torch.load('saved_models/classifier.pth', weights_only=True))
    print(f"\nBest model loaded (Val F1: {best_val_f1:.4f})")

    # ── Save label mapping ───────────────────────────────────
    with open('saved_models/label_mapping.json', 'w') as f:
        json.dump(LABEL_MAPPING, f, indent=2)
    print("Label mapping saved to saved_models/label_mapping.json")

    # ── Temperature Calibration ──────────────────────────────
    print("\nCalibrating confidence with temperature scaling...")
    model.eval()
    all_logits = []
    all_labels = []
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            X_batch = X_batch.to(device)
            logits = model(X_batch)
            all_logits.append(logits.cpu().numpy())
            all_labels.extend(y_batch.numpy())

    all_logits = np.concatenate(all_logits, axis=0)
    all_labels = np.array(all_labels)

    calibrator = TemperatureScaling()
    optimal_temp = calibrator.calibrate(all_logits, all_labels)
    print(f"  Optimal temperature: {optimal_temp:.4f}")

    with open('saved_models/temperature.json', 'w') as f:
        json.dump({'temperature': optimal_temp}, f)
    print("  Temperature saved to saved_models/temperature.json")

    # ── Final Evaluation on Test Set ─────────────────────────
    model.eval()
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            X_batch = X_batch.to(device)
            logits = model(X_batch)
            preds = torch.argmax(logits, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(y_batch.numpy())

    # Generate target names for all classes present in the data
    present_classes = sorted(set(all_labels) | set(all_preds))
    target_names = [LABEL_MAPPING.get(str(int(c)), f"Class_{int(c)}") for c in present_classes]

    print("\n" + "=" * 70)
    print("TEST SET Classification Report:")
    print("=" * 70)
    print(classification_report(
        all_labels, all_preds,
        labels=present_classes,
        target_names=target_names,
        zero_division=0
    ))

    # ── Confusion Matrix ─────────────────────────────────────
    cm = confusion_matrix(all_labels, all_preds, labels=present_classes)
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=target_names,
        yticklabels=target_names,
    )
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix — Deep Residual Classifier (Test Set)')
    plt.tight_layout()
    plt.savefig('plots/confusion_matrix.png', dpi=150)
    plt.close()

    # ── Training Metrics Plots ───────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    axes[0].plot(train_losses, label='Train', linewidth=2)
    axes[0].plot(val_losses, label='Val', linewidth=2)
    axes[0].set_title('Focal Loss')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(train_accs, label='Train', linewidth=2)
    axes[1].plot(val_accs, label='Val', linewidth=2)
    axes[1].set_title('Accuracy')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    axes[2].plot(train_f1s, label='Train', linewidth=2, color='#e74c3c')
    axes[2].plot(val_f1s, label='Val', linewidth=2, color='#3498db')
    axes[2].set_title('Macro F1 Score')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.suptitle('Deep Residual Classifier Training Metrics', fontsize=14)
    plt.tight_layout()
    plt.savefig('plots/classifier_metrics.png', dpi=150)
    plt.close()

    print("\nPlots saved to plots/")
    print("\n" + "=" * 60)
    print("Classifier training complete!")
    print(f"  Best Val F1: {best_val_f1:.4f}")
    print(f"  Temperature: {optimal_temp:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    train_classifier()
