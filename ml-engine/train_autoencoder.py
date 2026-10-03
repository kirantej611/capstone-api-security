import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import joblib
from tqdm import tqdm
from models.autoencoder import DeepAutoencoder
from utils.preprocess import load_and_split, normalize_features, APIRequestDataset
from torch.utils.data import DataLoader


def train_autoencoder():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Ensure directories exist
    os.makedirs("saved_models", exist_ok=True)
    os.makedirs("plots", exist_ok=True)

    # Load data
    print("Loading dataset...")
    X_train, X_val, X_test, y_train, y_val, y_test = load_and_split(
        'data/synthetic_dataset.csv', test_size=0.15, val_size=0.15
    )
    print(f"  Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    # Filter to ONLY normal traffic (label=0) for training the autoencoder
    train_normal_mask = (y_train == 0)
    X_train_normal = X_train[train_normal_mask]
    y_train_normal = y_train[train_normal_mask]
    print(f"  Normal training samples: {len(X_train_normal)}")

    # Normalize features — fit scaler on normal training data only
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    X_train_norm = scaler.fit_transform(X_train_normal)
    X_val_norm = scaler.transform(X_val)
    X_test_norm = scaler.transform(X_test)

    # Create dataloaders manually (since autoencoder only trains on normal data)
    train_dataset = APIRequestDataset(X_train_norm, y_train_normal)
    val_dataset = APIRequestDataset(X_val_norm, y_val)

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)

    model = DeepAutoencoder(input_dim=X_train_norm.shape[1]).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)

    epochs = 100
    patience = 15
    best_val_loss = float('inf')
    epochs_no_improve = 0

    train_losses = []
    val_losses = []

    print(f"\nTraining Deep Autoencoder ({X_train_norm.shape[1]} features)...")
    print("-" * 60)
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for X_batch, _ in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}", leave=False):
            X_batch = X_batch.to(device)
            optimizer.zero_grad()
            reconstruction = model(X_batch)
            loss = criterion(reconstruction, X_batch)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * X_batch.size(0)

        train_loss = running_loss / len(train_loader.dataset)
        train_losses.append(train_loss)

        # Validate on normal samples only (to guide early stopping)
        model.eval()
        val_loss = 0.0
        val_normal_count = 0
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch = X_batch.to(device)
                mask = (y_batch == 0)
                if mask.sum() > 0:
                    reconstruction = model(X_batch[mask])
                    loss = criterion(reconstruction, X_batch[mask])
                    val_loss += loss.item() * mask.sum().item()
                    val_normal_count += mask.sum().item()

        val_loss = val_loss / max(val_normal_count, 1)
        val_losses.append(val_loss)

        print(f"Epoch {epoch+1:3d}/{epochs} — Train Loss: {train_loss:.6f} — Val Loss (Normal): {val_loss:.6f}")

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

    # Load best model
    model.load_state_dict(torch.load('saved_models/autoencoder.pth', weights_only=True))
    print("\nBest model loaded.")

    # Save scaler
    joblib.dump(scaler, 'saved_models/scaler.joblib')
    print("Scaler saved to saved_models/scaler.joblib")

    # Compute reconstruction error distribution for normal vs anomalous
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
    print(f"  Normal    — Mean: {normal_errors.mean():.6f}, Std: {normal_errors.std():.6f}")
    if len(anomalous_errors) > 0:
        print(f"  Anomalous — Mean: {anomalous_errors.mean():.6f}, Std: {anomalous_errors.std():.6f}")

    threshold = float(np.percentile(normal_errors, 95))
    print(f"\nAnomaly Threshold (95th percentile of normal): {threshold:.6f}")

    # Calculate detection rates
    if len(anomalous_errors) > 0:
        detected = (anomalous_errors > threshold).sum()
        print(f"Anomalous samples detected: {detected}/{len(anomalous_errors)} ({detected/len(anomalous_errors)*100:.1f}%)")

    with open('saved_models/anomaly_threshold.json', 'w') as f:
        json.dump({"threshold": threshold}, f)
    print("Threshold saved to saved_models/anomaly_threshold.json")

    # Plot training loss
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='Train Loss', linewidth=2)
    plt.plot(val_losses, label='Val Loss (Normal)', linewidth=2)
    plt.xlabel('Epoch')
    plt.ylabel('MSE Loss')
    plt.legend()
    plt.title('Autoencoder Training Curve')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('plots/autoencoder_loss.png', dpi=150)
    plt.close()
    print("Training curve saved to plots/autoencoder_loss.png")

    # Plot anomaly distribution
    plt.figure(figsize=(10, 5))
    plt.hist(normal_errors, bins=50, alpha=0.6, label='Normal', density=True, color='#2ecc71')
    if len(anomalous_errors) > 0:
        plt.hist(anomalous_errors, bins=50, alpha=0.6, label='Anomalous', density=True, color='#e74c3c')
    plt.axvline(threshold, color='r', linestyle='dashed', linewidth=2, label=f'Threshold ({threshold:.4f})')
    plt.xlabel('Reconstruction Error (MSE)')
    plt.ylabel('Density')
    plt.legend()
    plt.title('Reconstruction Error Distribution: Normal vs Anomalous')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('plots/anomaly_distribution.png', dpi=150)
    plt.close()
    print("Anomaly distribution saved to plots/anomaly_distribution.png")

    print("\n" + "=" * 60)
    print("Autoencoder training complete!")
    print("=" * 60)


if __name__ == "__main__":
    train_autoencoder()

