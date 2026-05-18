from services.rules.evidence import add_amount_mismatch, add_text_mismatch, final_decision, number


DIAGNOSIS_BASELINES = {
    "minor": {"per_day": 8000, "total": 50000},
    "moderate": {"per_day": 20000, "total": 200000},
    "major": {"per_day": 50000, "total": 500000},
}


def _diagnosis_category(diagnosis):
    diagnosis = str(diagnosis or "").lower()
    if any(term in diagnosis for term in ["fever", "cold", "viral", "flu"]):
        return "minor"
    if any(term in diagnosis for term in ["infection", "pneumonia", "dengue", "typhoid"]):
        return "moderate"
    if any(term in diagnosis for term in ["surgery", "operation", "fracture", "cardiac", "cancer"]):
        return "major"
    return "moderate"


def run(data):
    reasons = []
    risk_score = 0

    financial = data.get("financial", {})
    hospital = data.get("hospital", {})
    admission = data.get("admission", {})
    docs = data.get("documents", {})
    document_info = data.get("document_info", {})
    history = number(data.get("history", 0))

    total_bill = number(financial.get("total_bill"))
    icu = number(financial.get("icu"))
    medicine = number(financial.get("medicine"))
    diagnosis = hospital.get("diagnosis", "")
    network = bool(hospital.get("network", True))
    days = max(number(admission.get("days"), 1), 1)
    admission_type = str(admission.get("type", "")).lower()

    if total_bill <= 0:
        return "Needs Review", ["Final bill amount is missing or invalid"], 50

    required_docs = ["final_bill", "medical_report", "kyc"]
    missing = [doc for doc in required_docs if docs.get(doc) is None]
    if missing:
        return "Needs Review", [f"Missing mandatory health claim documents: {', '.join(missing)}"], 55

    risk_score += add_text_mismatch(
        reasons,
        "Diagnosis",
        diagnosis,
        document_info.get("diagnosis"),
        risk_points=35,
    )
    risk_score += add_amount_mismatch(
        reasons,
        "final bill",
        total_bill,
        document_info.get("total_bill"),
        tolerance=0.03,
        risk_points=35,
    )
    risk_score += add_amount_mismatch(
        reasons,
        "hospitalization days",
        days,
        document_info.get("days"),
        tolerance=0.0,
        risk_points=25,
    )

    category = _diagnosis_category(diagnosis)
    baseline = DIAGNOSIS_BASELINES[category]
    per_day = total_bill / days

    if total_bill > baseline["total"] * 3:
        return "Reject", ["Final bill is far above the expected range for the stated diagnosis"], 95
    if category == "minor" and icu > 20000:
        return "Reject", ["ICU charges are inconsistent with a minor diagnosis"], 92
    if days <= 2 and total_bill > baseline["total"] * 2:
        return "Reject", ["Short hospital stay has an inflated final bill"], 90
    if per_day > baseline["per_day"] * 3:
        return "Reject", ["Per-day hospital charge is far above the expected treatment range"], 92
    if total_bill > 0 and medicine > total_bill * 0.7:
        return "Reject", ["Medicine charges exceed 70% of the total bill"], 90

    expected_total = baseline["per_day"] * days
    if admission_type == "emergency" and total_bill < expected_total * 0.2:
        reasons.append("Emergency admission bill is materially lower than expected and may indicate wrong claim details")
        risk_score += 25
    elif total_bill < expected_total * 0.5:
        reasons.append("Bill is lower than expected for diagnosis and stay length")
        risk_score += 10

    if admission_type == "planned" and category == "minor":
        reasons.append("Planned hospitalization for minor diagnosis requires medical necessity review")
        risk_score += 20
    if icu > 0 and days <= 1:
        reasons.append("ICU charge appears in a one-day admission")
        risk_score += 25
    if per_day > baseline["per_day"] * 1.5:
        reasons.append("High per-day hospital cost for the diagnosis category")
        risk_score += 30
    if total_bill > baseline["total"] * 1.5:
        reasons.append("Total bill is high for the diagnosis category")
        risk_score += 20
    if not network:
        reasons.append("Hospital is outside the insurer network")
        risk_score += 15
    if history >= 3:
        reasons.append("Frequent previous health claims linked to the customer")
        risk_score += 25

    return final_decision(
        risk_score,
        reasons,
        "Health claim passed document completeness, diagnosis, billing, network, and history checks",
    )
