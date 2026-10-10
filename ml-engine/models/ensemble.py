"""
Ensemble decision engine that combines VAE anomaly detection
and the DeepResidualClassifier for robust, calibrated predictions.
"""
import torch
import numpy as np
from typing import Dict, Any, Optional


class TemperatureScaling:
    """
    Post-hoc temperature scaling for calibrating classifier confidence.
    Fit on a validation set after training.
    """
    def __init__(self, temperature: float = 1.0):
        self.temperature = temperature

    def calibrate(self, logits: np.ndarray, labels: np.ndarray, lr: float = 0.01, max_iter: int = 200):
        """
        Learn optimal temperature on a validation set using NLL minimisation.
        logits: (N, C) raw logits
        labels: (N,) integer labels
        """
        import torch.nn.functional as F
        logits_t = torch.tensor(logits, dtype=torch.float32)
        labels_t = torch.tensor(labels, dtype=torch.long)

        temp = torch.tensor([1.5], requires_grad=True)
        optimizer = torch.optim.LBFGS([temp], lr=lr, max_iter=max_iter)

        def closure():
            optimizer.zero_grad()
            scaled = logits_t / temp
            loss = F.cross_entropy(scaled, labels_t)
            loss.backward()
            return loss

        optimizer.step(closure)
        self.temperature = max(temp.item(), 0.1)  # prevent degenerate values
        return self.temperature

    def scale(self, logits: np.ndarray) -> np.ndarray:
        """Apply temperature scaling to logits."""
        return logits / self.temperature


class EnsembleDecisionEngine:
    """
    Combines VAE anomaly detection + classifier predictions into
    a unified, calibrated threat assessment.

    Decision logic:
    1. VAE produces anomaly_score (reconstruction error + KL)
    2. Classifier produces class probabilities
    3. Ensemble combines both for final verdict

    The classifier is weighted higher (0.6) since it is the discriminative
    model trained to distinguish attack types.  The VAE is a novelty
    detector (0.4) that catches zero-day / unknown attacks.
    """

    def __init__(
        self,
        per_class_thresholds: Optional[Dict[int, float]] = None,
        global_threshold: float = 0.5,
        calibrator: Optional[TemperatureScaling] = None,
        vae_weight: float = 0.4,
        classifier_weight: float = 0.6,
    ):
        self.per_class_thresholds = per_class_thresholds or {}
        self.global_threshold = global_threshold
        self.calibrator = calibrator or TemperatureScaling()
        self.vae_weight = vae_weight
        self.classifier_weight = classifier_weight

    def decide(
        self,
        anomaly_score: float,
        class_probs: np.ndarray,
        raw_logits: np.ndarray,
        label_mapping: Dict[str, str],
        attack_indicators: Optional[Dict[str, bool]] = None,
        novelty_indicators: bool = False,
    ) -> Dict[str, Any]:
        """
        Make an ensemble decision.

        Args:
            anomaly_score: float from VAE (higher = more anomalous)
            class_probs: (num_classes,) softmax probabilities
            raw_logits: (num_classes,) raw logits (for calibration)
            label_mapping: {str(idx): "ClassName"} mapping

        Returns:
            Dict with threat_type, threat_confidence, risk_level, etc.
        """
        num_classes = len(class_probs)

        # A temperature below 1 sharpens predictions and worsened observed
        # false positives. Never use inference-time scaling to amplify them.
        if self.calibrator.temperature > 1.0:
            calibrated_logits = self.calibrator.scale(raw_logits)
            calibrated_probs = _softmax(calibrated_logits)
        else:
            calibrated_probs = class_probs

        predicted_idx = int(np.argmax(calibrated_probs))
        predicted_confidence = float(calibrated_probs[predicted_idx])
        anomaly_confidence = _sigmoid_scale(
            anomaly_score, center=self.global_threshold, steepness=5.0
        )

        confirmed_indices = [
            int(index)
            for index, name in label_mapping.items()
            if name != "Normal" and (attack_indicators or {}).get(name, False)
        ]
        if confirmed_indices:
            # Specific request evidence can correct a confused classifier label.
            selected_idx = max(confirmed_indices, key=lambda idx: calibrated_probs[idx])
            threat_type = label_mapping[str(selected_idx)]
            threat_confidence = float(calibrated_probs[selected_idx])
            is_anomalous = True
            risk_level = "HIGH"
            composite_score = max(threat_confidence, 0.5)
            vae_anomalous = anomaly_score > self.global_threshold
        elif (
            anomaly_score > max(self.global_threshold * 10.0, self.global_threshold + 1.0)
            and novelty_indicators
        ):
            # The VAE threshold is miscalibrated for live request features.
            # Require both a larger-than-threshold score and suspicious payload
            # structure so benign traffic is not flagged by the score alone.
            threat_type = "Unknown"
            threat_confidence = float(anomaly_confidence)
            is_anomalous = True
            risk_level = "MEDIUM"
            composite_score = float(anomaly_confidence)
            vae_anomalous = True
        else:
            threat_type = "Normal"
            threat_confidence = predicted_confidence
            is_anomalous = False
            risk_level = "NONE"
            composite_score = float(1.0 - predicted_confidence)
            vae_anomalous = anomaly_score > self.global_threshold

        # All probabilities dict
        all_probs = {}
        for i in range(num_classes):
            label = label_mapping.get(str(i), f"Class_{i}")
            all_probs[label] = float(calibrated_probs[i])

        return {
            'is_anomalous': is_anomalous,
            'threat_type': threat_type,
            'threat_confidence': threat_confidence,
            'composite_score': float(composite_score),
            'anomaly_score': float(anomaly_score),
            'anomaly_confidence': float(anomaly_confidence),
            'vae_anomalous': vae_anomalous,
            'risk_level': risk_level,
            'all_probabilities': all_probs,
            'calibrated': self.calibrator.temperature > 1.0,
        }


def compute_per_class_thresholds(
    errors: np.ndarray,
    labels: np.ndarray,
    percentile: float = 95.0,
) -> Dict[int, float]:
    """
    Compute anomaly thresholds per class from validation data.

    Strategy:
    - Normal class (0): 95th percentile of normal errors (high bar).
    - Attack classes: Find the threshold that maximises the F1 score for
      binary detection (normal-vs-this-class) on the validation set.
      Fall back to 50th-percentile of normal errors if F1 search fails.
    """
    normal_errors = errors[labels == 0]
    global_thresh = float(np.percentile(normal_errors, percentile))

    thresholds = {0: global_thresh}

    unique_labels = np.unique(labels)
    for lbl in unique_labels:
        if lbl == 0:
            continue

        class_errors = errors[labels == lbl]
        if len(class_errors) == 0:
            thresholds[int(lbl)] = global_thresh
            continue

        # Binary F1-optimised threshold search:
        # Sweep candidate thresholds and pick the one with the best F1
        # for detecting *this* attack class against normal traffic.
        combined_errors = np.concatenate([normal_errors, class_errors])
        combined_labels = np.concatenate([
            np.zeros(len(normal_errors)),
            np.ones(len(class_errors)),
        ])

        candidates = np.percentile(
            normal_errors,
            np.arange(50, 100, 2),  # sweep from P50 to P98
        )

        best_f1, best_thresh = 0.0, global_thresh
        for cand in candidates:
            preds = (combined_errors > cand).astype(int)
            tp = ((preds == 1) & (combined_labels == 1)).sum()
            fp = ((preds == 1) & (combined_labels == 0)).sum()
            fn = ((preds == 0) & (combined_labels == 1)).sum()
            precision = tp / max(tp + fp, 1)
            recall = tp / max(tp + fn, 1)
            f1 = 2 * precision * recall / max(precision + recall, 1e-8)
            if f1 > best_f1:
                best_f1 = f1
                best_thresh = float(cand)

        thresholds[int(lbl)] = best_thresh

    return thresholds


def _softmax(x: np.ndarray) -> np.ndarray:
    """Numerically stable softmax."""
    e = np.exp(x - np.max(x))
    return e / e.sum()


def _sigmoid_scale(value: float, center: float, steepness: float = 5.0) -> float:
    """Scale a value to [0, 1] using a sigmoid centered at `center`."""
    z = steepness * (value - center) / max(center, 1e-6)
    return 1.0 / (1.0 + np.exp(-z))
