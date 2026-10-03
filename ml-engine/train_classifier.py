import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
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
    try:
        X_train, X_val, X_test, y_train, y_val, y_test = load_and_split('data/synthetic_dataset.csv', test_size=0.15, val_size=0.15)
    except Exception as e:
        print(f"Error loading data (mocking data for testing): {e}")
        np.random.seed(42)
        X_train = np.random.randn(1000, 18)
        y_train = np.random.randint(0, 5, 1000)
        X_val = np.random.randn(200, 18)
        y_val = np.random.randint(0, 5, 200)

    # Normalize features
    X_train_norm, X_val_norm, _, scaler = normalize_features(X_train, X_val, X_val)

    # Create dataloaders
    train_loader = create_dataloaders(X_train_norm, y_train, batch_size=64, shuffle=True)
    val_loader = create_dataloaders(X_val_norm, y_val, batch_size=64, shuffle=False)

    # Compute class weights
    classes, counts = np.unique(y_train, return_counts=True)
    total = len(y_train)
    class_weights = []
    # Sort by class index
    for i in range(5):
        if i in classes:
            idx = np.where(classes == i)[0][0]
            # w = total / (num_classes * count)
            weight = total / (5.0 * counts[idx])
        else:
            weight = 1.0
        class_weights.append(weight)
    
    class_weights_tensor = torch.tensor(class_weights, dtype=torch.float32).to(device)
    
    model = HybridClassifier(input_dim=18, num_classes=5).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights_tensor)
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-5)
    scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5, verbose=True)

    epochs = 100
    patience = 15
    best_val_loss = float('inf')
    epochs_no_improve = 0

    train_losses, val_losses = [], []
    train_accs, val_accs = [], []

    print("Training CNN+BiLSTM Classifier...")
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total_samples = 0
        
        for X_batch, y_batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs} [Train]", leave=False):
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
        
        print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Acc: {train_acc:.4f} | Val Loss: {val_loss:.4f}, Acc: {val_acc:.4f}")

        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            torch.save(model.state_dict(), 'saved_models/classifier.pth')
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"Early stopping at epoch {epoch+1}")
                break

    # Load best model
    model.load_state_dict(torch.load('saved_models/classifier.pth'))
    
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

    # Evaluation
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

    print("\nClassification Report:")
    print(classification_report(all_labels, all_preds, target_names=[label_mapping[str(i)] for i in range(5)]))

    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    plt.figure(figsize=(8,6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=[label_mapping[str(i)] for i in range(5)], yticklabels=[label_mapping[str(i)] for i in range(5)])
    plt.xlabel('Predicted')
    plt.ylabel('Actual')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig('plots/confusion_matrix.png')
    plt.close()

    # Metrics plot
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(train_losses, label='Train Loss')
    plt.plot(val_losses, label='Val Loss')
    plt.legend()
    plt.title('Loss Curve')
    
    plt.subplot(1, 2, 2)
    plt.plot(train_accs, label='Train Acc')
    plt.plot(val_accs, label='Val Acc')
    plt.legend()
    plt.title('Accuracy Curve')
    plt.tight_layout()
    plt.savefig('plots/classifier_metrics.png')
    plt.close()

if __name__ == "__main__":
    train_classifier()
