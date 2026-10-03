from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import json
import joblib
import numpy as np
import logging
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.autoencoder import DeepAutoencoder
from models.classifier import HybridClassifier
from utils.feature_extraction import extract_features as _extract_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Attack Detection ML Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class ModelState:
    def __init__(self):
        self.autoencoder = None
        self.classifier = None
        self.scaler = None
        self.threshold = 0.0
        self.label_mapping = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = False
        
        self.feature_names = [
            "url_length", "body_length", "num_special_chars", "num_sql_keywords",
            "num_xss_keywords", "num_path_traversal_patterns", "num_command_injection_patterns",
            "has_encoded_chars", "num_parameters", "max_param_value_length",
            "avg_param_value_length", "payload_entropy", "num_digits_ratio",
            "uppercase_ratio", "num_dots", "num_slashes", "request_method",
            "content_length_header"
        ]
        
        # Approximated normal mean for XAI (mocked)
        self.normal_mean = np.zeros(18)

    def load_models(self):
        try:
            # Load Scaler
            self.scaler = joblib.load('saved_models/scaler.joblib')
            
            # Load Threshold
            with open('saved_models/anomaly_threshold.json', 'r') as f:
                self.threshold = json.load(f)['threshold']
                
            # Load Label Mapping
            with open('saved_models/label_mapping.json', 'r') as f:
                self.label_mapping = json.load(f)

            # Load Autoencoder
            self.autoencoder = DeepAutoencoder(input_dim=18).to(self.device)
            self.autoencoder.load_state_dict(torch.load('saved_models/autoencoder.pth', map_location=self.device))
            self.autoencoder.eval()

            # Load Classifier
            self.classifier = HybridClassifier(input_dim=18, num_classes=5).to(self.device)
            self.classifier.load_state_dict(torch.load('saved_models/classifier.pth', map_location=self.device))
            self.classifier.eval()
            
            self.is_loaded = True
            logger.info("Models loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading models: {e}")

model_state = ModelState()

@app.on_event("startup")
async def startup_event():
    model_state.load_models()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/model/status")
async def model_status():
    return {
        "is_loaded": model_state.is_loaded,
        "device": str(model_state.device),
        "threshold": model_state.threshold,
        "version": "1.0.0"
    }

def extract_request_features(req: PredictRequest) -> np.ndarray:
    """
    Extract features from a PredictRequest using the shared feature extraction module.
    Returns a numpy array of 18 features in the correct order.
    """
    features_dict = _extract_features(
        url=req.url,
        method=req.method,
        body=req.body,
        headers=req.headers
    )
    # Ensure consistent ordering matching the training pipeline
    feature_order = [
        'url_length', 'body_length', 'num_special_chars', 'num_sql_keywords',
        'num_xss_keywords', 'num_path_traversal_patterns', 'num_command_injection_patterns',
        'has_encoded_chars', 'num_parameters', 'max_param_value_length',
        'avg_param_value_length', 'payload_entropy', 'num_digits_ratio',
        'uppercase_ratio', 'num_dots', 'num_slashes', 'request_method',
        'content_length_header'
    ]
    return np.array([features_dict[k] for k in feature_order])

@app.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    if not model_state.is_loaded:
        raise HTTPException(status_code=503, detail="Models not loaded")

    # 1. Feature Extraction
    raw_features = extract_request_features(req)
    
    # 2. Preprocessing (Scaling)
    # Scaler expects 2D array
    scaled_features = model_state.scaler.transform(raw_features.reshape(1, -1))
    
    # Convert to Tensor
    x_tensor = torch.tensor(scaled_features, dtype=torch.float32).to(model_state.device)
    
    # 3. Anomaly Detection
    with torch.no_grad():
        anomaly_score = model_state.autoencoder.get_reconstruction_error(x_tensor).item()
        
    is_anomalous = anomaly_score > model_state.threshold
    
    # 4. Threat Classification
    threat_type = "Normal"
    threat_confidence = 0.0
    all_probs_dict = {model_state.label_mapping[str(i)]: 0.0 for i in range(5)}
    
    with torch.no_grad():
        probs = model_state.classifier.predict_proba(x_tensor)[0].cpu().numpy()
        
    for i in range(5):
        all_probs_dict[model_state.label_mapping[str(i)]] = float(probs[i])
        
    pred_class_idx = int(np.argmax(probs))
    threat_type = model_state.label_mapping[str(pred_class_idx)]
    threat_confidence = float(probs[pred_class_idx])
    
    # If autoencoder says normal but classifier says threat with high conf?
    # Usually we rely on autoencoder for detection, classifier for attribution.
    # Let's say if it's not anomalous, it's normal.
    if not is_anomalous:
        threat_type = "Normal"
        threat_confidence = all_probs_dict["Normal"]
        
    # Risk Level
    risk_level = "LOW"
    if is_anomalous:
        if threat_confidence > 0.8:
            risk_level = "CRITICAL"
        elif threat_confidence > 0.5:
            risk_level = "HIGH"
        else:
            risk_level = "MEDIUM"
            
    # Feature Importance (Basic XAI)
    # Compare raw features to a mocked normal mean, scale by absolute difference
    diffs = np.abs(raw_features - model_state.normal_mean)
    # Sort and take top 5
    top_indices = np.argsort(diffs)[::-1][:5]
    feature_importance = {}
    for idx in top_indices:
        feature_importance[model_state.feature_names[idx]] = float(diffs[idx])

    return PredictResponse(
        anomaly_score=anomaly_score,
        is_anomalous=is_anomalous,
        threat_type=threat_type,
        threat_confidence=threat_confidence,
        all_probabilities=all_probs_dict,
        risk_level=risk_level,
        feature_importance=feature_importance
    )
