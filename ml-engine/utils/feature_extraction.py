import math
import re
from urllib.parse import urlparse, parse_qsl

def calculate_entropy(text: str) -> float:
    """Calculate the Shannon entropy of a string."""
    if not text:
        return 0.0
    entropy = 0.0
    length = len(text)
    char_counts = {}
    for char in text:
        char_counts[char] = char_counts.get(char, 0) + 1
    for count in char_counts.values():
        prob = count / length
        entropy -= prob * math.log2(prob)
    return entropy

def count_sql_keywords(text: str) -> int:
    """Count SQL keywords in the text."""
    keywords = ['select', 'union', 'drop', 'insert', 'delete', 'update', 'where', 'from', 'or', 'and']
    text_lower = text.lower()
    return sum(len(re.findall(rf'\b{kw}\b', text_lower)) for kw in keywords)

def count_xss_keywords(text: str) -> int:
    """Count XSS related tokens in the text."""
    keywords = ['<script', 'alert', 'onerror', 'onload', 'javascript:']
    text_lower = text.lower()
    return sum(text_lower.count(kw) for kw in keywords)

def count_path_traversal_patterns(text: str) -> int:
    """Count path traversal patterns like ../ or ..\\."""
    return len(re.findall(r'\.\./|\.\.\\', text))

def count_command_injection_patterns(text: str) -> int:
    """Count command injection patterns like |, ;, $(, `."""
    return len(re.findall(r'\||;|\$\(|`', text))

def extract_features(url: str, method: str, body: str, headers: dict) -> dict:
    """
    Extract 18 numeric features from HTTP request components.
    """
    method = method.upper()
    body = body or ""
    url = url or ""
    
    full_request = f"{url} {body} " + " ".join([f"{k}:{v}" for k,v in headers.items()])
    
    # 1. url_length
    url_length = len(url)
    
    # 2. body_length
    body_length = len(body)
    
    # 3. num_special_chars
    num_special_chars = len(re.findall(r'[\'\"<>;\|]', full_request))
    
    # 4. num_sql_keywords
    num_sql_keywords = count_sql_keywords(full_request)
    
    # 5. num_xss_keywords
    num_xss_keywords = count_xss_keywords(full_request)
    
    # 6. num_path_traversal_patterns
    num_path_traversal_patterns = count_path_traversal_patterns(full_request)
    
    # 7. num_command_injection_patterns
    num_command_injection_patterns = count_command_injection_patterns(full_request)
    
    # 8. has_encoded_chars
    has_encoded_chars = 1 if re.search(r'%[0-9A-Fa-f]{2}', full_request) else 0
    
    # URL parsing for parameters
    parsed_url = urlparse(url)
    query_params = parse_qsl(parsed_url.query)
    
    # Assume body is url-encoded if no other info, or just try to parse
    body_params = []
    if '=' in body:
        body_params = parse_qsl(body)
    
    all_params = query_params + body_params
    
    # 9. num_parameters
    num_parameters = len(all_params)
    
    # 10. max_param_value_length
    max_param_value_length = max([len(v) for k, v in all_params]) if all_params else 0
    
    # 11. avg_param_value_length
    avg_param_value_length = sum([len(v) for k, v in all_params]) / num_parameters if num_parameters > 0 else 0
    
    # 12. payload_entropy
    payload = full_request
    payload_entropy = calculate_entropy(payload)
    
    # 13. num_digits_ratio
    num_digits = sum(1 for c in payload if c.isdigit())
    num_digits_ratio = num_digits / len(payload) if len(payload) > 0 else 0
    
    # 14. uppercase_ratio
    num_uppercase = sum(1 for c in payload if c.isupper())
    uppercase_ratio = num_uppercase / len(payload) if len(payload) > 0 else 0
    
    # 15. num_dots
    num_dots = parsed_url.path.count('.')
    
    # 16. num_slashes
    num_slashes = parsed_url.path.count('/')
    
    # 17. request_method
    method_map = {'GET': 0, 'POST': 1, 'PUT': 2, 'DELETE': 3}
    request_method = method_map.get(method, 0) # Default to GET
    
    # 18. content_length_header
    content_length_header = int(headers.get('Content-Length', headers.get('content-length', 0)))
    if content_length_header == 0 and body_length > 0:
        content_length_header = body_length
        
    return {
        'url_length': url_length,
        'body_length': body_length,
        'num_special_chars': num_special_chars,
        'num_sql_keywords': num_sql_keywords,
        'num_xss_keywords': num_xss_keywords,
        'num_path_traversal_patterns': num_path_traversal_patterns,
        'num_command_injection_patterns': num_command_injection_patterns,
        'has_encoded_chars': has_encoded_chars,
        'num_parameters': num_parameters,
        'max_param_value_length': max_param_value_length,
        'avg_param_value_length': avg_param_value_length,
        'payload_entropy': payload_entropy,
        'num_digits_ratio': num_digits_ratio,
        'uppercase_ratio': uppercase_ratio,
        'num_dots': num_dots,
        'num_slashes': num_slashes,
        'request_method': request_method,
        'content_length_header': content_length_header
    }
