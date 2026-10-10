"""Inference-time request normalization and attack-signal corroboration."""

import re
from typing import Dict, Mapping, Tuple
from urllib.parse import unquote_plus, urlsplit

from utils.feature_extraction import extract_features

_MODEL_HEADERS = {
    "authorization",
    "content-type",
    "cookie",
}
_CANONICAL_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}
_ATTACK_PATTERNS = {
    "SQLi": re.compile(
        r"\bunion(?:\s+|/\*.*?\*/)+(?:all(?:\s+|/\*.*?\*/)+)?select\b"
        r"|\b(?:or|and)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+"
        r"|['\"]\s*(?:or|and)\s+['\"]?\w+"
        r"|\b(?:drop\s+table|insert\s+into|delete\s+from|xp_cmdshell|"
        r"information_schema)\b",
        re.IGNORECASE,
    ),
    "XSS": re.compile(
        r"<\s*script\b|javascript\s*:|<\s*iframe\b|"
        r"\bon[a-z]+\s*=|"
        r"\balert\s*\(|document\.(?:cookie|write|location)|\beval\s*\(",
        re.IGNORECASE,
    ),
    "PathTraversal": re.compile(
        r"(?:\.\./|\.\.\\|%2e%2e(?:%2f|/|%5c|\\)|"
        r"/etc/(?:passwd|shadow)|/proc/self)",
        re.IGNORECASE,
    ),
    "CommandInjection": re.compile(
        r"(?:;|\||&&|`|\$\(|\$\{?IFS\}?|\n)\s*"
        r"(?:/(?:usr/)?bin/)?"
        r"(?:id|whoami|uname|cat|ls|curl|wget|nc|bash|sh|python|perl|ruby)\b",
        re.IGNORECASE,
    ),
    "SSRF": re.compile(
        r"(?:169\.254\.169\.254|metadata\.google\.internal|"
        r"(?:https?://|=)(?:127\.0\.0\.1|localhost|0\.0\.0\.0)"
        r"(?=[:/?&#\s]|$)|"
        r"gopher://|dict://|ftp://)",
        re.IGNORECASE,
    ),
}


def normalize_request_for_inference(
    url: str, body: str, headers: Mapping[str, str]
) -> Tuple[str, str, Dict[str, str]]:
    """Remove origin/browser noise while preserving user-controlled payloads."""
    parsed = urlsplit(url)
    target = parsed.path or "/"
    if parsed.query:
        target = f"{target}?{parsed.query}"

    selected_headers = {
        **_CANONICAL_HEADERS,
        **{
            key: value
            for key, value in headers.items()
            if key.lower() in _MODEL_HEADERS
            or (
                key.lower().startswith("x-")
                and not key.lower().startswith("x-forwarded-")
                and key.lower() not in {"x-request-id", "x-real-ip"}
            )
        },
    }
    return target, body or "", selected_headers


def detect_attack_indicators(
    url: str, body: str, headers: Mapping[str, str]
) -> Dict[str, bool]:
    """Find class-specific payload evidence independent of model confidence."""
    parsed_url = urlsplit(url)
    request_target = parsed_url.path
    if parsed_url.query:
        request_target = f"{request_target}?{parsed_url.query}"
    payload_parts = [request_target, body]
    payload_parts.extend(headers.values())
    payload = " ".join(part for part in payload_parts if part)

    decoded_payload = payload
    for _ in range(2):
        decoded_payload = unquote_plus(decoded_payload)

    evidence = {
        "SQLi": bool(_ATTACK_PATTERNS["SQLi"].search(decoded_payload)),
        "XSS": bool(_ATTACK_PATTERNS["XSS"].search(decoded_payload)),
        "PathTraversal": bool(_ATTACK_PATTERNS["PathTraversal"].search(decoded_payload)),
        "CommandInjection": bool(_ATTACK_PATTERNS["CommandInjection"].search(decoded_payload)),
        "SSRF": bool(_ATTACK_PATTERNS["SSRF"].search(decoded_payload)),
    }
    return evidence


def has_novel_attack_indicators(
    url: str, method: str, body: str, headers: Mapping[str, str]
) -> bool:
    """Require suspicious payload structure alongside VAE novelty."""
    parsed_url = urlsplit(url)
    request_target = parsed_url.path or "/"
    if parsed_url.query:
        request_target = f"{request_target}?{parsed_url.query}"

    decoded_url, decoded_body = request_target, body
    for _ in range(2):
        decoded_url = unquote_plus(decoded_url)
        decoded_body = unquote_plus(decoded_body)

    feature_sets = (
        extract_features(request_target, method, body, dict(headers)),
        extract_features(decoded_url, method, decoded_body, dict(headers)),
    )
    for features in feature_sets:
        if any(
            (
                features["double_encoding_depth"] > 0,
                features["unicode_escape_count"] > 0,
                features["null_byte_count"] > 0,
                features["comment_sequence_count"] > 0,
                features["hex_encoding_count"] > 0,
                features["nested_tag_depth"] > 0,
                features["event_handler_count"] > 0,
                features["protocol_handler_count"] > 0,
                features["suspicious_header_count"] > 0,
                features["curly_brace_depth"] > 0,
                features["non_printable_char_count"] > 0,
                features["consecutive_special_max"] >= 5,
            )
        ):
            return True
    return False
