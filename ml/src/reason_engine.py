def generate_reasons(data):
    reasons = []

    if data["claim_amount"] > 150000:
        reasons.append("High claim amount")

    if data["policy_tenure_days"] < 60:
        reasons.append("Very short policy tenure")

    if data["num_previous_claims"] > 3:
        reasons.append("Multiple previous claims")

    return reasons
