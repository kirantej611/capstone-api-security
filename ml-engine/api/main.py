"""
Production-grade ML Engine API.

Improvements:
- Ensemble scoring (VAE + Classifier via EnsembleDecisionEngine)
- Real feature importance via perturbation-based XAI
- Temperature-calibrated confidence scores
- Per-class anomaly thresholds
- Model versioning and comprehensive health checks
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import json
import joblib
import numpy as np
import logging
from typing import Dict, Any, Optional, List

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.autoencoder import VariationalAutoencoder
from models.classifier import DeepResidualClassifier
from models.ensemble import EnsembleDecisionEngine, TemperatureScaling
from utils.feature_extraction import extract_features as _extract_features, FEATURE_NAMES, NUM_FEATURES
from utils.inference_policy import (
    detect_attack_indicators,
    has_novel_attack_indicators,
    normalize_request_for_inference,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Attack Detection ML Engine",
    description="Production-grade ensemble ML engine for real-time API threat detection",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Schemas ───────────────────────────────────────

class PredictRequest(BaseModel):
    url: str
    method: str
    body: str = ""
    headers: Dict[str, str] = {}

class PredictResponse(BaseModel):
    anomaly_score: float
    is_anomalous: bool
    threat_type: str
    threat_confidence: float
    all_probabilities: Dict[str, float]
    risk_level: str
    feature_importance: Dict[str, float]
    composite_score: float
    anomaly_confidence: float
    calibrated: bool

class BatchPredictRequest(BaseModel):
    requests: List[PredictRequest]

class ModelStatusResponse(BaseModel):
    is_loaded: bool
    device: str
    global_threshold: float
    temperature: float
    version: str
    input_dim: int
    num_classes: int
    num_features: int


# ── Model State ──────────────────────────────────────────────────────

class ModelState:
    def __init__(self):
        self.autoencoder = None
        self.classifier = None
        self.scaler = None
        self.ensemble: Optional[EnsembleDecisionEngine] = None
        self.global_threshold = 0.0
        self.label_mapping = {}
        self.temperature = 1.0
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = False
        self.normal_mean = None  # Real normal mean for XAI
        self.raw_normal_mean = None
        self.input_dim = NUM_FEATURES
        self.num_classes = 6

    def load_models(self):
        try:
            # ── Load Scaler ──────────────────────────────────
            self.scaler = joblib.load('saved_models/scaler.joblib')
            logger.info("Scaler loaded.")

            # ── Load Thresholds ──────────────────────────────
            with open('saved_models/anomaly_threshold.json', 'r') as f:
                threshold_data = json.load(f)
                self.global_threshold = threshold_data['threshold']
            logger.info(f"Global threshold: {self.global_threshold:.6f}")

            # ── Load Label Mapping ───────────────────────────
            with open('saved_models/label_mapping.json', 'r') as f:
                self.label_mapping = json.load(f)
            self.num_classes = len(self.label_mapping)
            logger.info(f"Label mapping: {self.label_mapping}")

            # ── Load Temperature ─────────────────────────────
            temp_path = 'saved_models/temperature.json'
            if os.path.exists(temp_path):
                with open(temp_path, 'r') as f:
                    self.temperature = json.load(f)['temperature']
                logger.info(f"Temperature: {self.temperature:.4f}")

            # ── Load Normal Mean for XAI ─────────────────────
            mean_path = 'saved_models/raw_normal_mean.npy'
            if os.path.exists(mean_path):
                self.raw_normal_mean = np.load(mean_path)
                logger.info("Raw normal mean loaded for XAI.")
            else:
                self.raw_normal_mean = np.zeros(NUM_FEATURES)
                logger.warning("No raw_normal_mean.npy found, using zeros.")

            scaled_mean_path = 'saved_models/normal_mean.npy'
            if os.path.exists(scaled_mean_path):
                self.normal_mean = np.load(scaled_mean_path)
            else:
                self.normal_mean = np.zeros(NUM_FEATURES)

            # ── Detect input dim from scaler ─────────────────
            if hasattr(self.scaler, 'n_features_in_'):
                self.input_dim = self.scaler.n_features_in_
            logger.info(f"Input dim: {self.input_dim}")

            # ── Load VAE ─────────────────────────────────────
            # Auto-detect latent_dim from saved checkpoint
            vae_state = torch.load('saved_models/autoencoder.pth', map_location=self.device, weights_only=True)
            latent_dim = vae_state['fc_mu.weight'].shape[0]  # mu head output = latent_dim
            logger.info(f"Detected VAE latent_dim={latent_dim}")

            self.autoencoder = VariationalAutoencoder(
                input_dim=self.input_dim, latent_dim=latent_dim
            ).to(self.device)
            self.autoencoder.load_state_dict(vae_state)
            self.autoencoder.eval()
            logger.info("VAE loaded.")

            # ── Load Classifier ──────────────────────────────
            self.classifier = DeepResidualClassifier(
                input_dim=self.input_dim, num_classes=self.num_classes
            ).to(self.device)
            self.classifier.load_state_dict(
                torch.load('saved_models/classifier.pth', map_location=self.device, weights_only=True)
            )
            self.classifier.eval()
            logger.info("Classifier loaded.")

            # ── Setup Ensemble Engine ────────────────────────
            calibrator = TemperatureScaling(temperature=self.temperature)
            self.ensemble = EnsembleDecisionEngine(
                global_threshold=self.global_threshold,
                calibrator=calibrator,
            )
            logger.info("Ensemble engine initialised.")

            self.is_loaded = True
            logger.info("All models loaded successfully.")

        except Exception as e:
            logger.error(f"Error loading models: {e}", exc_info=True)
            self.is_loaded = False


model_state = ModelState()


@app.on_event("startup")
async def startup_event():
    model_state.load_models()


# ── Endpoints ────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {
        "status": "healthy" if model_state.is_loaded else "degraded",
        "models_loaded": model_state.is_loaded,
    }


@app.get("/model/status", response_model=ModelStatusResponse)
async def model_status():
    return ModelStatusResponse(
        is_loaded=model_state.is_loaded,
        device=str(model_state.device),
        global_threshold=model_state.global_threshold,
        temperature=model_state.temperature,
        version="2.0.0",
        input_dim=model_state.input_dim,
        num_classes=model_state.num_classes,
        num_features=NUM_FEATURES,
    )


def extract_request_features(req: PredictRequest) -> np.ndarray:
    """
    Extract features from a PredictRequest using the shared feature extraction module.
    Returns a numpy array of features in canonical order.
    """
    features_dict = _extract_features(
        url=req.url,
        method=req.method,
        body=req.body,
        headers=req.headers
    )
    return np.array([features_dict[k] for k in FEATURE_NAMES])


def compute_feature_importance(
    raw_features: np.ndarray,
    scaled_features: np.ndarray,
    anomaly_score: float,
    top_k: int = 8,
) -> Dict[str, float]:
    """
    Perturbation-based feature importance.
    For each feature, compute how much the anomaly score changes when the
    feature is replaced with the normal mean value.
    """
    if model_state.autoencoder is None or model_state.normal_mean is None:
        return {}

    importances = {}
    base_tensor = torch.tensor(scaled_features, dtype=torch.float32).to(model_state.device)

    with torch.no_grad():
        for i, name in enumerate(FEATURE_NAMES[:model_state.input_dim]):
            # Replace feature i with its normal mean value
            perturbed = base_tensor.clone()
            perturbed[0, i] = float(model_state.normal_mean[i])

            perturbed_score = model_state.autoencoder.get_reconstruction_error(perturbed).item()
            # Importance = how much the score drops when we "normalise" this feature
            importance = anomaly_score - perturbed_score
            importances[name] = max(importance, 0.0)  # only positive contributions

    # Normalise and take top-k
    total = sum(importances.values())
    if total > 0:
        importances = {k: v / total for k, v in importances.items()}

    # Sort by importance and keep top-k
    sorted_imp = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True)[:top_k])
    return sorted_imp


def run_prediction(req: PredictRequest) -> dict:
    """Core prediction logic, separated from endpoint for reuse in batch."""
    model_url, model_body, model_headers = normalize_request_for_inference(
        req.url, req.body, req.headers
    )
    model_req = PredictRequest(
        url=model_url,
        method=req.method,
        body=model_body,
        headers=model_headers,
    )

    # 1. Feature Extraction
    raw_features = extract_request_features(model_req)

    # 2. Scaling
    scaled_features = model_state.scaler.transform(raw_features.reshape(1, -1))

    # 3. Convert to tensor
    x_tensor = torch.tensor(scaled_features, dtype=torch.float32).to(model_state.device)

    # 4. VAE Anomaly Score
    with torch.no_grad():
        anomaly_score = model_state.autoencoder.get_reconstruction_error(x_tensor).item()

    # 5. Classifier
    with torch.no_grad():
        logits = model_state.classifier(x_tensor)[0].cpu().numpy()
        probs = torch.softmax(torch.tensor(logits), dim=0).numpy()

    # 6. Ensemble Decision
    decision = model_state.ensemble.decide(
        anomaly_score=anomaly_score,
        class_probs=probs,
        raw_logits=logits,
        label_mapping=model_state.label_mapping,
        attack_indicators=detect_attack_indicators(
            req.url, req.body, req.headers
        ),
        novelty_indicators=has_novel_attack_indicators(
            req.url, req.method, req.body, req.headers
        ),
    )

    # 7. Feature Importance (real perturbation-based XAI)
    feature_importance = compute_feature_importance(
        raw_features, scaled_features, anomaly_score, top_k=8
    )

    return {
        **decision,
        'feature_importance': feature_importance,
    }


@app.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    if not model_state.is_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded")

    result = run_prediction(req)

    return PredictResponse(
        anomaly_score=result['anomaly_score'],
        is_anomalous=result['is_anomalous'],
        threat_type=result['threat_type'],
        threat_confidence=result['threat_confidence'],
        all_probabilities=result['all_probabilities'],
        risk_level=result['risk_level'],
        feature_importance=result['feature_importance'],
        composite_score=result['composite_score'],
        anomaly_confidence=result['anomaly_confidence'],
        calibrated=result['calibrated'],
    )


@app.post("/predict/batch")
async def predict_batch(batch: BatchPredictRequest):
    """Batch prediction endpoint for processing multiple requests at once."""
    if not model_state.is_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded")

    results = []
    for req in batch.requests:
        try:
            result = run_prediction(req)
            results.append({"status": "ok", **result})
        except Exception as e:
            results.append({"status": "error", "error": str(e)})

    return {
        "total": len(results),
        "predictions": results,
    }
