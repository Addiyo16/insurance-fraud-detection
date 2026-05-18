from services.rules.evidence import add_amount_mismatch, add_text_mismatch, final_decision, number


def run(data):
    reasons = []
    risk_score = 0

    policy = data.get("policy", {})
    incident = data.get("incident", {})
    docs = data.get("documents", {})
    document_info = data.get("document_info", {})
    history = number(data.get("history", 0))

    claim_amount = number(data.get("financial", {}).get("claim_amount"))
    sum_assured = number(policy.get("sum_assured"))
    policy_age = number(policy.get("age_years"))
    cause = str(incident.get("cause", "")).lower()
    hospitalized = bool(incident.get("hospitalized", False))

    if not policy.get("active", True):
        return "Reject", ["Policy is inactive on the claim event date"], 98
    if sum_assured <= 0:
        return "Needs Review", ["Sum assured is missing or invalid"], 55
    if claim_amount <= 0:
        return "Needs Review", ["Claim amount is missing or invalid"], 50
    if claim_amount > sum_assured:
        return "Reject", ["Claim amount exceeds sum assured"], 98

    if not docs.get("death_certificate"):
        return "Needs Review", ["Death certificate is mandatory for life claim review"], 60

    risk_score += add_text_mismatch(
        reasons,
        "Cause of death",
        cause,
        document_info.get("cause"),
        risk_points=35,
    )
    risk_score += add_amount_mismatch(
        reasons,
        "sum assured",
        sum_assured,
        document_info.get("sum_assured"),
        tolerance=0.02,
        risk_points=30,
    )

    if cause == "illness" and not docs.get("medical_report"):
        return "Needs Review", ["Medical report is required for illness-related life claim"], 55
    if cause == "accident" and not docs.get("police_report"):
        reasons.append("Police/FIR report is missing for accidental death")
        risk_score += 30

    if policy_age < 1:
        reasons.append("Claim occurred within first policy year")
        risk_score += 35
    elif policy_age < 2:
        reasons.append("Claim occurred within early policy period")
        risk_score += 25

    claim_ratio = claim_amount / sum_assured
    if policy_age < 1 and claim_ratio >= 0.9:
        reasons.append("Very early claim requests almost the full sum assured")
        risk_score += 45
    elif claim_ratio >= 0.95:
        reasons.append("Full sum assured claim is expected in life insurance and was treated as normal")

    if cause == "accident" and not hospitalized:
        reasons.append("Accident claim has no matching hospitalization record")
        risk_score += 20
    if cause == "natural" and docs.get("police_report"):
        reasons.append("Police report is unusual for natural death and should be checked")
        risk_score += 10
    if cause == "illness" and not hospitalized:
        reasons.append("Illness death has no hospitalization or treatment record")
        risk_score += 20
    if history >= 2:
        reasons.append("Multiple prior related claims are linked to policy/customer/family")
        risk_score += 25

    return final_decision(
        risk_score,
        reasons,
        "Life claim passed policy status, sum assured, document, cause-of-death, timing, and history checks",
    )
