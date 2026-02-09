import joblib
import pandas as pd

MODEL_PATH = "ml/artifacts/best_fraud_pipeline.pkl"
pipeline = joblib.load(MODEL_PATH)

def predict_fraud(data):
    df = pd.DataFrame([data])
    prediction = pipeline.predict(df)[0]
    probability = pipeline.predict_proba(df)[0][1]
    return prediction, probability

