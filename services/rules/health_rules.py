from services.api_client import get_policy_details, verify_doctor, verify_hospital, get_claim_history_count, check_duplicate_claim

def run(data):
    reasons = []
    decision = "Approve"
    risk_score = 0

    # ---------------- UI & DOC DATA EXTRACT ----------------
    policy_no = data.get("policyholder", {}).get("policy_no", "").strip()
    patient_name = data.get("patient", {}).get("name", "").strip()
    hospital_name = data.get("hospital", {}).get("name", "").strip()
    diagnosis = data.get("hospital", {}).get("diagnosis", "").lower()
    
    financial = data.get("financial", {})
    total_bill = financial.get("total_bill", 0)
    icu = financial.get("icu", 0)
    medicine = financial.get("medicine", 0)
    
    admission = data.get("admission", {})
    days = max(admission.get("days", 1), 1)
    admission_type = admission.get("type", "").lower()

    # ---------------- 1. REGISTRY POLICY CHECK ----------------
    if not policy_no:
        return "Reject", ["Policy number is required for verification."]
        
    registry_policy = get_policy_details(policy_no)
    if not registry_policy:
        return "Reject", [f"Invalid Policy Number '{policy_no}': Record not found in registry."]
        
    if registry_policy["status"].lower() != "active":
        return "Reject", [f"Policy '{policy_no}' is currently {registry_policy['status']} (Coverage suspended)."]

    # DYNAMIC DUPLICATE CLAIM CHECK
    if total_bill > 0 and check_duplicate_claim(policy_no, total_bill):
        return "Reject", [f"Claim Rejected: A claim for the exact same amount (${total_bill}) already exists under Policy '{policy_no}' (Potential duplicate submission)."]

    # DYNAMIC HISTORY CHECK
    history_count = get_claim_history_count(policy_no)
    if history_count >= 3:
        reasons.append(f"⚠ High claim frequency: Policyholder has {history_count} previous claims in the registry ledger.")
        risk_score += 25

    # Verify Patient Identity
    holder_name = registry_policy["full_name"].lower().strip()
    patient_name_clean = patient_name.lower().strip()
    if patient_name_clean and patient_name_clean != holder_name:
        reasons.append("⚠ Patient name does not match the primary policyholder.")
        risk_score += 30

    # ---------------- 2. HOSPITAL & DOCTOR CHECK ----------------
    if hospital_name:
        hospital_record = verify_hospital(hospital_name)
        if not hospital_record:
            reasons.append(f"⚠ Hospital '{hospital_name}' is not registered in the medical directory.")
            risk_score += 20
        else:
            if hospital_record["blacklist_flag"] == 1:
                return "Reject", [f"Claim Rejected: Hospital '{hospital_name}' is blacklisted for fraud."]
            if not hospital_record["network_flag"]:
                reasons.append("Hospital is out of network (higher co-pay applies).")
                risk_score += 10

    # Verify Doctor License (Extracted from OCR or parsed from medical reports)
    # The OCR will extract this, let's get it from the data block
    doctor_license = data.get("ocr_data", {}).get("doctor_license", "").strip()
    if doctor_license:
        doc_record = verify_doctor(doctor_license)
        if not doc_record:
            reasons.append(f"⚠ Certifying Doctor License '{doctor_license}' not found in medical council registry.")
            risk_score += 25
        elif doc_record["blacklist_flag"] == 1 or doc_record["status"].lower() == "suspended":
            return "Reject", [f"Claim Rejected: Certifying doctor ({doc_record['doctor_name']}) has a suspended/blacklisted license."]

    # ---------------- 3. MEDICAL & BILLING BASELINES ----------------
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

    # Hard triggers
    if total_bill > baseline["total"] * 3:
        return "Reject", [f"Total Bill (${total_bill}) is extremely inflated relative to baseline for {category} illness (${baseline['total']})."]

    if category == "minor" and icu > 20000:
        return "Reject", ["ICU billing charges registered for minor illness."]

    if days <= 2 and total_bill > baseline["total"] * 2:
        return "Reject", ["Short-stay hospitalization with highly inflated billing."]

    # Heuristic scoring
    expected_total = baseline["per_day"] * days
    if total_bill > expected_total * 1.5:
        reasons.append("High per-day billing charges detected.")
        risk_score += 25

    if medicine > total_bill * 0.7:
        reasons.append("Unusual medicine cost proportion (>70% of total bill).")
        risk_score += 20

    if admission_type == "planned" and category == "minor":
        reasons.append("Planned inpatient admission registered for minor illness.")
        risk_score += 15

    # ---------------- 4. FINAL SCORE AGGREGATION ----------------
    if risk_score >= 80:
        decision = "Reject"
    elif risk_score >= 40:
        decision = "Needs Review"
    else:
        decision = "Approve"

    if not reasons:
        reasons.append("All health registry and baseline checks passed.")

    return decision, reasons