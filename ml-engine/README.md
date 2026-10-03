# ML Engine

The intelligence layer of the API Attack Detection System. Contains deep learning models for anomaly detection and threat classification.

## Architecture

```
ml-engine/
├── data/
│   ├── generate_synthetic.py      # Generates 20K+ custom API traffic samples
│   ├── process_cicids.py          # Processes CICIDS 2017 academic dataset
│   ├── process_kaggle.py          # Processes Kaggle web attack payloads
│   ├── download_csic.py           # Processes CSIC 2010 HTTP dataset
│   ├── combine_datasets.py        # Merges all datasets into one
│   ├── synthetic_dataset.csv      # Generated synthetic data (committed)
│   ├── cicids_raw/                # Place CICIDS CSVs here (not committed)
│   ├── kaggle_raw/                # Place Kaggle CSVs here (not committed)
│   └── csic_raw/                  # Place CSIC files here (not committed)
├── models/
│   ├── autoencoder.py             # Deep Autoencoder (anomaly detection)
│   └── classifier.py             # Hybrid CNN+BiLSTM with Attention (classification)
├── utils/
│   ├── feature_extraction.py      # Shared 18-feature extractor
│   └── preprocess.py             # Data loading, normalization, DataLoaders
├── api/
│   └── main.py                   # FastAPI inference endpoint
├── train_autoencoder.py           # Autoencoder training script
├── train_classifier.py            # Classifier training script
├── requirements.txt
└── Dockerfile
```

## Datasets Used

| Dataset | Type | Samples | Purpose |
|---------|------|---------|---------|
| **Custom Synthetic** | Generated | 20,000 | Primary training data with e-commerce attack patterns |
| **CICIDS 2017** | Academic benchmark | ~2.8M | Cross-validation, academic credibility (network-level features) |
| **Kaggle Web Payloads** | Community curated | ~240K | Real-world SQLi/XSS payloads for payload-level training |
| **CSIC 2010** | Academic benchmark | ~36K | HTTP request-level attacks, academic credibility |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Step 1: Generate synthetic dataset (already generated, but you can regenerate)
python data/generate_synthetic.py

# Step 2 (Optional): Process standard datasets if you've downloaded them
python data/process_cicids.py     # Requires CICIDS CSVs in data/cicids_raw/
python data/process_kaggle.py     # Requires Kaggle CSVs in data/kaggle_raw/
python data/download_csic.py      # Requires CSIC files in data/csic_raw/

# Step 3: Combine all available datasets
python data/combine_datasets.py

# Step 4: Train models
python train_autoencoder.py
python train_classifier.py

# Step 5: Start inference API
uvicorn api.main:app --port 8001
```

## Models

### Deep Autoencoder (Anomaly Detection)
- Trained on **normal traffic only**
- Detects anomalies via high reconstruction error
- Architecture: 18→64→32→16→**8**→16→32→64→18

### Hybrid CNN+BiLSTM (Threat Classification)
- Classifies attacks into: Normal, SQLi, XSS, Path Traversal, Command Injection
- CNN extracts spatial patterns, BiLSTM captures sequential dependencies
- Self-attention mechanism for explainability (XAI)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/model/status` | Model loading status |
| POST | `/predict` | Classify a request and get anomaly score |
