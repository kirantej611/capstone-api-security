"""
CSIC 2010 HTTP Dataset Downloader and Processor

The CSIC 2010 HTTP Dataset contains thousands of web requests to an e-commerce platform.
It is widely used in academic research for web application firewall (WAF) and intrusion
detection system (IDS) evaluation.

Source: https://www.tic.itefi.csic.es/dataset/

This script parses the raw text files, auto-classifies attack types based on payload
content, extracts all 42 features, and saves a processed CSV.

CITATION:
    C. Torrano-Gimenez, A. Perez-Villegas, and G. Alvarez,
    "A Self-Learning Anomaly-Based Web Application Firewall",
    International Joint Conference CISIS/ICEUTE/SOCO, 2009.
"""
import os
import re
import sys
import pandas as pd
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.feature_extraction import extract_features


def classify_attack_type(url: str, body: str, method: str) -> int:
    """
    Auto-classify the attack type from the raw CSIC request content.
    
    Returns:
        0 = Normal, 1 = SQLi, 2 = XSS, 3 = PathTraversal, 4 = CommandInjection, 5 = SSRF
    """
    full_text = f"{url} {body}".lower()
    
    # SQL Injection patterns
    sqli_patterns = [
        r"(\bor\b|\band\b)\s+\d+\s*=\s*\d+",  # OR 1=1, AND 1=1
        r"union\s+(all\s+)?select", r"select\s+.*\s+from",
        r"insert\s+into", r"delete\s+from", r"drop\s+table",
        r"'(\s*or\s*|\s*and\s*)", r"--\s*$", r";\s*--",
        r"exec(\s+|\()", r"xp_cmdshell", r"information_schema",
        r"1\s*=\s*1", r"'\s*=\s*'", r"benchmark\s*\(",
        r"sleep\s*\(", r"waitfor\s+delay",
    ]
    
    # XSS patterns
    xss_patterns = [
        r"<\s*script", r"javascript\s*:", r"on(error|load|click|mouseover)\s*=",
        r"alert\s*\(", r"document\.(cookie|write|location)",
        r"<\s*iframe", r"<\s*img[^>]+onerror",
        r"eval\s*\(", r"fromcharcode",
    ]
    
    # Path traversal patterns
    pt_patterns = [
        r"\.\./", r"\.\.\\", r"%2e%2e", r"%252e",
        r"/etc/(passwd|shadow|hosts)", r"\\windows\\",
        r"\\boot\.ini", r"web\.xml", r"/proc/self",
    ]
    
    # Command injection patterns
    ci_patterns = [
        r";\s*(ls|cat|id|whoami|uname|wget|curl|nc|bash|sh|python|perl|ruby)",
        r"\|\s*(ls|cat|id|whoami)", r"`[^`]+`",
        r"\$\([^)]+\)", r"%0a", r"%0d",
    ]
    
    # Count matches per category
    sqli_score = sum(1 for p in sqli_patterns if re.search(p, full_text))
    xss_score = sum(1 for p in xss_patterns if re.search(p, full_text))
    pt_score = sum(1 for p in pt_patterns if re.search(p, full_text))
    ci_score = sum(1 for p in ci_patterns if re.search(p, full_text))
    
    scores = {1: sqli_score, 2: xss_score, 3: pt_score, 4: ci_score}
    
    if max(scores.values()) == 0:
        return 1  # Default anomalous to SQLi (CSIC is mainly SQLi)
    
    return max(scores, key=scores.get)


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
        
        # Auto-classify attack type for anomalous traffic
        if label != 0:
            actual_label = classify_attack_type(url, body, method)
        else:
            actual_label = 0
        
        try:
            features = extract_features(url, method, body, headers)
            features['label'] = actual_label
            samples.append(features)
        except Exception:
            continue
        
    return samples


def main():
    raw_dir = os.path.join(os.path.dirname(__file__), 'csic_raw')
    
    files = [
        ('normalTrafficTraining.txt', 0),
        ('normalTrafficTest.txt', 0),
        ('anomalousTrafficTest.txt', 1)  # Will be auto-classified
    ]
    
    all_samples = []
    
    for filename, label in files:
        filepath = os.path.join(raw_dir, filename)
        samples = parse_csic_file(filepath, label)
        all_samples.extend(samples)
        print(f"  → {len(samples)} samples from {filename}")
        
    if not all_samples:
        print("No samples parsed. Please ensure the raw CSIC files are in data/csic_raw/")
        return
        
    df = pd.DataFrame(all_samples)
    
    # Drop any raw_request column if present
    if 'raw_request' in df.columns:
        df = df.drop(columns=['raw_request'])
    
    out_path = os.path.join(os.path.dirname(__file__), 'csic_processed.csv')
    df.to_csv(out_path, index=False)
    
    label_names = {0: 'Normal', 1: 'SQLi', 2: 'XSS', 3: 'PathTraversal', 4: 'CmdInjection', 5: 'SSRF'}
    print(f"\nSaved {len(all_samples)} processed samples to {out_path}")
    print("\nClass distribution:")
    for label, count in df['label'].value_counts().sort_index().items():
        name = label_names.get(label, f'Class_{label}')
        print(f"  {name}: {count:,} ({count/len(df)*100:.1f}%)")


if __name__ == "__main__":
    main()
