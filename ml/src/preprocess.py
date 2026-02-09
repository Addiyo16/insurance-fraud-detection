from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def build_preprocessor(X):
    categorical_cols = [
        "insurance_type",
        "policy_type",
        "incident_type",
        "payment_method",
        "region",
    ]

    numerical_cols = [
        "claim_amount",
        "customer_age",
        "policy_tenure_days",
        "num_previous_claims",
        "days_since_last_claim",
        "claim_processing_days",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numerical_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
        ]
    )

    return preprocessor, categorical_cols + numerical_cols
