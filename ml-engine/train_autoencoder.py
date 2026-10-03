import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import joblib
from tqdm import tqdm
from models.autoencoder import DeepAutoencoder
from utils.preprocess import load_and_split, normalize_features, create_dataloaders

def train_autoencoder():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Ensure directories exist
    os.makedirs("saved_models", exist_ok=True)
    os.makedirs("plots", exist_ok=True)

    # Load data
    try:
        X_train, X_val, X_test, y_train, y_val, y_test = load_and_split('data/synthetic_dataset.csv', test_size=0.15, val_size=0.15)
    except Exception as e:
        print(f"Error loading data (mocking data for testing): {e}")
        # Mock data for demonstration if file doesn't exist
        np.random.seed(42)
        X_train = np.random.randn(1000, 18)
        y_train = np.zeros(1000)
        X_val = np.random.randn(200, 18)
        y_val = np.zeros(200)
        y_val[150:] = 1 # some anomalous

    # Filter to ONLY normal traffic (label=0) for training
    train_mask = (y_train == 0)
    X_train_normal = X_train[train_mask]
    y_train_normal = y_train[train_mask]

    # Normalize features
    X_train_norm, X_val_norm, _, scaler = normalize_features(X_train_normal, X_val, X_val)

    # Create dataloaders
    train_loader = create_dataloaders(X_train_norm, y_train_normal, batch_size=64, shuffle=True)
    val_loader = create_dataloaders(X_val_norm, y_val, batch_size=64, shuffle=False)

    model = DeepAutoencoder(input_dim=18).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)

    epochs = 100
    patience = 15
    best_val_loss = float('inf')
    epochs_no_improve = 0

    train_losses = []
    val_losses = []

    print("Training Deep Autoencoder...")
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for X_batch, _ in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [Train]", leave=False):
            X_batch = X_batch.to(device)
            optimizer.zero_grad()
            reconstruction = model(X_batch)
            loss = criterion(reconstruction, X_batch)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * X_batch.size(0)
        
        train_loss = running_loss / len(train_loader.dataset)
        train_losses.append(train_loss)

        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch = X_batch.to(device)
                # Only use normal validation samples for loss to guide early stopping, or use all.
                # Usually we can just evaluate reconstruction on normal
                mask = (y_batch == 0)
                if mask.sum() > 0:
                    reconstruction = model(X_batch[mask])
                    loss = criterion(reconstruction, X_batch[mask])
                    val_loss += loss.item() * mask.sum().item()
        
        val_loss = val_loss / max((y_val == 0).sum(), 1)
        val_losses.append(val_loss)

        print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.6f} - Val Loss (Normal): {val_loss:.6f}")

        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            torch.save(model.state_dict(), 'saved_models/autoencoder.pth')
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"Early stopping at epoch {epoch+1}")
                break

    # Load best model
    model.load_state_dict(torch.load('saved_models/autoencoder.pth'))
    
    # Save scaler
    joblib.dump(scaler, 'saved_models/scaler.joblib')

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

    if len(normal_errors) > 0:
        threshold = float(np.percentile(normal_errors, 95))
        print(f"Suggested Anomaly Threshold (95th percentile of normal): {threshold:.6f}")
        with open('saved_models/anomaly_threshold.json', 'w') as f:
            json.dump({"threshold": threshold}, f)

    # Plot training loss
    plt.figure()
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Val Loss (Normal)')
    plt.xlabel('Epoch')
    plt.ylabel('MSE Loss')
    plt.legend()
    plt.title('Autoencoder Training Curve')
    plt.savefig('plots/autoencoder_loss.png')
    plt.close()

    # Plot anomaly distribution
    plt.figure()
    plt.hist(normal_errors, bins=50, alpha=0.6, label='Normal', density=True)
    if len(anomalous_errors) > 0:
        plt.hist(anomalous_errors, bins=50, alpha=0.6, label='Anomalous', density=True)
    if len(normal_errors) > 0:
        plt.axvline(threshold, color='r', linestyle='dashed', linewidth=2, label='Threshold (95%)')
    plt.xlabel('Reconstruction Error (MSE)')
    plt.ylabel('Density')
    plt.legend()
    plt.title('Reconstruction Error Distribution')
    plt.savefig('plots/anomaly_distribution.png')
    plt.close()

if __name__ == "__main__":
    train_autoencoder()
