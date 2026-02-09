import re

def extract_features_from_text(text: str):
    features = {}

    amount = re.search(r"(\d{4,6})", text)
    if amount:
        features["claim_amount"] = int(amount.group(1))

    text_lower = text.lower()

    if "accident" in text_lower:
        features["incident_type"] = "accident"
    elif "theft" in text_lower:
        features["incident_type"] = "theft"
    elif "illness" in text_lower:
        features["incident_type"] = "illness"

    return features
