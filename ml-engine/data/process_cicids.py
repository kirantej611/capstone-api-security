"""
CICIDS 2017 Dataset Processor
==============================

The CICIDS 2017 (Canadian Institute for Cybersecurity Intrusion Detection System)
dataset is one of the most widely cited network/web attack datasets in academic
research. It contains labeled network traffic including:

    - Benign traffic
    - Brute Force (FTP, SSH)
    - DoS / DDoS (Hulk, GoldenEye, Slowloris, Slowhttptest, Heartbleed)
    - Web Attacks (SQL Injection, XSS, Brute Force)
    - Infiltration
    - Botnet (ARES)
    - Port Scan

HOW TO GET THE DATA:
====================
1. Visit: https://www.unb.ca/cic/datasets/ids-2017.html
2. Download the "MachineLearningCSV.zip" file (~250MB)
3. Extract the ZIP into: ml-engine/data/cicids_raw/
   You should have files like:
     - Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
     - Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv
     - Friday-WorkingHours-Morning.pcap_ISCX.csv
     - Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv
     - Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv  <-- THIS ONE has SQLi/XSS
     - Tuesday-WorkingHours.pcap_ISCX.csv
     - Wednesday-workingHours.pcap_ISCX.csv
     - Monday-WorkingHours.pcap_ISCX.csv
4. Run this script: python data/process_cicids.py

This script will:
    - Load all CSV files from cicids_raw/
    - Clean column names (strip whitespace)
    - Handle missing/infinite values
    - Map the CICIDS labels to our project's label scheme
    - Select the most relevant features
    - Save the processed dataset to data/cicids_processed.csv

CITATION:
=========
Iman Sharafaldin, Arash Habibi Lashkari, and Ali A. Ghorbani,
"Intrusion Detection Evaluation Dataset (CIC-IDS2017)",
Canadian Institute for Cybersecurity, 2017.
"""

import os
import sys
import glob
import numpy as np
import pandas as pd
from tqdm import tqdm

# Label mapping: CICIDS labels -> Our project labels
# We focus on web attacks for our project, and group the rest
LABEL_MAP = {
    'BENIGN': 0,                    # Normal
    'Web Attack \x96 Sql Injection': 1,  # SQLi
    'Web Attack – Sql Injection': 1,     # SQLi (different dash encoding)
    'Web Attack Sql Injection': 1,       # SQLi
    'Web Attack \x96 XSS': 2,           # XSS
    'Web Attack – XSS': 2,              # XSS
    'Web Attack XSS': 2,                # XSS
    'Web Attack \x96 Brute Force': 1,   # Map web brute force to SQLi category
    'Web Attack – Brute Force': 1,       # (closest match for web attacks)
    'Web Attack Brute Force': 1,
}

# Features from CICIDS that are most relevant for our project
# These are network-level features but correlate with attack behavior
SELECTED_FEATURES = [
    ' Flow Duration',          # Duration of the network flow
    ' Total Fwd Packets',     # Forward packets count
    ' Total Backward Packets', # Backward packets count
    'Total Length of Fwd Packets',  # Total forward payload size
    ' Total Length of Bwd Packets', # Total backward payload size
    ' Fwd Packet Length Max',  # Max forward packet length
    ' Fwd Packet Length Mean', # Mean forward packet length
    ' Bwd Packet Length Max',  # Max backward packet length
    ' Bwd Packet Length Mean', # Mean backward packet length
    ' Flow Bytes/s',           # Flow bytes per second
    ' Flow Packets/s',        # Flow packets per second
    ' Flow IAT Mean',         # Inter-arrival time mean
    ' Flow IAT Std',          # Inter-arrival time std
    ' Fwd IAT Total',         # Forward inter-arrival time
    ' Bwd IAT Total',         # Backward inter-arrival time
    ' Fwd PSH Flags',         # Forward PSH flags
    ' Average Packet Size',   # Average packet size
    ' Avg Fwd Segment Size',  # Average forward segment
]

# Cleaned names for our processed output
CLEAN_FEATURE_NAMES = [
    'flow_duration',
    'total_fwd_packets',
    'total_bwd_packets',
    'total_fwd_payload_length',
    'total_bwd_payload_length',
    'fwd_packet_length_max',
    'fwd_packet_length_mean',
    'bwd_packet_length_max',
    'bwd_packet_length_mean',
    'flow_bytes_per_sec',
    'flow_packets_per_sec',
    'flow_iat_mean',
    'flow_iat_std',
    'fwd_iat_total',
    'bwd_iat_total',
    'fwd_psh_flags',
    'avg_packet_size',
    'avg_fwd_segment_size',
]


def load_cicids_csvs(raw_dir: str) -> pd.DataFrame:
    """Load and concatenate all CICIDS CSV files from the raw directory."""
    csv_files = glob.glob(os.path.join(raw_dir, '*.csv'))
    
    if not csv_files:
        print(f"ERROR: No CSV files found in {raw_dir}")
        print("Please download the CICIDS 2017 dataset first.")
        print("Visit: https://www.unb.ca/cic/datasets/ids-2017.html")
        print("Download 'MachineLearningCSV.zip' and extract to data/cicids_raw/")
        sys.exit(1)
    
    print(f"Found {len(csv_files)} CSV files:")
    for f in csv_files:
        print(f"  - {os.path.basename(f)}")
    
    dfs = []
    for csv_file in tqdm(csv_files, desc="Loading CSV files"):
        try:
            df = pd.read_csv(csv_file, encoding='utf-8', low_memory=False)
            dfs.append(df)
        except Exception as e:
            print(f"  Warning: Could not load {csv_file}: {e}")
    
    combined = pd.concat(dfs, ignore_index=True)
    print(f"\nTotal rows loaded: {len(combined):,}")
    return combined


def clean_and_process(df: pd.DataFrame) -> pd.DataFrame:
    """Clean column names, handle missing values, and map labels."""
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    
    # The label column in CICIDS is typically ' Label' (with leading space)
    label_col = None
    for col in df.columns:
        if 'label' in col.lower():
            label_col = col
            break
    
    if label_col is None:
        print("ERROR: Could not find a 'Label' column in the data.")
        sys.exit(1)
    
    print(f"\nOriginal label distribution:")
    print(df[label_col].value_counts())
    
    # Map labels to our scheme
    # Keep only labels we have mappings for
    df['label'] = df[label_col].map(LABEL_MAP)
    
    # For labels we don't map (DoS, DDoS, Bot, etc.), we can either:
    # - Drop them (if we only want web attacks)
    # - Map them to a generic "attack" category
    # For this project, we'll keep BENIGN + web attacks only
    df_filtered = df.dropna(subset=['label']).copy()
    df_filtered['label'] = df_filtered['label'].astype(int)
    
    print(f"\nFiltered to web-attack-relevant rows: {len(df_filtered):,}")
    print(f"Dropped {len(df) - len(df_filtered):,} rows (DoS, DDoS, Bot, etc.)")
    
    # Try to select features - handle column name variations
    available_features = []
    feature_name_map = {}
    
    for orig, clean in zip(SELECTED_FEATURES, CLEAN_FEATURE_NAMES):
        # Try exact match first, then stripped match
        if orig in df_filtered.columns:
            available_features.append(orig)
            feature_name_map[orig] = clean
        elif orig.strip() in df_filtered.columns:
            available_features.append(orig.strip())
            feature_name_map[orig.strip()] = clean
    
    if not available_features:
        print("WARNING: Could not find expected CICIDS feature columns.")
        print("Available columns:", list(df_filtered.columns[:20]))
        print("Using first 18 numeric columns instead...")
        numeric_cols = df_filtered.select_dtypes(include=[np.number]).columns[:18]
        result = df_filtered[list(numeric_cols) + ['label']].copy()
    else:
        result = df_filtered[available_features + ['label']].copy()
        result.rename(columns=feature_name_map, inplace=True)
    
    # Replace inf with NaN, then fill NaN with 0
    result.replace([np.inf, -np.inf], np.nan, inplace=True)
    result.fillna(0, inplace=True)
    
    # Ensure all feature columns are numeric
    for col in result.columns:
        if col != 'label':
            result[col] = pd.to_numeric(result[col], errors='coerce').fillna(0)
    
    return result


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(script_dir, 'cicids_raw')
    out_path = os.path.join(script_dir, 'cicids_processed.csv')
    
    print("=" * 60)
    print("CICIDS 2017 Dataset Processor")
    print("=" * 60)
    
    if not os.path.isdir(raw_dir):
        os.makedirs(raw_dir, exist_ok=True)
        print(f"\nCreated directory: {raw_dir}")
        print("\nPlease download the CICIDS 2017 dataset:")
        print("  1. Visit: https://www.unb.ca/cic/datasets/ids-2017.html")
        print("  2. Download 'MachineLearningCSV.zip'")
        print(f"  3. Extract CSV files into: {raw_dir}")
        print("  4. Re-run this script")
        sys.exit(0)
    
    # Load
    df = load_cicids_csvs(raw_dir)
    
    # Process
    result = clean_and_process(df)
    
    # Save
    result.to_csv(out_path, index=False)
    
    print(f"\n{'=' * 60}")
    print(f"Processed dataset saved to: {out_path}")
    print(f"Total samples: {len(result):,}")
    print(f"Features: {len(result.columns) - 1}")
    print(f"\nLabel distribution:")
    label_names = {0: 'Normal', 1: 'SQLi/WebBruteForce', 2: 'XSS'}
    for label, count in result['label'].value_counts().items():
        name = label_names.get(label, f'Unknown({label})')
        print(f"  {name}: {count:,} ({count/len(result)*100:.1f}%)")
    print("=" * 60)


if __name__ == '__main__':
    main()
