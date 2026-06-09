from services.api_client import get_policy_details, get_death_record, get_claim_history_count, check_duplicate_claim
from datetime import datetime

def run(data):
    reasons = []
    decision = "Approve"
    risk_score = 0

    # ---------------- EXTRACT FIELDS ----------------
    policy_no = data.get("policy", {}).get("policy_no", "").strip()
    claim_amount = data.get("financial", {}).get("claim_amount", 0)
    
    incident = data.get("incident", {})
    cause_ui = incident.get("cause", "").lower().strip()
    
    # Extract Death Certificate ID from OCR or UI
    death_cert_id = data.get("ocr_data", {}).get("death_certificate_id", "").strip()
    if not death_cert_id:
        death_cert_id = data.get("incident", {}).get("death_certificate_id", "").strip()

    # ---------------- 1. REGISTRY POLICY CHECK ----------------
    if not policy_no:
        return "Reject", ["Policy number is required for verification."]
        
    registry_policy = get_policy_details(policy_no)
    if not registry_policy:
        return "Reject", [f"Invalid Policy Number '{policy_no}': Record not found in registry."]
        
    if registry_policy["status"].lower() != "active":
        return "Reject", [f"Policy '{policy_no}' is currently {registry_policy['status']} (Coverage suspended)."]

    # DYNAMIC DUPLICATE CLAIM CHECK
    if claim_amount > 0 and check_duplicate_claim(policy_no, claim_amount):
        return "Reject", [f"Claim Rejected: A death benefit claim for the exact same amount (${claim_amount}) already exists under Policy '{policy_no}'."]

    # DYNAMIC HISTORY CHECK
    history_count = get_claim_history_count(policy_no)
    if history_count >= 1: # Life insurance claims are typically single-event
        reasons.append(f"⚠ Critical claim flag: Policyholder already has {history_count} registered life claims in the claims ledger.")
        risk_score += 40

    sum_assured = registry_policy.get("sum_assured", 0)
    if claim_amount > sum_assured:
        return "Reject", [f"Claim amount (${claim_amount}) exceeds the policy sum assured (${sum_assured})."]

    # ---------------- 2. DEATH CERTIFICATE REGISTRY CHECK ----------------
    if not death_cert_id:
        reasons.append("⚠ Death Certificate ID missing from submission.")
        risk_score += 30
    else:
        death_record = get_death_record(death_cert_id)
        if not death_record:
            return "Reject", [f"Claim Rejected: Death Certificate ID '{death_cert_id}' is invalid or not registered in national records."]
            
        # Verify deceased name matches policyholder
        policyholder_name = registry_policy["full_name"].lower().strip()
        deceased_name = death_record["full_name"].lower().strip()
        if policyholder_name != deceased_name:
            return "Reject", [f"Claim Rejected: Deceased name '{death_record['full_name']}' does not match the policyholder '{registry_policy['full_name']}'."]

        # Calculate Policy Age at time of death
        inception_str = registry_policy["inception_date"] # YYYY-MM-DD
        death_str = death_record["date_of_death"] # YYYY-MM-DD
        
        try:
            inception_date = datetime.strptime(inception_str, "%Y-%m-%d")
            death_date = datetime.strptime(death_str, "%Y-%m-%d")
            duration_days = (death_date - inception_date).days
            policy_age_years = duration_days / 365.25
        except Exception:
            policy_age_years = 2.0  # fallback

        # ---------------- 3. CONTESTABILITY & EXCLUSIONS ----------------
        cause_of_death = death_record["cause_of_death"].lower()
        
        # Suicide Exclusion (Common industry clause: 1-year exclusion for suicide)
        if "suicide" in cause_of_death and policy_age_years < 1.0:
            return "Reject", ["Claim Rejected: Death by suicide is excluded under the first 12 months of policy inception (Suicide Exclusion Clause)."]

        # Early Contestability check (deaths within first 2 years are heavily audited)
        if policy_age_years < 2.0:
            reasons.append(f"⚠ Contestability Audit: Early death claim filed within {policy_age_years:.2f} years of policy start.")
            risk_score += 40
            
        # Compare cause of death in certificate with UI declaration
        if cause_ui and cause_ui not in cause_of_death and cause_of_death not in cause_ui:
            reasons.append(f"⚠ Cause of death mismatch: UI declared '{cause_ui}' vs Certificate '{death_record['cause_of_death']}'")
            risk_score += 25

    # ---------------- 4. FINAL SCORE AGGREGATION ----------------
    if risk_score >= 80:
        decision = "Reject"
    elif risk_score >= 40:
        decision = "Needs Review"
    else:
        decision = "Approve"

    if not reasons:
        reasons.append("All life registry and contestability checks passed.")

    return decision, reasons