def run(data):

    reasons = []
    decision = "Approve"
    risk_score = 0

    vehicle = data.get("vehicle", {})
    damage = data.get("damage", {})
    incident = data.get("incident", {})
    docs = data.get("documents", {})
    policy = data.get("policy", {})
    history = data.get("history", 0)

    idv = vehicle.get("idv", 0)
    estimated_cost = damage.get("estimated_cost", 0)
    accident_type = incident.get("type", "").lower()
    location = incident.get("location", "").lower()
    vehicle_type = vehicle.get("type", "").lower()

    # =====================================================
    # 🔹 1. BASIC VALIDATION
    # =====================================================
    if idv <= 0:
        return "Needs Review", ["Invalid or missing vehicle IDV"]

    damage_ratio = estimated_cost / idv

    # =====================================================
    # 🔹 2. LOCATION CHECK
    # =====================================================
    if location:
        if not any(ind in location for ind in ["india", "maharashtra", "delhi", "mumbai", "pune", "bangalore"]):
            reasons.append("⚠ Accident location outside expected region (needs verification)")
            risk_score += 10

    # =====================================================
    # 🔹 3. HIGH CLAIM FLAG (NO PENALTY)
    # =====================================================
    if damage_ratio >= 0.8:
        reasons.append("⚠ High claim amount (close to insured value) – recommended manual review")

    # =====================================================
    # 🔹 4. HARD RULE
    # =====================================================
    if estimated_cost > idv:
        return "Reject", ["Claim exceeds insured vehicle value (IDV)"]

    # =====================================================
    # 🔹 5. CLAIM vs IDV
    # =====================================================
    if damage_ratio > 0.8:
        reasons.append("High claim relative to IDV")
        risk_score += 25

    elif damage_ratio > 0.5:
        reasons.append("Moderately high damage")
        risk_score += 10

    # =====================================================
    # 🔹 STRONG CONSISTENCY RULES
    # =====================================================

    # 🚨 Minor accident but very high claim → Reject
    if accident_type == "minor" and damage_ratio >= 0.9:
        return "Reject", ["High claim inconsistent with minor accident"]

    # ⚠ Major accident high claim → Needs Review
    if accident_type == "major" and damage_ratio >= 0.8:
        reasons.append("High claim in major accident (requires review)")
        decision = "Needs Review"

    # =====================================================
    # 🔹 6. ACCIDENT CONSISTENCY
    # =====================================================

    # Minor + low claim → normal
    if accident_type == "minor" and damage_ratio < 0.2:
        reasons.append("Low damage for minor accident (normal case)")

    # Minor + high claim
    elif accident_type == "minor":

    # 🔹 Low IDV vehicles → stricter rules
        if idv < 200000 and damage_ratio >= 0.4:
            reasons.append("High claim for minor accident (low-value vehicle)")
            risk_score += 40

    # 🔹 Normal vehicles
    elif damage_ratio > 0.5:
        reasons.append("Damage too high for minor accident")
        risk_score += 35

    # Major + very low claim
    elif accident_type == "major" and damage_ratio < 0.05:
        reasons.append("Very low claim for major accident (inconsistent)")
        risk_score += 20

    elif accident_type == "major" and damage_ratio < 0.1:
        reasons.append("Low claim for major accident")
        risk_score += 10

    # =====================================================
    # 🔹 7. DOCUMENT VALIDATION
    # =====================================================
    required_docs = ["rc", "police", "images"]
    missing = [d for d in required_docs if not docs.get(d)]

    if missing:
        reasons.append(f"Missing documents: {', '.join(missing)}")
        risk_score += 15

    # 🔹 Document strength
    doc_count = sum([
        1 if docs.get("rc") else 0,
        1 if docs.get("police") else 0,
        1 if docs.get("images") else 0
    ])

    if doc_count < 2:
        reasons.append("Insufficient supporting documents")
        risk_score += 15

    # =====================================================
    # 🔹 8. TIMING CHECK (NEW)
    # =====================================================
    delay = incident.get("report_delay_hours", 0)

    if delay > 72:
        reasons.append("Very late reporting")
        risk_score += 25
    elif delay > 48:
        reasons.append("Late reporting")
        risk_score += 10

    # =====================================================
    # 🔹 9. POLICY AGE (NEW)
    # =====================================================
    policy_age = policy.get("age_months", 12)

    if policy_age < 1 and damage_ratio > 0.5:
        reasons.append("Early claim after policy start with high damage")
        risk_score += 25

    # =====================================================
    # 🔹 10. CLAIM HISTORY (NEW)
    # =====================================================
    if history >= 3:
        reasons.append("Multiple previous claims")
        risk_score += 20

    # =====================================================
    # 🔹 11. VEHICLE TYPE LOGIC (NEW)
    # =====================================================
    if vehicle_type == "bike" and damage_ratio > 0.6:
        reasons.append("High damage for bike")
        risk_score += 20

    if vehicle_type == "truck" and accident_type == "major" and damage_ratio < 0.1:
        reasons.append("Low damage for major accident (truck)")
        risk_score += 15

    # =====================================================
    # 🔹 12. EXTREME CASE
    # =====================================================
    if estimated_cost > 1_000_000:
        reasons.append("Very high repair cost (manual verification)")
        risk_score += 15

    # =====================================================
    # 🔹 FINAL DECISION (PROTECTED)
    # =====================================================
    if decision != "Needs Review":
        if risk_score >= 80:
            decision = "Reject"
        elif risk_score >= 40:
            decision = "Needs Review"
        else:
            decision = "Approve"

    # Force review for strong inconsistency
    if "Very low claim for major accident (inconsistent)" in reasons:
        decision = "Needs Review"

    if not reasons:
        reasons.append("All vehicle checks passed")

    return decision, reasons