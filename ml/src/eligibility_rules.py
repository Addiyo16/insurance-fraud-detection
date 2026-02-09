def check_eligibility(data):
    reasons = []

    if data["policy_tenure_days"] < 30:
        reasons.append("Policy waiting period not completed")

    if data["claim_amount"] < 5000:
        reasons.append("Claim amount below minimum threshold")

    if data["policy_type"] == "basic" and data["incident_type"] == "minor":
        reasons.append("Minor incidents not covered under basic policy")

    return (len(reasons) == 0), reasons
