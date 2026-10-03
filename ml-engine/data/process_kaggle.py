"""
Kaggle Web Application Attack Payloads Processor
=================================================

This script processes the popular Kaggle "Web Application Attack Payload" datasets
to extract features compatible with our ML pipeline. We support two Kaggle datasets:

1. "Web Application Attack Payload Dataset" by syedjaferk (~240K payloads)
   URL: https://www.kaggle.com/datasets/syedjaferk/web-application-attack-payload-dataset
   Contains: clean_payloads.csv with columns like 'payload' and 'label'

2. "SQLi-XSS-Detection" by hiteshchauhan19 (mixed SQLi + XSS payloads)
   URL: https://www.kaggle.com/datasets/hiteshchauhan19/sqli-xss-detection
   Contains: SQLInjection_XSS_MixDataset.1.0.0.csv

HOW TO GET THE DATA:
====================
Option A (Recommended - Kaggle CLI):
    pip install kaggle
    kaggle datasets download -d syedjaferk/web-application-attack-payload-dataset
    unzip web-application-attack-payload-dataset.zip -d data/kaggle_raw/

Option B (Manual Download):
    1. Visit the Kaggle dataset page (URLs above)
    2. Click "Download" button
    3. Extract the ZIP contents into: ml-engine/data/kaggle_raw/

Then run this script:
    python data/process_kaggle.py

OUTPUT:
=======
    data/kaggle_processed.csv — Feature-extracted dataset ready for training.

CITATION:
=========
Syed Jafer K, "Web Application Attack Payload Dataset", Kaggle, 2023.
"""

import os
import sys
import glob
import numpy as np
import pandas as pd
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.feature_extraction import extract_features


# Common label mappings across different Kaggle dataset formats
LABEL_NORMALIZATION = {
    # syedjaferk dataset labels
    'norm': 0,
    'normal': 0,
    'benign': 0,
    'sqli': 1,
    'sql': 1,
    'sql injection': 1,
    'sql-injection': 1,
    'xss': 2,
    'cross-site scripting': 2,
    'path-traversal': 3,
    'path traversal': 3,
    'directory traversal': 3,
    'lfi': 3,
    'rfi': 3,
    'cmdi': 4,
    'command injection': 4,
    'command-injection': 4,
    'rce': 4,
    'os command': 4,
    'ssrf': 4,  # Group SSRF with command injection (both server-side)
}

LABEL_NAMES = {
    0: 'Normal',
    1: 'SQLi',
    2: 'XSS',
    3: 'PathTraversal',
    4: 'CommandInjection',
}


def find_payload_column(df: pd.DataFrame) -> str:
    """Find the column containing the attack payloads."""
    candidates = ['payload', 'Payload', 'request', 'Request', 'data',
                  'sentence', 'text', 'query', 'input', 'Sentence']
    for col in candidates:
        if col in df.columns:
            return col
    # Fallback: use the first string column
    for col in df.columns:
        if df[col].dtype == object:
            return col
    raise ValueError(f"Could not find payload column. Columns: {list(df.columns)}")


def find_label_column(df: pd.DataFrame) -> str:
    """Find the column containing labels."""
    candidates = ['label', 'Label', 'class', 'Class', 'type', 'Type',
                  'category', 'Category', 'attack_type', 'is_malicious']
    for col in candidates:
        if col in df.columns:
            return col
    raise ValueError(f"Could not find label column. Columns: {list(df.columns)}")


def normalize_label(label_value) -> int:
    """Map a raw label value to our standardized label scheme."""
    if isinstance(label_value, (int, float)):
        # If it's already numeric, check if it's a binary label (0/1)
        val = int(label_value)
        if val in [0, 1]:
            return val  # 0=normal, 1=attack (we'll handle binary separately)
        return val if val in LABEL_NAMES else -1

    # String label
    label_str = str(label_value).strip().lower()
    return LABEL_NORMALIZATION.get(label_str, -1)


def process_payloads(df: pd.DataFrame, payload_col: str, label_col: str) -> pd.DataFrame:
    """Extract features from raw payloads using our shared feature extraction module."""
    records = []

    for idx, row in tqdm(df.iterrows(), total=len(df), desc="Extracting features"):
        payload = str(row[payload_col]) if pd.notna(row[payload_col]) else ''
        raw_label = row[label_col]
        label = normalize_label(raw_label)

        if label == -1:
            continue  # Skip unknown labels

        # Simulate an HTTP request from the payload
        # Most payloads in these datasets are URL params or POST bodies
        if payload.startswith('/') or payload.startswith('http'):
            url = payload
            method = 'GET'
            body = ''
        elif '=' in payload and not payload.startswith('<'):
            url = f'/api/endpoint?q={payload}'
            method = 'GET'
            body = ''
        else:
            url = '/api/endpoint'
            method = 'POST'
            body = payload

        try:
            features = extract_features(
                url=url,
                method=method,
                body=body,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            features['label'] = label
            features['raw_payload'] = payload[:500]  # Truncate for storage
            records.append(features)
        except Exception as e:
            continue  # Skip problematic payloads

    return pd.DataFrame(records)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(script_dir, 'kaggle_raw')
    out_path = os.path.join(script_dir, 'kaggle_processed.csv')

    print("=" * 60)
    print("Kaggle Web Attack Payloads Processor")
    print("=" * 60)

    if not os.path.isdir(raw_dir):
        os.makedirs(raw_dir, exist_ok=True)
        print(f"\nCreated directory: {raw_dir}")
        print("\nPlease download one of these Kaggle datasets:")
        print()
        print("  Option 1 (Recommended):")
        print("    kaggle datasets download -d syedjaferk/web-application-attack-payload-dataset")
        print(f"    unzip *.zip -d {raw_dir}")
        print()
        print("  Option 2:")
        print("    kaggle datasets download -d hiteshchauhan19/sqli-xss-detection")
        print(f"    unzip *.zip -d {raw_dir}")
        print()
        print("  Then re-run: python data/process_kaggle.py")
        sys.exit(0)

    # Find CSV files in the raw directory
    csv_files = glob.glob(os.path.join(raw_dir, '**/*.csv'), recursive=True)
    if not csv_files:
        print(f"ERROR: No CSV files found in {raw_dir}")
        sys.exit(1)

    print(f"\nFound {len(csv_files)} CSV file(s):")
    for f in csv_files:
        print(f"  - {os.path.basename(f)}")

    # Load and concatenate all CSVs
    all_processed = []

    for csv_file in csv_files:
        print(f"\nProcessing: {os.path.basename(csv_file)}")
        try:
            df = pd.read_csv(csv_file, encoding='utf-8', low_memory=False,
                             on_bad_lines='skip')
        except Exception:
            try:
                df = pd.read_csv(csv_file, encoding='latin-1', low_memory=False,
                                 on_bad_lines='skip')
            except Exception as e:
                print(f"  Skipping (could not read): {e}")
                continue

        print(f"  Rows: {len(df):,}")
        print(f"  Columns: {list(df.columns)}")

        try:
            payload_col = find_payload_column(df)
            label_col = find_label_column(df)
        except ValueError as e:
            print(f"  Skipping: {e}")
            continue

        print(f"  Payload column: '{payload_col}'")
        print(f"  Label column: '{label_col}'")
        print(f"  Label distribution:\n{df[label_col].value_counts().head(10)}")

        # Sample if too large (>50K rows) to keep processing time reasonable
        if len(df) > 50000:
            print(f"  Sampling 50,000 rows from {len(df):,}...")
            df = df.sample(n=50000, random_state=42)

        processed = process_payloads(df, payload_col, label_col)
        all_processed.append(processed)

    if not all_processed:
        print("\nERROR: No data was successfully processed.")
        sys.exit(1)

    result = pd.concat(all_processed, ignore_index=True)

    # Save
    result.to_csv(out_path, index=False)

    print(f"\n{'=' * 60}")
    print(f"Processed dataset saved to: {out_path}")
    print(f"Total samples: {len(result):,}")
    print(f"Features: {len(result.columns) - 2}")  # -2 for label and raw_payload
    print(f"\nLabel distribution:")
    for label, count in result['label'].value_counts().sort_index().items():
        name = LABEL_NAMES.get(label, f'Unknown({label})')
        print(f"  {name}: {count:,} ({count/len(result)*100:.1f}%)")
    print("=" * 60)


if __name__ == '__main__':
    main()
