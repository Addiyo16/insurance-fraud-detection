import pandas as pd


FEATURE_COLUMNS = [
    "amount",
    "history",
    "high_amount",
    "frequent_claims",
    "domain_health",
    "domain_vehicle",
    "domain_life",
    "domain_financial",
    "non_network",
    "high_damage",
    "early_policy",
    "income_mismatch",
]


def preprocess():
    print("Loading raw dataset...")
    df = pd.read_csv("data/raw/claims.csv")

    df["high_amount"] = (df["amount"] > 100000).astype(int)
    df["frequent_claims"] = (df["history"] > 3).astype(int)

    df["domain_health"] = (df["domain"] == "Health").astype(int)
    df["domain_vehicle"] = (df["domain"] == "Vehicle").astype(int)
    df["domain_life"] = (df["domain"] == "Life").astype(int)
    df["domain_financial"] = (df["domain"] == "Financial").astype(int)

    df["non_network"] = (df["hospital_network"] == 0).astype(int)
    df["high_damage"] = (df["damage_cost"] > 50000).astype(int)
    df["early_policy"] = (df["policy_duration"] < 1).astype(int)
    df["income_mismatch"] = (df["loan_amount"] > df["income"] * 5).astype(int)

    final_df = df[FEATURE_COLUMNS + ["fraud"]]
    final_df.to_csv("data/processed/features.csv", index=False)

    print("Preprocessing complete.")
    print("Final shape:", final_df.shape)


if __name__ == "__main__":
    preprocess()
