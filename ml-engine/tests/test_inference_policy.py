import numpy as np

from models.ensemble import EnsembleDecisionEngine, TemperatureScaling
from utils.inference_policy import (
    detect_attack_indicators,
    has_novel_attack_indicators,
    normalize_request_for_inference,
)


LABELS = {
    "0": "Normal",
    "1": "SQLi",
    "2": "XSS",
    "3": "PathTraversal",
    "4": "CommandInjection",
    "5": "SSRF",
}


def test_normalize_absolute_url_and_browser_headers():
    target, body, headers = normalize_request_for_inference(
        "http://localhost:8080/api/products?sort=price#top",
        "",
        {
            "Host": "localhost:8080",
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Request-Id": "request-id",
            "X-Forwarded-Host": "api.example.test",
            "Content-Type": "application/json",
            "X-Custom-Payload": "value",
        },
    )

    assert target == "/api/products?sort=price"
    assert body == ""
    assert headers == {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Custom-Payload": "value",
    }


def test_model_headers_are_canonical_for_browser_and_headerless_clients():
    _, _, no_headers = normalize_request_for_inference("/api/products", "", {})
    _, _, browser_headers = normalize_request_for_inference(
        "/api/products",
        "",
        {
            "User-Agent": "Some other browser",
            "Accept": "text/html,*/*",
            "Accept-Language": "en-US",
            "Host": "localhost:8080",
        },
    )

    assert no_headers == browser_headers


def test_attack_indicators_require_class_specific_payloads():
    assert not any(detect_attack_indicators("/api/products", "", {}).values())
    assert detect_attack_indicators(
        "/api/login?username=admin%27%20OR%201=1", "", {}
    )["SQLi"]
    assert detect_attack_indicators(
        "/api/search?q=UNION%2F%2A%2A%2FSELECT", "", {}
    )["SQLi"]
    assert detect_attack_indicators(
        "/api/search?q=UNION+SELECT", "", {}
    )["SQLi"]
    assert detect_attack_indicators(
        "/api/search?q=%3Cscript%3Ealert(1)%3C/script%3E", "", {}
    )["XSS"]
    assert detect_attack_indicators(
        "/api/files?path=../../etc/passwd", "", {}
    )["PathTraversal"]
    assert detect_attack_indicators("/api/run?cmd=id%3Bwhoami", "", {})[
        "CommandInjection"
    ]
    assert detect_attack_indicators(
        "/api/run?cmd=%24IFS%20id", "", {}
    )["CommandInjection"]
    assert detect_attack_indicators(
        "/api/run?cmd=%3B%20%2Fbin%2Fbash%20-c%20id", "", {}
    )["CommandInjection"]
    assert detect_attack_indicators(
        "/api/run?cmd=%0Awhoami", "", {}
    )["CommandInjection"]
    assert detect_attack_indicators(
        "/api/comments", '{"value":"<svg onfocus=alert(1)>"}', {}
    )["XSS"]
    assert detect_attack_indicators(
        "/api/fetch?url=http%3A%2F%2F169.254.169.254%2Flatest", "", {}
    )["SSRF"]
    assert detect_attack_indicators(
        "http://localhost:8080/api/products", "", {"Host": "localhost:8080"}
    )["SSRF"] is False
    assert detect_attack_indicators(
        "/api/fetch?url=localhost%3A8080%2Fadmin", "", {}
    )["SSRF"]
    assert not detect_attack_indicators(
        "/api/products", "", {"Accept-Language": "en-US,en;q=0.9"}
    )["CommandInjection"]
    assert not detect_attack_indicators(
        "/api/products",
        "",
        {"User-Agent": "Chrome/120.0.0.0 Safari/537.36"},
    )["SSRF"]
    assert not detect_attack_indicators("/api/products?comment=--help", "", {})[
        "SQLi"
    ]


def test_indicators_inspect_original_headers_not_model_normalized_headers():
    original_headers = {
        "User-Agent": "Mozilla/5.0 () { :; }; /bin/bash -c id",
        "Referer": "https://shop.example/search?q=UNION+SELECT",
    }
    _, _, model_headers = normalize_request_for_inference(
        "/api/products", "", original_headers
    )

    assert "Referer" not in model_headers
    assert model_headers["User-Agent"].startswith("Mozilla/5.0 (Windows")
    assert detect_attack_indicators(
        "http://localhost:8080/api/products", "", original_headers
    )["CommandInjection"]
    assert detect_attack_indicators(
        "http://localhost:8080/api/products", "", original_headers
    )["SQLi"]
    assert not any(
        detect_attack_indicators(
            "http://localhost:8080/api/products", "", model_headers
        ).values()
    )


def test_unsupported_anomaly_is_flagged_as_unknown_not_block_level():
    engine = EnsembleDecisionEngine(
        global_threshold=0.6,
        calibrator=TemperatureScaling(temperature=0.1),
    )
    decision = engine.decide(
        anomaly_score=20.0,
        class_probs=np.array([0.01, 0.01, 0.01, 0.01, 0.95, 0.01]),
        raw_logits=np.array([-1.0, -1.0, -1.0, -1.0, 4.0, -1.0]),
        label_mapping=LABELS,
        attack_indicators={name: False for name in LABELS.values()},
        novelty_indicators=True,
    )

    assert decision["is_anomalous"]
    assert decision["threat_type"] == "Unknown"
    assert decision["risk_level"] == "MEDIUM"
    assert not decision["calibrated"]


def test_high_vae_score_without_suspicious_payload_does_not_flag_benign():
    engine = EnsembleDecisionEngine(
        global_threshold=0.6,
        calibrator=TemperatureScaling(temperature=0.1),
    )
    decision = engine.decide(
        anomaly_score=20.0,
        class_probs=np.array([0.01, 0.01, 0.01, 0.01, 0.95, 0.01]),
        raw_logits=np.array([-1.0, -1.0, -1.0, -1.0, 4.0, -1.0]),
        label_mapping=LABELS,
        attack_indicators={name: False for name in LABELS.values()},
        novelty_indicators=False,
    )

    assert not decision["is_anomalous"]
    assert decision["threat_type"] == "Normal"
    assert decision["vae_anomalous"]


def test_novel_payload_indicator_requires_anomalous_score():
    assert not has_novel_attack_indicators(
        "/api/products", "GET", "", {}
    )
    assert has_novel_attack_indicators(
        "/api/search?q=%24%7B%7B7*7%7D%7D%3B%3b", "GET", "", {}
    )
    assert not has_novel_attack_indicators(
        "http://localhost:8080/api/products",
        "GET",
        "",
        {"Host": "localhost:8080"},
    )


def test_specific_evidence_corrects_classifier_label():
    engine = EnsembleDecisionEngine(
        global_threshold=0.6,
        calibrator=TemperatureScaling(temperature=0.1),
    )
    decision = engine.decide(
        anomaly_score=10.0,
        class_probs=np.array([0.01, 0.01, 0.01, 0.01, 0.01, 0.95]),
        raw_logits=np.array([-1.0, -1.0, -1.0, -1.0, -1.0, 4.0]),
        label_mapping=LABELS,
        attack_indicators={
            "Normal": False,
            "SQLi": True,
            "XSS": False,
            "PathTraversal": False,
            "CommandInjection": False,
            "SSRF": False,
        },
        novelty_indicators=True,
    )

    assert decision["is_anomalous"]
    assert decision["threat_type"] == "SQLi"
    assert decision["risk_level"] == "HIGH"


def test_classifier_attack_label_alone_does_not_flag_normal_traffic():
    engine = EnsembleDecisionEngine(
        global_threshold=0.6,
        calibrator=TemperatureScaling(temperature=0.1),
    )
    decision = engine.decide(
        anomaly_score=0.1,
        class_probs=np.array([0.01, 0.01, 0.01, 0.01, 0.95, 0.01]),
        raw_logits=np.array([-1.0, -1.0, -1.0, -1.0, 4.0, -1.0]),
        label_mapping=LABELS,
        attack_indicators={name: False for name in LABELS.values()},
        novelty_indicators=False,
    )

    assert not decision["is_anomalous"]
    assert decision["threat_type"] == "Normal"
    assert decision["risk_level"] == "NONE"
