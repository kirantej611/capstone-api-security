# ML Engine v2.0 — API Attack Detection

Production-grade ensemble ML engine for real-time API threat detection and classification.

## Architecture

```
HTTP Request → Feature Extraction (42 features)
                    ↓
              ┌─────┴──────┐
              │   Scaler    │  (RobustScaler)
              └─────┬──────┘
                    ↓
        ┌───────────┼───────────┐
        ↓                       ↓
┌───────────────┐    ┌──────────────────┐
│      VAE      │    │  Deep Residual   │
│ (Anomaly Det) │    │  MLP Classifier  │
│  Recon + KL   │    │  (Focal Loss)    │
└───────┬───────┘    └────────┬─────────┘
        ↓                     ↓
        └─────────┬───────────┘
                  ↓
      ┌───────────────────────┐
      │  Ensemble Decision    │
      │  Engine + Calibration │
      └───────────┬───────────┘
                  ↓
          Threat Assessment
```

## Components

| Component | File | Description |
|-----------|------|-------------|
| Feature Extraction | `utils/feature_extraction.py` | 42 numeric features covering SQL, XSS, path traversal, command injection, SSRF, encoding patterns, entropy analysis |
| VAE | `models/autoencoder.py` | Variational Autoencoder with skip connections, residual blocks, multi-scale reconstruction |
| Classifier | `models/classifier.py` | Deep Residual MLP with multi-head feature-group attention, Focal Loss |
| Ensemble | `models/ensemble.py` | Weighted decision engine with temperature calibration, per-class thresholds |
| API | `api/main.py` | FastAPI server with `/predict`, `/predict/batch`, `/health`, `/model/status` |

## Attack Classes (6)

| Label | Class | Description |
|-------|-------|-------------|
| 0 | Normal | Legitimate API traffic |
| 1 | SQLi | SQL Injection (obvious + evasion variants) |
| 2 | XSS | Cross-Site Scripting (DOM, stored, reflected) |
| 3 | PathTraversal | Directory traversal / LFI |
| 4 | CommandInjection | OS command injection |
| 5 | SSRF | Server-Side Request Forgery |

## Training Pipeline

```bash
# 1. Generate training data (100K samples)
python data/generate_synthetic_v3.py

# 2. Train the VAE (anomaly detection)
python train_autoencoder.py

# 3. Train the classifier (threat classification)
python train_classifier.py

# 4. Start the API server
uvicorn api.main:app --host 0.0.0.0 --port 8001
```

## Key Improvements (v1 → v2)

- **Features**: 18 → 42 (double-encoding, SSRF, template injection, event handlers, etc.)
- **Anomaly Detection**: Simple AE → VAE with KL annealing, skip connections, multi-scale loss
- **Classification**: CNN+BiLSTM → Deep Residual MLP with feature-group attention
- **Loss**: CrossEntropy → Focal Loss (γ=2.0) for class imbalance
- **Data**: 30K → 100K samples, 50+ templates per attack class, SSRF class
- **Augmentation**: None → Mixup (α=0.2)
- **XAI**: Mocked zeros → perturbation-based feature importance
- **Calibration**: None → temperature scaling on validation set
- **Thresholds**: Single global → per-class adaptive thresholds
- **Inference**: Single model → ensemble (VAE × Classifier) with composite scoring
