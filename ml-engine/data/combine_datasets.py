"""
Dataset Combiner — Research-Grade Combined Dataset
====================================================

Merges all available real-world benchmark datasets into a single
unified training dataset using the full 42-feature extraction pipeline.

Sources supported:
    1. CSIC 2010 HTTP Dataset (auto-classified attack types)
    2. Kaggle Web Application Attack Payloads
    3. CICIDS 2017 (separate — network-level features, not merged)

The synthetic datasets are intentionally EXCLUDED from the combined
dataset.  The combined dataset uses only real/semi-real payloads from
published benchmarks, which is essential for credible research results.

Usage:
    python data/combine_datasets.py

Output:
    data/combined_dataset.csv  — ready for train_classifier.py / train_autoencoder.py

CITATION (in your paper):
    "We trained our models on a combined dataset comprising the CSIC 2010
     HTTP Dataset [1] and the Kaggle Web Application Attack Payload
     collection [2], processed through a unified 42-feature extraction
     pipeline.  The combined dataset contains N samples across 6 classes."
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.feature_extraction import FEATURE_NAMES, NUM_FEATURES

LABEL_NAMES = {
    0: 'Normal',
    1: 'SQLi',
    2: 'XSS',
    3: 'PathTraversal',
    4: 'CommandInjection',
    5: 'SSRF',
}


def load_dataset(path: str, name: str) -> pd.DataFrame:
    """Load a processed dataset and validate its format."""
    if not os.path.exists(path):
        print(f"  [{name}] Not found at {path} — skipping.")
        return None

    df = pd.read_csv(path)
    print(f"  [{name}] Loaded {len(df):,} samples")

    if 'label' not in df.columns:
        print(f"  [{name}] WARNING: No 'label' column found — skipping.")
        return None

    # Keep only known feature columns + label
    available = [f for f in FEATURE_NAMES if f in df.columns]
    missing = set(FEATURE_NAMES) - set(available)
    if missing:
        print(f"  [{name}] Adding {len(missing)} missing features as zeros")
        for col in missing:
            df[col] = 0

    df = df[FEATURE_NAMES + ['label']].copy()
    df['label'] = df['label'].astype(int)

    # Keep only valid labels (0-5)
    df = df[df['label'].isin(range(6))]

    # Add source tracking
    df['source'] = name

    print(f"  [{name}] After filtering: {len(df):,} samples")
    for lbl, cnt in df['label'].value_counts().sort_index().items():
        name_str = LABEL_NAMES.get(lbl, f'Class_{lbl}')
        print(f"    {name_str}: {cnt:,}")

    return df


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(script_dir, 'combined_dataset.csv')

    print("=" * 60)
    print("Dataset Combiner — Real-World Benchmarks Only")
    print("=" * 60)

    datasets = []

    # 1. CSIC 2010
    print("\n1. CSIC 2010 HTTP Dataset:")
    csic = load_dataset(
        os.path.join(script_dir, 'csic_processed.csv'), 'CSIC2010'
    )
    if csic is not None:
        datasets.append(csic)

    # 2. Kaggle Web Attack Payloads
    print("\n2. Kaggle Web Attack Payloads:")
    kaggle = load_dataset(
        os.path.join(script_dir, 'kaggle_processed.csv'), 'Kaggle'
    )
    if kaggle is not None:
        datasets.append(kaggle)

    # 3. Note about CICIDS
    print("\n3. CICIDS 2017:")
    cicids_path = os.path.join(script_dir, 'cicids_processed.csv')
    if os.path.exists(cicids_path):
        print("  [CICIDS] Available but NOT merged (network-level features)")
        print("  [CICIDS] Use separately for cross-validation experiments.")
    else:
        print("  [CICIDS] Not found — skipping.")

    if not datasets:
        print("\nERROR: No datasets available to combine!")
        print("Please run:")
        print("  python data/download_csic.py")
        print("  python data/process_kaggle.py")
        sys.exit(1)

    # Combine
    print(f"\n{'=' * 60}")
    print(f"Combining {len(datasets)} dataset(s)...")

    combined = pd.concat(datasets, ignore_index=True)

    # Shuffle
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)

    # Clean: replace inf/nan
    feature_cols = [c for c in combined.columns if c not in ('label', 'source')]
    combined[feature_cols] = combined[feature_cols].replace(
        [np.inf, -np.inf], np.nan
    ).fillna(0)

    # Save
    combined.to_csv(out_path, index=False)

    print(f"\nCombined dataset saved to: {out_path}")
    print(f"Total samples: {len(combined):,}")
    print(f"Features: {NUM_FEATURES}")
    print(f"\nBy source:")
    for source, count in combined['source'].value_counts().items():
        print(f"  {source}: {count:,} ({count/len(combined)*100:.1f}%)")
    print(f"\nBy label:")
    for label in sorted(combined['label'].unique()):
        count = (combined['label'] == label).sum()
        name = LABEL_NAMES.get(label, f'Class_{label}')
        print(f"  {label} ({name}): {count:,} ({count/len(combined)*100:.1f}%)")
    print("=" * 60)


if __name__ == '__main__':
    main()
