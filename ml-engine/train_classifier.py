import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns

from models.classifier import HybridClassifier
from utils.preprocess import load_and_split, normalize_features, create_dataloaders

def train_classifier():
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

    # Normalize features
    X_train_norm, X_val_norm, X_test_norm, scaler = normalize_features(X_train, X_val, X_test)

    # Create dataloaders
    train_loader, val_loader, test_loader = create_dataloaders(
        X_train_norm, y_train, X_val_norm, y_val, X_test_norm, y_test,
        batch_size=64, shuffle=True
    )

    # Compute class weights
    classes, counts = np.unique(y_train, return_counts=True)
    total = len(y_train)
    class_weights = []
    for i in range(5):
        if i in classes:
            idx = np.where(classes == i)[0][0]
            weight = total / (5.0 * counts[idx])
        else:
            weight = 1.0
        class_weights.append(weight)
    
    class_weights_tensor = torch.tensor(class_weights, dtype=torch.float32).to(device)
    print(f"  Class weights: {[f'{w:.2f}' for w in class_weights]}")
    
    model = HybridClassifier(input_dim=X_train_norm.shape[1], num_classes=5).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
    scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)

    epochs = 100
    patience = 15
    best_val_loss = float('inf')
    epochs_no_improve = 0

    train_losses, val_losses = [], []
    train_accs, val_accs = [], []

    print(f"\nTraining CNN+BiLSTM Classifier ({X_train_norm.shape[1]} features, 5 classes)...")
    print("-" * 70)
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total_samples = 0
        
        for X_batch, y_batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}", leave=False):
            X_batch, y_batch = X_batch.to(device), y_batch.to(device).long()
            
            optimizer.zero_grad()
            logits = model(X_batch)
            loss = criterion(logits, y_batch)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * X_batch.size(0)
            preds = torch.argmax(logits, dim=1)
            correct += (preds == y_batch).sum().item()
            total_samples += y_batch.size(0)
            
        train_loss = running_loss / total_samples
        train_acc = correct / total_samples
        train_losses.append(train_loss)
        train_accs.append(train_acc)

        model.eval()
        val_loss = 0.0
        correct = 0
        total_samples = 0
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device).long()
                logits = model(X_batch)
                loss = criterion(logits, y_batch)
                
                val_loss += loss.item() * X_batch.size(0)
                preds = torch.argmax(logits, dim=1)
                correct += (preds == y_batch).sum().item()
                total_samples += y_batch.size(0)
                
        val_loss = val_loss / total_samples
        val_acc = correct / total_samples
        val_losses.append(val_loss)
        val_accs.append(val_acc)
        
        scheduler.step(val_loss)
        
        print(f"Epoch {epoch+1:3d}/{epochs} — Train Loss: {train_loss:.4f}, Acc: {train_acc:.4f} | Val Loss: {val_loss:.4f}, Acc: {val_acc:.4f}")

        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            torch.save(model.state_dict(), 'saved_models/classifier.pth')
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"\nEarly stopping at epoch {epoch+1}")
                break

    # Load best model
    model.load_state_dict(torch.load('saved_models/classifier.pth', weights_only=True))
    print("\nBest model loaded.")
    
    # Save label mapping
    label_mapping = {
        "0": "Normal",
        "1": "SQLi",
        "2": "XSS",
        "3": "PathTraversal",
        "4": "CommandInjection"
    }
    with open('saved_models/label_mapping.json', 'w') as f:
        json.dump(label_mapping, f)
    print("Label mapping saved to saved_models/label_mapping.json")

    # Evaluation on validation set
    model.eval()
    all_preds = []
    all_labels = []
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            X_batch = X_batch.to(device)
            logits = model(X_batch)
            preds = torch.argmax(logits, dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(y_batch.numpy())

    print("\n" + "=" * 60)
    print("Classification Report:")
    print("=" * 60)
    print(classification_report(
        all_labels, all_preds,
        target_names=[label_mapping[str(i)] for i in range(5)],
        zero_division=0
    ))

    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=[label_mapping[str(i)] for i in range(5)],
        yticklabels=[label_mapping[str(i)] for i in range(5)]
    )
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix — CNN+BiLSTM Classifier')
    plt.tight_layout()
    plt.savefig('plots/confusion_matrix.png', dpi=150)
    plt.close()
    print("Confusion matrix saved to plots/confusion_matrix.png")

    # Metrics plot
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train Loss', linewidth=2)
    plt.plot(val_losses, label='Val Loss', linewidth=2)
    plt.legend()
    plt.title('Loss Curve')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(1, 2, 2)
    plt.plot(train_accs, label='Train Acc', linewidth=2)
    plt.plot(val_accs, label='Val Acc', linewidth=2)
    plt.legend()
    plt.title('Accuracy Curve')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('plots/classifier_metrics.png', dpi=150)
    plt.close()
    print("Training metrics saved to plots/classifier_metrics.png")

    print("\n" + "=" * 60)
    print("Classifier training complete!")
    print("=" * 60)

if __name__ == "__main__":
    train_classifier()

