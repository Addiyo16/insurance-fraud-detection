import pandas as pd

def build_features(df):
    df = df.copy()

    # Basic features (expand later)
    df["amount"] = df["amount"]
    df["history"] = df["history"]

    # Derived features
    df["high_amount"] = (df["amount"] > 100000).astype(int)
    df["frequent_claims"] = (df["history"] > 3).astype(int)

    return df[["amount", "history", "high_amount", "frequent_claims"]]