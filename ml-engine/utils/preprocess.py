import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

class APIRequestDataset(Dataset):
    """Custom PyTorch Dataset for API request features."""
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)
        
    def __len__(self):
        return len(self.y)
        
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

def load_and_split(csv_path: str, test_size: float = 0.2, val_size: float = 0.1):
    """
    Load CSV dataset and split into train, validation, and test sets.
    
    Args:
        csv_path (str): Path to the CSV dataset.
        test_size (float): Proportion of the dataset to include in the test split.
        val_size (float): Proportion of the dataset to include in the validation split.
        
    Returns:
        tuple: X_train, X_val, X_test, y_train, y_val, y_test
    """
    df = pd.read_csv(csv_path)
    
    # Assuming the target column is 'label' and 'raw_request' should be excluded
    X = df.drop(columns=['label', 'raw_request'], errors='ignore').values
    y = df['label'].values
    
    # First split: train+val vs test
    X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
    
    # Second split: train vs val
    val_ratio = val_size / (1.0 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=val_ratio, random_state=42, stratify=y_temp)
    
    return X_train, X_val, X_test, y_train, y_val, y_test

def normalize_features(X_train, X_val, X_test):
    """
    Normalize features using StandardScaler.
    
    Returns:
        tuple: X_train_scaled, X_val_scaled, X_test_scaled, scaler
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_val_scaled, X_test_scaled, scaler

def create_dataloaders(X_train, y_train, X_val, y_val, X_test, y_test, batch_size=64, shuffle=True):
    """
    Convert arrays to PyTorch DataLoaders.
    
    Returns:
        tuple: train_loader, val_loader, test_loader
    """
    train_dataset = APIRequestDataset(X_train, y_train)
    val_dataset = APIRequestDataset(X_val, y_val)
    test_dataset = APIRequestDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=shuffle)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, val_loader, test_loader
