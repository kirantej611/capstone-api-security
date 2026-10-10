import random
import numpy as np
import pandas as pd
import sys
import os

# Add parent directory to sys.path to import utils
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.feature_extraction import extract_features

random.seed(42)
np.random.seed(42)

def generate_normal(is_ambiguous=False):
    methods = ['GET', 'POST']
    method = random.choice(methods)
    
    headers = {
        'User-Agent': random.choice(['Mozilla/5.0', 'curl/7.68.0', 'PostmanRuntime/7.26.8', 'Python-urllib/3.8', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36']),
        'Accept': '*/*'
    }
    
    url = ''
    body = ''
    
    if not is_ambiguous:
        # Normal traffic with noise
        paths = ['/api/products', '/api/users', '/api/search', '/api/checkout', '/api/v2.0/products/image.jpg']
        path = random.choice(paths)
        
        noise_types = ['special_chars', 'encoded_chars', 'long_query', 'html_like', 'none', 'none']
        noise = random.choice(noise_types)
        
        if method == 'GET':
            if noise == 'special_chars':
                url = f"{path}?q=O'Brien's+Widgets"
            elif noise == 'encoded_chars':
                url = f"{path}?q=shoes%26bags"
            elif noise == 'long_query':
                url = f"{path}?category=electronics&brand=samsung&model=galaxy+s24&color=black&size=128gb"
            else:
                url = f"{path}?id={random.randint(1, 1000)}"
        else:
            url = path
            if noise == 'html_like':
                body = '{"review": "<b>great product!</b>"}'
            else:
                body = '{"id": ' + str(random.randint(1, 1000)) + '}'
    else:
        # Borderline/Ambiguous Cases
        ambiguous_cases = [
            ('/api/debug?query=SELECT+count+FROM+products', ''),
            ('/api/search?q=how+to+prevent+SQL+injection', ''),
            ('/api/products?name=Script+Runner+Pro', ''),
            ('/api/files?path=docs/reports/2024/q1.pdf', ''),
            ('/api/reviews', '{"text": "Great tutorial on using <code>alert()</code> in JS"}')
        ]
        url, body = random.choice(ambiguous_cases)
        if body:
            method = 'POST'
        else:
            method = 'GET'

    return url, method, body, headers, 0, False

def generate_sqli(is_subtle=False):
    method = random.choice(['GET', 'POST'])
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}
    
    obvious = [
        "' OR 1=1 --",
        "' UNION SELECT * FROM users --",
        '" OR "1"="1'
    ]
    
    subtle = [
        "' oR 1=1 --",
        "' UnIoN SeLeCt",
        "'/**/OR/**/1=1--",
        "%2527%2520OR%25201%253D1",
        "'OR'1'='1",
        "admin'||'"
    ]
    
    payload = random.choice(subtle) if is_subtle else random.choice(obvious)
    
    if method == 'GET':
        url = f"/api/users?id={payload}"
        body = ""
    else:
        url = "/api/login"
        body = f'{{"username": "{payload}", "password": "password123"}}'
        
    return url, method, body, headers, 1, is_subtle

def generate_xss(is_subtle=False):
    method = random.choice(['GET', 'POST'])
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}
    
    obvious = [
        "<script>alert(1)</script>",
        "<img onerror=alert(1)>"
    ]
    
    subtle = [
        "<ScRiPt>alert(1)</sCrIpT>",
        "<div onmouseover=\"alert(1)\">",
        "<svg/onload=alert(1)>",
        "%3Cscript%3Ealert(1)%3C/script%3E",
        "{{constructor.constructor('alert(1)')()"
    ]
    
    payload = random.choice(subtle) if is_subtle else random.choice(obvious)
    
    if method == 'GET':
        url = f"/api/search?q={payload}"
        body = ""
    else:
        url = "/api/comments"
        body = f'{{"comment": "{payload}"}}'
        
    return url, method, body, headers, 2, is_subtle

def generate_path_traversal(is_subtle=False):
    method = 'GET'
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}
    
    obvious = [
        "../../etc/passwd",
        "../../../windows/win.ini"
    ]
    
    subtle = [
        "....//....//etc/passwd",
        "..%252f..%252f",
        "..%c0%af..%c0%af"
    ]
    
    payload = random.choice(subtle) if is_subtle else random.choice(obvious)
    url = f"/api/download?file={payload}"
    body = ""
    
    return url, method, body, headers, 3, is_subtle

def generate_cmd_injection(is_subtle=False):
    method = random.choice(['GET', 'POST'])
    headers = {'User-Agent': 'Mozilla/5.0', 'Accept': '*/*'}
    
    obvious = [
        "; ls -la",
        "| cat /etc/passwd"
    ]
    
    subtle = [
        "%0als",
        "$(echo whoami)",
        "`id`"
    ]
    
    payload = random.choice(subtle) if is_subtle else random.choice(obvious)
    
    if method == 'GET':
        url = f"/api/ping?ip=127.0.0.1{payload}"
        body = ""
    else:
        url = "/api/tools/ping"
        body = f'{{"target": "127.0.0.1{payload}"}}'
        
    return url, method, body, headers, 4, is_subtle

def main():
    total_samples = 30000
    data = []
    
    # Distributions
    # 0: Normal (~40% normal, ~10% ambiguous -> 50% total)
    # 1: SQLi (~15%)
    # 2: XSS (~15%)
    # 3: Path Traversal (~10%)
    # 4: Command Injection (~10%)
    
    n_normal = int(total_samples * 0.40)
    n_ambiguous = int(total_samples * 0.10)
    n_sqli = int(total_samples * 0.15)
    n_xss = int(total_samples * 0.15)
    n_pt = int(total_samples * 0.10)
    n_ci = int(total_samples * 0.10)
    
    stats = {
        'labels': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0},
        'subtle_attacks': 0,
        'obvious_attacks': 0
    }
    
    requests_to_generate = []
    
    for _ in range(n_normal): requests_to_generate.append(('normal', False))
    for _ in range(n_ambiguous): requests_to_generate.append(('normal', True))
    
    for _ in range(n_sqli): requests_to_generate.append(('sqli', random.choice([True, False])))
    for _ in range(n_xss): requests_to_generate.append(('xss', random.choice([True, False])))
    for _ in range(n_pt): requests_to_generate.append(('pt', random.choice([True, False])))
    for _ in range(n_ci): requests_to_generate.append(('ci', random.choice([True, False])))
    
    random.shuffle(requests_to_generate)
    
    for req_type, is_subtle_or_ambig in requests_to_generate:
        if req_type == 'normal':
            url, method, body, headers, label, is_subtle = generate_normal(is_subtle_or_ambig)
        elif req_type == 'sqli':
            url, method, body, headers, label, is_subtle = generate_sqli(is_subtle_or_ambig)
        elif req_type == 'xss':
            url, method, body, headers, label, is_subtle = generate_xss(is_subtle_or_ambig)
        elif req_type == 'pt':
            url, method, body, headers, label, is_subtle = generate_path_traversal(is_subtle_or_ambig)
        elif req_type == 'ci':
            url, method, body, headers, label, is_subtle = generate_cmd_injection(is_subtle_or_ambig)
            
        stats['labels'][label] += 1
        if label > 0:
            if is_subtle:
                stats['subtle_attacks'] += 1
            else:
                stats['obvious_attacks'] += 1
                
        features = extract_features(url, method, body, headers)
        features['label'] = label
        
        # Adding metadata to DataFrame for tracking if needed, though mostly features + label matter
        data.append(features)
        
    df = pd.DataFrame(data)
    
    output_path = os.path.join(current_dir, 'synthetic_v2_dataset.csv')
    df.to_csv(output_path, index=False)
    
    print(f"Generated {len(df)} samples and saved to {output_path}")
    print("Class Distribution:")
    print(f"  0 (Normal): {stats['labels'][0]}")
    print(f"  1 (SQLi): {stats['labels'][1]}")
    print(f"  2 (XSS): {stats['labels'][2]}")
    print(f"  3 (Path Traversal): {stats['labels'][3]}")
    print(f"  4 (Command Inj): {stats['labels'][4]}")
    print(f"Attacks breakdown: {stats['subtle_attacks']} subtle, {stats['obvious_attacks']} obvious")

if __name__ == "__main__":
    main()
