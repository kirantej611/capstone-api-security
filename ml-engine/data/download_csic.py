"""
CSIC 2010 HTTP Dataset Downloader and Processor

The CSIC 2010 HTTP Dataset contains thousands of web requests to an e-commerce platform.
It is widely used in academic research for web application firewall (WAF) and intrusion detection system (IDS) evaluation.

Since the dataset might not be directly downloadable via a simple static URL, 
please download it manually from:
https://www.tic.itefi.csic.es/dataset/

Extract and place the following files in the `data/csic_raw/` directory:
- normalTrafficTraining.txt
- normalTrafficTest.txt
- anomalousTrafficTest.txt

This script will parse those raw text files, extract features, and save a combined processed CSV.
"""
import os
import sys
import pandas as pd
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.feature_extraction import extract_features

def parse_csic_file(filepath, label):
    """
    Parse a CSIC 2010 raw text file.
    Requests are separated by blank lines.
    """
    samples = []
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return samples
        
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    # Split by empty lines
    raw_requests = content.split('\n\n')
    
    for raw in tqdm(raw_requests, desc=f"Parsing {os.path.basename(filepath)}"):
        lines = raw.strip().split('\n')
        if len(lines) < 2:
            continue
            
        request_line = lines[0].strip().split(' ')
        if len(request_line) < 2:
            continue
            
        method = request_line[0]
        url = request_line[1]
        
        headers = {}
        body = ""
        is_body = False
        
        for line in lines[1:]:
            line = line.strip()
            if not line:
                is_body = True
                continue
                
            if is_body:
                body += line
            else:
                if ':' in line:
                    k, v = line.split(':', 1)
                    headers[k.strip()] = v.strip()
                    
        features = extract_features(url, method, body, headers)
        features['label'] = label
        features['raw_request'] = raw.replace('\n', ' | ')
        samples.append(features)
        
    return samples

def main():
    raw_dir = os.path.join(os.path.dirname(__file__), 'csic_raw')
    
    files = [
        ('normalTrafficTraining.txt', 0),
        ('normalTrafficTest.txt', 0),
        ('anomalousTrafficTest.txt', 1)
    ]
    
    all_samples = []
    
    for filename, label in files:
        filepath = os.path.join(raw_dir, filename)
        samples = parse_csic_file(filepath, label)
        all_samples.extend(samples)
        
    if not all_samples:
        print("No samples parsed. Please ensure the raw CSIC files are in data/csic_raw/")
        return
        
    df = pd.DataFrame(all_samples)
    out_path = os.path.join(os.path.dirname(__file__), 'csic_processed.csv')
    df.to_csv(out_path, index=False)
    
    print(f"\nSaved {len(all_samples)} processed samples to {out_path}")
    print("\nClass distribution:")
    print(df['label'].value_counts())

if __name__ == "__main__":
    main()
