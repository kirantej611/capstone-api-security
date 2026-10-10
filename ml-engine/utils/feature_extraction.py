import math
import re
from urllib.parse import urlparse, parse_qsl, unquote


# ──────────────────────────────────────────────────────────────────────
# Atomic counters / detectors
# ──────────────────────────────────────────────────────────────────────

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
    keywords = [
        'select', 'union', 'drop', 'insert', 'delete', 'update',
        'where', 'from', 'or', 'and', 'having', 'group', 'order',
        'exec', 'execute', 'xp_', 'sp_', 'into', 'outfile',
        'load_file', 'benchmark', 'sleep', 'waitfor', 'delay',
        'concat', 'char', 'cast', 'convert', 'substring', 'ascii',
        'information_schema', 'table_name', 'column_name',
    ]
    text_lower = text.lower()
    return sum(len(re.findall(rf'\b{kw}\b', text_lower)) for kw in keywords)


def count_xss_keywords(text: str) -> int:
    """Count XSS related tokens in the text."""
    keywords = [
        '<script', 'alert(', 'onerror', 'onload', 'javascript:',
        'document.cookie', 'document.write', 'eval(', 'innerhtml',
        'fromcharcode', 'expression(', 'vbscript:', 'livescript:',
        '<iframe', '<object', '<embed', '<applet',
    ]
    text_lower = text.lower()
    return sum(text_lower.count(kw) for kw in keywords)


def count_path_traversal_patterns(text: str) -> int:
    """Count path traversal patterns like ../ or ..\\."""
    return len(re.findall(r'\.\./|\.\.\\|\.\.%2[fF]|\.\.%5[cC]', text))


def count_command_injection_patterns(text: str) -> int:
    """Count command injection patterns like |, ;, $(, `."""
    return len(re.findall(r'\||;|\$\(|`|%0[aAdD]|\$\{', text))


def count_double_encoding_depth(text: str) -> int:
    """
    Detect double/triple percent-encoding.
    %25XX = double-encoded %XX.  %2525XX = triple.
    """
    depth = 0
    cur = text
    while '%25' in cur:
        depth += 1
        cur = cur.replace('%25', '%', 1)
    return depth


def count_unicode_escapes(text: str) -> int:
    r"""Count Unicode escape sequences like \uXXXX, \xXX."""
    return len(re.findall(r'\\u[0-9a-fA-F]{4}|\\x[0-9a-fA-F]{2}', text))


def count_null_bytes(text: str) -> int:
    """Count null-byte injection attempts (%00, \\x00, \\0)."""
    return len(re.findall(r'%00|\\x00|\\0(?![0-9])', text))


def count_comment_sequences(text: str) -> int:
    """Count SQL / code comment markers used for evasion."""
    patterns = [r'/\*', r'\*/', r'--', r'#(?![0-9a-fA-F]{3,6}\b)']
    return sum(len(re.findall(p, text)) for p in patterns)


def count_hex_encoding(text: str) -> int:
    """Count 0x-prefixed hex values (common in SQLi)."""
    return len(re.findall(r'0x[0-9a-fA-F]{2,}', text))


def count_nested_tag_depth(text: str) -> int:
    """Approximate the maximum nesting depth of HTML tags."""
    depth = 0
    max_depth = 0
    for m in re.finditer(r'<(/?)(\w+)', text):
        if m.group(1) == '':
            depth += 1
            max_depth = max(max_depth, depth)
        else:
            depth = max(0, depth - 1)
    return max_depth


def count_event_handlers(text: str) -> int:
    """Count HTML event handler attributes (XSS vectors)."""
    handlers = [
        'onclick', 'onmouseover', 'onfocus', 'onblur', 'onload',
        'onerror', 'onsubmit', 'onkeydown', 'onkeyup', 'onkeypress',
        'onmouseout', 'onmouseenter', 'onchange', 'oninput',
        'onanimationend', 'ontransitionend', 'onwheel', 'onscroll',
        'onpointerdown', 'onautocomplete', 'onbeforeprint',
    ]
    text_lower = text.lower()
    return sum(1 for h in handlers if h in text_lower)


def count_protocol_handlers(text: str) -> int:
    """Count suspicious protocol handlers."""
    protocols = [
        'javascript:', 'data:', 'vbscript:', 'livescript:',
        'blob:', 'file:', 'mhtml:', 'cid:',
    ]
    text_lower = text.lower()
    return sum(text_lower.count(p) for p in protocols)


def count_suspicious_headers(headers: dict) -> int:
    """Count suspicious or unusual headers."""
    suspicious = 0
    for k, v in headers.items():
        kl = k.lower()
        # Stacked X-Forwarded-For (IP spoofing)
        if kl == 'x-forwarded-for' and ',' in v:
            suspicious += 1
        # Oversized cookie
        if kl == 'cookie' and len(v) > 4096:
            suspicious += 1
        # Suspicious content types
        if kl == 'content-type' and any(x in v.lower() for x in ['text/xml', 'application/xml', 'text/html']):
            suspicious += 1
        # Unusual authorization patterns
        if kl == 'authorization' and len(v) > 2048:
            suspicious += 1
    return suspicious


def has_base64_pattern(text: str) -> int:
    """Detect probable base64-encoded payloads (≥16 chars of base64 alphabet)."""
    return 1 if re.search(r'[A-Za-z0-9+/]{16,}={0,2}', text) else 0


def max_consecutive_special(text: str) -> int:
    """Return the longest run of consecutive non-alphanumeric characters."""
    runs = re.findall(r'[^a-zA-Z0-9]+', text)
    return max((len(r) for r in runs), default=0)


def count_ssrf_indicators(text: str) -> int:
    """Count indicators of server-side request forgery."""
    patterns = [
        r'127\.0\.0\.1', r'localhost', r'0\.0\.0\.0',
        r'169\.254\.169\.254',  # AWS metadata
        r'metadata\.google',  # GCP metadata
        r'10\.\d+\.\d+\.\d+', r'172\.(1[6-9]|2\d|3[01])\.\d+\.\d+',
        r'192\.168\.\d+\.\d+',
        r'http://[^/]*@',  # URL with embedded credentials
        r'gopher://', r'dict://', r'ftp://',
    ]
    text_lower = text.lower()
    return sum(len(re.findall(p, text_lower)) for p in patterns)


def count_template_injection(text: str) -> int:
    """Count template injection patterns like {{, ${, #{, <%."""
    return len(re.findall(r'\{\{|\$\{|#\{|<%|%>', text))


# ──────────────────────────────────────────────────────────────────────
# Main feature vector
# ──────────────────────────────────────────────────────────────────────

# Canonical ordered list of all 42 features.
FEATURE_NAMES = [
    # ── Original core (18) ──────────────────────────────────
    'url_length',
    'body_length',
    'num_special_chars',
    'num_sql_keywords',
    'num_xss_keywords',
    'num_path_traversal_patterns',
    'num_command_injection_patterns',
    'has_encoded_chars',
    'num_parameters',
    'max_param_value_length',
    'avg_param_value_length',
    'payload_entropy',
    'num_digits_ratio',
    'uppercase_ratio',
    'num_dots',
    'num_slashes',
    'request_method',
    'content_length_header',
    # ── New features (24) ───────────────────────────────────
    'double_encoding_depth',
    'unicode_escape_count',
    'null_byte_count',
    'comment_sequence_count',
    'hex_encoding_count',
    'nested_tag_depth',
    'event_handler_count',
    'protocol_handler_count',
    'suspicious_header_count',
    'param_name_entropy',
    'repeated_char_ratio',
    'non_printable_char_count',
    'max_param_name_length',
    'query_depth',
    'body_entropy',
    'url_entropy',
    'has_base64_pattern',
    'semicolon_count',
    'pipe_count',
    'backtick_count',
    'curly_brace_depth',
    'ratio_non_alnum',
    'consecutive_special_max',
    'ssrf_indicator_count',
]

NUM_FEATURES = len(FEATURE_NAMES)  # 42


def extract_features(url: str, method: str, body: str, headers: dict) -> dict:
    """
    Extract 42 numeric features from HTTP request components.
    """
    method = method.upper()
    body = body or ""
    url = url or ""

    full_request = f"{url} {body} " + " ".join(f"{k}:{v}" for k, v in headers.items())

    # URL parsing
    parsed_url = urlparse(url)
    query_params = parse_qsl(parsed_url.query)

    body_params = []
    if '=' in body:
        body_params = parse_qsl(body)
    all_params = query_params + body_params

    num_parameters = len(all_params)

    # ── Original 18 ─────────────────────────────────────────
    url_length = len(url)
    body_length = len(body)
    num_special_chars = len(re.findall(r'[\'\"<>;|\\`\{\}\[\]]', full_request))
    num_sql_kw = count_sql_keywords(full_request)
    num_xss_kw = count_xss_keywords(full_request)
    num_pt = count_path_traversal_patterns(full_request)
    num_ci = count_command_injection_patterns(full_request)
    has_enc = 1 if re.search(r'%[0-9A-Fa-f]{2}', full_request) else 0
    max_pv_len = max((len(v) for _, v in all_params), default=0)
    avg_pv_len = (sum(len(v) for _, v in all_params) / num_parameters) if num_parameters > 0 else 0
    payload_entropy = calculate_entropy(full_request)
    payload = full_request
    num_digits_ratio = sum(1 for c in payload if c.isdigit()) / max(len(payload), 1)
    uppercase_ratio = sum(1 for c in payload if c.isupper()) / max(len(payload), 1)
    num_dots = parsed_url.path.count('.')
    num_slashes = parsed_url.path.count('/')
    method_map = {'GET': 0, 'POST': 1, 'PUT': 2, 'DELETE': 3, 'PATCH': 4, 'OPTIONS': 5, 'HEAD': 6}
    request_method = method_map.get(method, 0)
    content_length_header = int(headers.get('Content-Length', headers.get('content-length', 0)))
    if content_length_header == 0 and body_length > 0:
        content_length_header = body_length

    # ── New 24 features ─────────────────────────────────────
    double_enc = count_double_encoding_depth(full_request)
    unicode_esc = count_unicode_escapes(full_request)
    null_bytes = count_null_bytes(full_request)
    comment_seq = count_comment_sequences(full_request)
    hex_enc = count_hex_encoding(full_request)
    nested_tags = count_nested_tag_depth(full_request)
    event_handlers = count_event_handlers(full_request)
    proto_handlers = count_protocol_handlers(full_request)
    susp_headers = count_suspicious_headers(headers)

    # Param name entropy
    param_names = [k for k, _ in all_params]
    param_name_entropy = calculate_entropy(' '.join(param_names)) if param_names else 0.0

    # Repeated character ratio — longest run of same char / total length
    if full_request:
        max_repeat = max(len(m.group()) for m in re.finditer(r'(.)\1*', full_request))
        repeated_char_ratio = max_repeat / len(full_request)
    else:
        repeated_char_ratio = 0.0

    # Non-printable character count
    non_printable = sum(1 for c in full_request if ord(c) < 32 and c not in '\n\r\t')

    # Max param name length
    max_pn_len = max((len(k) for k, _ in all_params), default=0)

    # Query depth (number of & separators)
    query_depth = parsed_url.query.count('&') + (1 if parsed_url.query else 0)

    # Body / URL entropy (separate from full payload)
    body_ent = calculate_entropy(body)
    url_ent = calculate_entropy(url)

    # Base64 pattern
    b64 = has_base64_pattern(full_request)

    # Individual command-injection markers
    semicolon_cnt = full_request.count(';')
    pipe_cnt = full_request.count('|')
    backtick_cnt = full_request.count('`')

    # Template injection depth
    curly_depth = count_template_injection(full_request)

    # Ratio non-alnum
    non_alnum = sum(1 for c in full_request if not c.isalnum())
    ratio_non_alnum = non_alnum / max(len(full_request), 1)

    # Consecutive special max
    consec_special = max_consecutive_special(full_request)

    # SSRF indicators
    ssrf_ind = count_ssrf_indicators(full_request)

    return {
        'url_length': url_length,
        'body_length': body_length,
        'num_special_chars': num_special_chars,
        'num_sql_keywords': num_sql_kw,
        'num_xss_keywords': num_xss_kw,
        'num_path_traversal_patterns': num_pt,
        'num_command_injection_patterns': num_ci,
        'has_encoded_chars': has_enc,
        'num_parameters': num_parameters,
        'max_param_value_length': max_pv_len,
        'avg_param_value_length': avg_pv_len,
        'payload_entropy': payload_entropy,
        'num_digits_ratio': num_digits_ratio,
        'uppercase_ratio': uppercase_ratio,
        'num_dots': num_dots,
        'num_slashes': num_slashes,
        'request_method': request_method,
        'content_length_header': content_length_header,
        # ── new ──
        'double_encoding_depth': double_enc,
        'unicode_escape_count': unicode_esc,
        'null_byte_count': null_bytes,
        'comment_sequence_count': comment_seq,
        'hex_encoding_count': hex_enc,
        'nested_tag_depth': nested_tags,
        'event_handler_count': event_handlers,
        'protocol_handler_count': proto_handlers,
        'suspicious_header_count': susp_headers,
        'param_name_entropy': param_name_entropy,
        'repeated_char_ratio': repeated_char_ratio,
        'non_printable_char_count': non_printable,
        'max_param_name_length': max_pn_len,
        'query_depth': query_depth,
        'body_entropy': body_ent,
        'url_entropy': url_ent,
        'has_base64_pattern': b64,
        'semicolon_count': semicolon_cnt,
        'pipe_count': pipe_cnt,
        'backtick_count': backtick_cnt,
        'curly_brace_depth': curly_depth,
        'ratio_non_alnum': ratio_non_alnum,
        'consecutive_special_max': consec_special,
        'ssrf_indicator_count': ssrf_ind,
    }
