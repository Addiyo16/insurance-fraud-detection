def run(data):

    reasons = []
    decision = "Approve"
    risk_score = 0

    # ---------------- EXTRACT ----------------
    policy = data.get("policy", {})
    financial = data.get("financial", {})
    hospital = data.get("hospital", {})
    admission = data.get("admission", {})
    docs = data.get("documents", {})
    history = data.get("history", 0)

    total_bill = financial.get("total_bill", 0)
    icu = financial.get("icu", 0)
    medicine = financial.get("medicine", 0)

    diagnosis = hospital.get("diagnosis", "").lower()
    network = hospital.get("network", True)

    days = max(admission.get("days", 1), 1)
    admission_type = admission.get("type", "").lower()

    # ---------------- DERIVED ----------------
    per_day = total_bill / days if days > 0 else total_bill

    # =====================================================
    # 🔴 1. CONTEXT-AWARE BASELINES
    # =====================================================

    BASELINES = {
        "minor": {"per_day": 8000, "total": 50000},
        "moderate": {"per_day": 20000, "total": 200000},
        "major": {"per_day": 50000, "total": 500000}
    }

    if any(x in diagnosis for x in ["fever", "cold", "viral", "flu"]):
        category = "minor"
    elif any(x in diagnosis for x in ["infection", "pneumonia"]):
        category = "moderate"
    elif any(x in diagnosis for x in ["surgery", "operation", "fracture"]):
        category = "major"
    else:
        category = "moderate"

    baseline = BASELINES[category]

    # =====================================================
    # 🔴 2. HARD RULES
    # =====================================================

    if total_bill > baseline["total"] * 3:
        return "Reject", ["Bill exceeds expected range for diagnosis"]

    if category == "minor" and icu > 20000:
        return "Reject", ["ICU usage for minor illness"]

    if days <= 2 and total_bill > baseline["total"] * 2:
        return "Reject", ["Short stay with inflated billing"]

    if per_day > baseline["per_day"] * 3:
        return "Reject", ["Unrealistic per-day hospital charges"]

    if medicine > total_bill * 0.7:
        return "Reject", ["Unusual medicine cost proportion"]

    # =====================================================
    # 🔹 3. DOCUMENT VALIDATION
    # =====================================================

    required_docs = ["final_bill", "medical_report", "kyc"]
    missing = [d for d in required_docs if docs.get(d) is None]

    if missing:
        return "Needs Review", [f"Missing documents: {', '.join(missing)}"]

    # =====================================================
    # 🔹 4. LOW BILL ANOMALY (YOUR NEW LOGIC)
    # =====================================================

    expected_total = baseline["per_day"] * days

    if admission_type == "emergency" and days >= 1:

        if total_bill < expected_total * 0.2:
            return "Needs Review", ["Bill significantly lower than expected for treatment"]

        elif total_bill < expected_total * 0.5:
            risk_score += 15
            reasons.append("Bill lower than expected range")

    # =====================================================
    # 🔹 5. CONSISTENCY CHECKS
    # =====================================================

    if admission_type == "planned" and category == "minor":
        risk_score += 20
        reasons.append("Planned admission for minor illness")

    if icu > 0 and days <= 1:
        risk_score += 25
        reasons.append("ICU used for very short stay")

    if category == "minor" and total_bill > baseline["total"]:
        risk_score += 30
        reasons.append("Cost exceeds expected for minor illness")

    # =====================================================
    # 🔹 6. RISK SIGNALS
    # =====================================================

    if per_day > baseline["per_day"] * 1.5:
        risk_score += 25
        reasons.append("High per-day cost")

    if total_bill > baseline["total"] * 1.5:
        risk_score += 20
        reasons.append("High total bill")

    if not network:
        risk_score += 15
        reasons.append("Non-network hospital")

    if history >= 3:
        risk_score += 25
        reasons.append("Frequent claim history")

    # =====================================================
    # 🔵 7. FINAL DECISION
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