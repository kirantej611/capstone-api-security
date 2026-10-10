import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, RobustScaler
import numpy as np

from utils.feature_extraction import FEATURE_NAMES, NUM_FEATURES


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

    # Use only the canonical feature columns (in order)
    available_features = [f for f in FEATURE_NAMES if f in df.columns]
    if len(available_features) < NUM_FEATURES:
        missing = set(FEATURE_NAMES) - set(available_features)
        print(f"  WARNING: Missing {len(missing)} features: {missing}")
        print(f"  Using {len(available_features)} available features.")

    X = df[available_features].values
    y = df['label'].values

    # First split: train+val vs test
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    # Second split: train vs val
    val_ratio = val_size / (1.0 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_ratio, random_state=42, stratify=y_temp
    )

    return X_train, X_val, X_test, y_train, y_val, y_test


def fit_scaler_on_normal(X_train: np.ndarray, y_train: np.ndarray, robust: bool = True):
    """
    Fit a scaler on normal-class (label=0) training data only.
    
    This ensures consistency between autoencoder and classifier training:
    both models see identically-scaled features, and the scaler used at
    inference matches what both models were trained with.

    Args:
        X_train: Training feature matrix.
        y_train: Training labels.
        robust: If True, use RobustScaler (default). Otherwise StandardScaler.

    Returns:
        scaler: Fitted scaler.
    """
    scaler = RobustScaler() if robust else StandardScaler()
    normal_mask = (y_train == 0)
    if normal_mask.sum() > 0:
        scaler.fit(X_train[normal_mask])
    else:
        # Fallback: fit on all data if no normal samples (shouldn't happen)
        scaler.fit(X_train)
    return scaler


def normalize_features(X_train, X_val, X_test, robust: bool = True):
    """
    Normalize features using RobustScaler (default) or StandardScaler.
    RobustScaler is more resilient to outliers in attack traffic.

    Returns:
        tuple: X_train_scaled, X_val_scaled, X_test_scaled, scaler
    """
    scaler = RobustScaler() if robust else StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    return X_train_scaled, X_val_scaled, X_test_scaled, scaler


def create_dataloaders(X_train, y_train, X_val, y_val, X_test, y_test,
                       batch_size=128, shuffle=True, num_workers=0,
                       use_weighted_sampling=False):
    """
    Convert arrays to PyTorch DataLoaders.

    When use_weighted_sampling=True, uses WeightedRandomSampler to
    oversample minority classes, producing approximately balanced batches.

    Returns:
        tuple: train_loader, val_loader, test_loader
    """
    train_dataset = APIRequestDataset(X_train, y_train)
    val_dataset = APIRequestDataset(X_val, y_val)
    test_dataset = APIRequestDataset(X_test, y_test)

    if use_weighted_sampling:
        # Compute per-sample weights: inverse class frequency
        classes, counts = np.unique(y_train, return_counts=True)
        class_weights = {int(c): len(y_train) / cnt for c, cnt in zip(classes, counts)}
        sample_weights = np.array([class_weights[int(y)] for y in y_train])
        sample_weights = torch.tensor(sample_weights, dtype=torch.float64)
        sampler = WeightedRandomSampler(
            sample_weights, num_samples=len(sample_weights), replacement=True
        )
        train_loader = DataLoader(
            train_dataset, batch_size=batch_size, sampler=sampler,
            num_workers=num_workers, pin_memory=True
        )
    else:
        train_loader = DataLoader(
            train_dataset, batch_size=batch_size, shuffle=shuffle,
            num_workers=num_workers, pin_memory=True
        )

    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=True
    )
    test_loader = DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=True
    )

    return train_loader, val_loader, test_loader


def compute_class_weights(y: np.ndarray, num_classes: int) -> np.ndarray:
    """
    Compute class weights using effective number of samples.
    
    Based on "Class-Balanced Loss Based on Effective Number of Samples"
    (Cui et al., CVPR 2019).  Produces smoother weights than raw inverse
    frequency, which avoids over-weighting extremely rare classes.
    """
    classes, counts = np.unique(y, return_counts=True)
    total = len(y)

    beta = 0.999  # Effective number hyperparameter
    weights = np.ones(num_classes)
    for cls, cnt in zip(classes, counts):
        effective_num = (1.0 - beta ** cnt) / (1.0 - beta)
        weights[int(cls)] = total / (num_classes * effective_num)

    # Normalise so weights sum to num_classes (preserves loss magnitude)
    weights = weights / weights.sum() * num_classes
    return weights


def compute_normal_statistics(X_train: np.ndarray, y_train: np.ndarray) -> np.ndarray:
    """
    Compute the mean feature vector for normal traffic (label=0).
    Used for XAI feature importance computation.
    """
    normal_mask = (y_train == 0)
    if normal_mask.sum() > 0:
        return X_train[normal_mask].mean(axis=0)
    return np.zeros(X_train.shape[1])
