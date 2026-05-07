def run(data):

    reasons = []
    decision = "Approve"
    risk_score = 0

    policy = data.get("policy", {})
    incident = data.get("incident", {})
    docs = data.get("documents", {})
    history = data.get("history", 0)

    claim_amount = data.get("financial", {}).get("claim_amount", 0)
    sum_assured = policy.get("sum_assured", 0)
    policy_age = policy.get("age_years", 0)

    cause = incident.get("cause", "").lower()  # accident / illness / natural
    hospitalized = incident.get("hospitalized", False)

    # =====================================================
    # 🔹 1. POLICY VALIDATION (HARD RULE)
    # =====================================================
    if not policy.get("active", True):
        return "Reject", ["Policy inactive"]

    if sum_assured <= 0:
        return "Needs Review", ["Invalid policy details"]

    if claim_amount > sum_assured:
        return "Reject", ["Claim exceeds sum assured"]

    # =====================================================
    # 🔹 2. DOCUMENT VALIDATION (VERY STRICT)
    # =====================================================
    required_docs = ["death_certificate"]

    missing = [d for d in required_docs if not docs.get(d)]
    if missing:
        return "Needs Review", [f"Missing mandatory document: {', '.join(missing)}"]

    # Cause-specific docs
    if cause == "illness" and not docs.get("medical_report"):
        return "Needs Review", ["Medical report required for illness claim"]

    if cause == "accident" and not docs.get("police_report"):
        reasons.append("Police report missing for accident")
        risk_score += 25

    # =====================================================
    # 🔹 3. EARLY CLAIM CHECK (CRITICAL)
    # =====================================================
    if policy_age < 2:
        reasons.append("Early claim (within 2 years)")
        risk_score += 30

    if policy_age < 1:
        reasons.append("Very early claim")
        risk_score += 20

    # =====================================================
    # 🔹 4. CAUSE CONSISTENCY
    # =====================================================
    if cause == "accident" and not hospitalized:
        reasons.append("No hospitalization record for accident")
        risk_score += 20

    if cause == "natural" and docs.get("police_report"):
        reasons.append("Unusual: police report for natural death")
        risk_score += 15

    # =====================================================
    # 🔹 5. CLAIM AMOUNT LOGIC (REAL WORLD)
    # =====================================================
    claim_ratio = claim_amount / sum_assured if sum_assured > 0 else 0

    # Full claim is NORMAL in life insurance
    if claim_ratio >= 0.95:
        reasons.append("Full sum assured claim (normal)")

    # Partial claim
    elif claim_ratio < 0.3:
        reasons.append("Partial claim (valid scenario)")

    # =====================================================
    # 🔹 6. HISTORY CHECK
    # =====================================================
    if history >= 2:
        reasons.append("Multiple previous claims linked to policy/family")
        risk_score += 25

    # =====================================================
    # 🔹 7. STRONG FRAUD SIGNALS
    # =====================================================
    if policy_age < 1 and claim_ratio >= 0.9:
        reasons.append("Very early high-value claim")
        risk_score += 40

    # Missing medical consistency
    if cause == "illness" and not hospitalized:
        reasons.append("No hospitalization for illness claim")
        risk_score += 15

    # =====================================================
    # 🔹 FINAL DECISION (SAFE LOGIC)
    # =====================================================
    if risk_score >= 80:
        decision = "Reject"

    elif risk_score >= 40:
        decision = "Needs Review"

    else:
        decision = "Approve"

    if not reasons:
        reasons.append("All checks passed")

    return decision, reasons