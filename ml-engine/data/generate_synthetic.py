import os
import random
import sys
import numpy as np
import pandas as pd
from tqdm import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.feature_extraction import extract_features

random.seed(42)
np.random.seed(42)

def generate_normal_sample():
    endpoints = ['/api/products', '/api/cart/add', '/api/user/profile', '/api/checkout', '/api/search']
    url = random.choice(endpoints)
    if 'products' in url or 'search' in url:
        url += f"?category={random.choice(['electronics', 'books', 'clothing'])}&page={random.randint(1, 10)}"
        method = 'GET'
        body = ''
    elif 'cart' in url or 'checkout' in url:
        method = 'POST'
        body = f'{{"item_id": {random.randint(100, 999)}, "qty": {random.randint(1, 5)}}}'
    else:
        method = 'GET'
        body = ''
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/json' if method == 'POST' else ''
    }
    return url, method, body, headers, 0

def generate_sqli_sample():
    payloads = [
        "' UNION SELECT username, password FROM users --",
        "' OR 1=1 --",
        "'; WAITFOR DELAY '0:0:5' --",
        "admin' --",
        "1 OR '1'='1"
    ]
    url = f"/api/login?username={random.choice(payloads)}"
    return url, 'GET', '', {'User-Agent': 'SQLMap/1.5'}, 1

def generate_xss_sample():
    payloads = [
        "<script>alert('xss')</script>",
        "<img onerror=alert(1)>",
        "javascript:alert(1)",
        "%3Cscript%3Ealert(1)%3C%2Fscript%3E"
    ]
    url = "/api/search"
    body = f"q={random.choice(payloads)}"
    return url, 'POST', body, {'Content-Type': 'application/x-www-form-urlencoded'}, 2

def generate_path_traversal_sample():
    payloads = [
        "../../etc/passwd",
        "..\\..\\windows\\system32",
        "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "....//....//etc/passwd\x00"
    ]
    url = f"/api/download?file={random.choice(payloads)}"
    return url, 'GET', '', {}, 3

def generate_command_injection_sample():
    payloads = [
        "; ls -la",
        "| cat /etc/passwd",
        "`whoami`",
        "$(whoami)",
        "&& rm -rf /"
    ]
    url = "/api/ping"
    body = f'{{"host": "127.0.0.1 {random.choice(payloads)}" }}'
    return url, 'POST', body, {'Content-Type': 'application/json'}, 4

def main():
    print("Generating synthetic dataset...")
    samples = []
    num_samples = 20000
    
    generators = [
        (generate_normal_sample, 0.5), # 50% normal
        (generate_sqli_sample, 0.15),
        (generate_xss_sample, 0.15),
        (generate_path_traversal_sample, 0.1),
        (generate_command_injection_sample, 0.1)
    ]
    
    for _ in tqdm(range(num_samples)):
        r = random.random()
        cumulative = 0.0
        for gen, prob in generators:
            cumulative += prob
            if r < cumulative:
                url, method, body, headers, label = gen()
                break
        
        features = extract_features(url, method, body, headers)
        features['label'] = label
        features['raw_request'] = f"{method} {url} {body} {headers}"
        samples.append(features)
        
    df = pd.DataFrame(samples)
    
    os.makedirs(os.path.join(os.path.dirname(__file__)), exist_ok=True)
    out_path = os.path.join(os.path.dirname(__file__), 'synthetic_dataset.csv')
    df.to_csv(out_path, index=False)
    
    print(f"\nSaved to {out_path}")
    print("\nClass distribution:")
    print(df['label'].value_counts(normalize=True))

if __name__ == "__main__":
    main()
