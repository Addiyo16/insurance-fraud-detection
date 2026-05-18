# Insurance Fraud Detection

Streamlit application for multi-domain insurance claim screening across Health,
Vehicle, Life, and Financial claims. The system combines deterministic claim
rules, a trained fraud-risk model, and local RAG-style explanations.

## What Improved

- Local RAG explanations now cite relevant review standards from `rag/knowledge_base.py`.
- Pipeline output includes rule decision, ML score, final score, reasons, and explanation.
- Life insurance UI fields now match the rule engine.
- Document verification fields compare claim-form values against values read from uploaded evidence.
- Vehicle rules now include low-IDV/minor-accident severity checks, RC mismatch rejection, IDV checks, late reporting, early policy claims, and total-loss style review.
- Synthetic training data generation is deterministic and domain-specific.
- Model loading is path-safe from any working directory.
- Docker and Cloud Run deployment files are included.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

In each claim domain, use **Document verification values** to enter values
read from uploaded documents or OCR. The system compares those values against
the claim form and uses mismatches in the decision.

## Retrain The Model

```bash
python training/generate_dataset.py
python training/preprocess.py
python training/train.py
```

The generated data is synthetic. It is useful for demos and baseline behavior,
but a production insurer should replace or calibrate it with approved historical
claims, investigation outcomes, policy metadata, and document-verification
signals.

## Deploy On Google Cloud Run

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
gcloud run deploy insurance-fraud-detection --source . --region us-central1 --allow-unauthenticated --memory 1Gi --cpu 1 --max-instances 1
```

Cloud Run is suitable for a free-tier friendly demo because it can scale to zero.
Always configure billing alerts and check current Google Cloud Free Program
limits before production use.

## Production Notes

This project is a strong prototype, not a finished regulated decision system.
Before an insurance company relies on it, add:

- Real labeled claim data with data-governance approval.
- Human-review workflow and audit logs.
- Document OCR validation and tamper checks.
- Bias, drift, and calibration monitoring.
- Jurisdiction-specific compliance review.
