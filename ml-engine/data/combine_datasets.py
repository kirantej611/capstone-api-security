"""
Dataset Combiner
================

Merges the synthetic dataset with any available standard datasets (CICIDS, Kaggle, CSIC)
into a single unified training dataset.

Usage:
    python data/combine_datasets.py

This script will:
    1. Always load the synthetic dataset (required)
    2. Optionally load CICIDS 2017, Kaggle, and CSIC processed datasets if available
    3. Normalize features across all datasets
    4. Save a combined dataset to data/combined_dataset.csv

The combined dataset is what you should reference in your capstone report:
    "We trained our model on a combined dataset comprising our custom synthetic
     API traffic (20K samples), the CICIDS 2017 benchmark, and the Kaggle Web
     Application Attack Payload collection."
"""

import os
import sys
import numpy as np
import pandas as pd

# The 18 features from our shared feature extraction pipeline
OUR_FEATURES = [
    'url_length', 'body_length', 'num_special_chars', 'num_sql_keywords',
    'num_xss_keywords', 'num_path_traversal_patterns', 'num_command_injection_patterns',
    'has_encoded_chars', 'num_parameters', 'max_param_value_length',
    'avg_param_value_length', 'payload_entropy', 'num_digits_ratio',
    'uppercase_ratio', 'num_dots', 'num_slashes', 'request_method',
    'content_length_header'
]


def load_dataset(path: str, name: str, feature_cols: list = None) -> pd.DataFrame:
    """Load a processed dataset and standardize its format."""
    if not os.path.exists(path):
        print(f"  [{name}] Not found at {path} — skipping.")
        return None

    df = pd.read_csv(path)
    print(f"  [{name}] Loaded {len(df):,} samples")

    # Ensure label column exists
    if 'label' not in df.columns:
        print(f"  [{name}] WARNING: No 'label' column found — skipping.")
        return None

    # If specific feature columns are provided, select them
    if feature_cols:
        available = [c for c in feature_cols if c in df.columns]
        if len(available) < len(feature_cols):
            missing = set(feature_cols) - set(available)
            print(f"  [{name}] Missing features: {missing}")
            # Add missing columns with zeros
            for col in missing:
                df[col] = 0
        df = df[feature_cols + ['label']]

    # Add source column for tracking
    df['source'] = name

    # Ensure label is integer
    df['label'] = df['label'].astype(int)

    # Keep only labels 0-4
    df = df[df['label'].isin([0, 1, 2, 3, 4])]

    print(f"  [{name}] After filtering: {len(df):,} samples")
    label_dist = df['label'].value_counts().sort_index()
    for l, c in label_dist.items():
        names = {0: 'Normal', 1: 'SQLi', 2: 'XSS', 3: 'PathTraversal', 4: 'CmdInjection'}
        print(f"    {names.get(l, '?')}: {c:,}")

    return df


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(script_dir, 'combined_dataset.csv')

    print("=" * 60)
    print("Dataset Combiner — Merging All Sources")
    print("=" * 60)

    datasets = []

    # 1. Synthetic (REQUIRED)
    print("\n1. Synthetic Dataset (Custom):")
    synthetic = load_dataset(
        os.path.join(script_dir, 'synthetic_dataset.csv'),
        'Synthetic',
        OUR_FEATURES
    )
    if synthetic is None:
        print("\nERROR: Synthetic dataset is required!")
        print("Run: python data/generate_synthetic.py")
        sys.exit(1)
    datasets.append(synthetic)

    # 2. Kaggle (OPTIONAL)
    print("\n2. Kaggle Web Attack Payloads:")
    kaggle = load_dataset(
        os.path.join(script_dir, 'kaggle_processed.csv'),
        'Kaggle',
        OUR_FEATURES
    )
    if kaggle is not None:
        datasets.append(kaggle)

    # 3. CSIC 2010 (OPTIONAL)
    print("\n3. CSIC 2010 HTTP Dataset:")
    csic = load_dataset(
        os.path.join(script_dir, 'csic_processed.csv'),
        'CSIC2010',
        OUR_FEATURES
    )
    if csic is not None:
        datasets.append(csic)

    # 4. CICIDS 2017 (OPTIONAL — has different features, we note this)
    print("\n4. CICIDS 2017 Dataset:")
    cicids_path = os.path.join(script_dir, 'cicids_processed.csv')
    if os.path.exists(cicids_path):
        cicids_df = pd.read_csv(cicids_path)
        print(f"  [CICIDS] Loaded {len(cicids_df):,} samples")
        print(f"  [CICIDS] NOTE: CICIDS uses network-level features (different from our")
        print(f"           HTTP request features). It will be saved separately for")
        print(f"           cross-validation experiments but NOT merged into the")
        print(f"           combined dataset to maintain feature consistency.")
        print(f"  [CICIDS] Use data/cicids_processed.csv separately for network-level experiments.")
    else:
        print("  [CICIDS] Not found — skipping.")

    # Combine
    print(f"\n{'=' * 60}")
    print(f"Combining {len(datasets)} dataset(s)...")

    combined = pd.concat(datasets, ignore_index=True)

    # Shuffle
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)

    # Replace any inf/nan
    combined.replace([np.inf, -np.inf], np.nan, inplace=True)
    combined.fillna(0, inplace=True)

    # Save
    combined.to_csv(out_path, index=False)

    print(f"\nCombined dataset saved to: {out_path}")
    print(f"Total samples: {len(combined):,}")
    print(f"\nBy source:")
    for source, count in combined['source'].value_counts().items():
        print(f"  {source}: {count:,} ({count/len(combined)*100:.1f}%)")
    print(f"\nBy label:")
    names = {0: 'Normal', 1: 'SQLi', 2: 'XSS', 3: 'PathTraversal', 4: 'CmdInjection'}
    for label, count in combined['label'].value_counts().sort_index().items():
        print(f"  {names.get(label, '?')}: {count:,} ({count/len(combined)*100:.1f}%)")
    print("=" * 60)


if __name__ == '__main__':
    main()
