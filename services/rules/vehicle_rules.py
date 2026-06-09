from services.api_client import get_policy_details, verify_vehicle, get_police_report, get_claim_history_count, check_duplicate_claim

def run(data):
    reasons = []
    decision = "Approve"
    risk_score = 0

    # ---------------- EXTRACT FIELDS ----------------
    policy_no = data.get("policy", {}).get("policy_no", "").strip()
    
    vehicle = data.get("vehicle", {})
    plate = vehicle.get("number", "").strip()
    idv = vehicle.get("idv", 0)
    vehicle_type = vehicle.get("type", "").lower()
    
    damage = data.get("damage", {})
    estimated_cost = damage.get("estimated_cost", 0)
    
    incident = data.get("incident", {})
    accident_type = incident.get("type", "").lower()
    location = incident.get("location", "").lower()

    # ---------------- 1. REGISTRY POLICY CHECK ----------------
    if not policy_no:
        return "Reject", ["Policy number is required for verification."]
        
    registry_policy = get_policy_details(policy_no)
    if not registry_policy:
        return "Reject", [f"Invalid Policy Number '{policy_no}': Record not found in registry."]
        
    if registry_policy["status"].lower() != "active":
        return "Reject", [f"Policy '{policy_no}' is currently {registry_policy['status']}."]

    # DYNAMIC DUPLICATE CLAIM CHECK
    if estimated_cost > 0 and check_duplicate_claim(policy_no, estimated_cost):
        return "Reject", [f"Claim Rejected: A vehicle claim for the exact same amount (${estimated_cost}) already exists under Policy '{policy_no}'."]

    # DYNAMIC HISTORY CHECK
    history_count = get_claim_history_count(policy_no)
    if history_count >= 3:
        reasons.append(f"⚠ High claim frequency: Policyholder has {history_count} previous vehicle claims logged in the database ledger.")
        risk_score += 20

    # ---------------- 2. VEHICLE REGISTRATION CHECK ----------------
    if not plate:
        return "Reject", ["License plate number is required."]
        
    vehicle_record = verify_vehicle(plate)
    if not vehicle_record:
        return "Reject", [f"Vehicle license plate '{plate}' is not registered in the motor vehicle database."]
        
    if vehicle_record["registration_status"].lower() == "stolen":
        return "Reject", [f"Claim Rejected: Vehicle '{plate}' is officially flagged as STOLEN in the registry."]

    # Verify ownership
    policyholder_name = registry_policy["full_name"].lower().strip()
    owner_name = vehicle_record["registered_owner_name"].lower().strip()
    if policyholder_name != owner_name:
        reasons.append(f"⚠ Registered owner '{vehicle_record['registered_owner_name']}' mismatch with policyholder.")
        risk_score += 35

    # ---------------- 3. POLICE REPORT CHECK ----------------
    police_record = get_police_report(plate)
    if not police_record:
        reasons.append("⚠ No official police accident report found in traffic logs.")
        risk_score += 25
    else:
        # Cross check location
        report_location = police_record["incident_location"].lower()
        if location and location not in report_location:
            reasons.append(f"⚠ Location discrepancy: UI location '{location}' vs Police Report location '{report_location}'")
            risk_score += 20
            
        # Cross check severity
        report_severity = police_record["severity"].lower()
        if accident_type == "minor" and report_severity == "major":
            reasons.append("Accident severity reported as minor, but police log indicates major collision.")
            risk_score += 15

    # ---------------- 4. COST & VALUE CHECKS ----------------
    if idv <= 0:
        return "Needs Review", ["Invalid or missing vehicle IDV."]

    damage_ratio = estimated_cost / idv

    if estimated_cost > idv:
        return "Reject", [f"Estimated repair cost (${estimated_cost}) exceeds the total Insured Declared Value (${idv}). Total loss rules apply."]

    if damage_ratio >= 0.8:
        reasons.append("High claim amount (near total loss threshold).")
        risk_score += 20

    if accident_type == "minor" and damage_ratio >= 0.6:
        return "Reject", ["Inconsistent: High damage cost claimed for minor accident severity."]

    if vehicle_type == "bike" and damage_ratio > 0.7:
        reasons.append("High damage percentage for a two-wheeler claim.")
        risk_score += 15

    # ---------------- 5. FINAL SCORE AGGREGATION ----------------
    if risk_score >= 80:
        decision = "Reject"
    elif risk_score >= 40:
        decision = "Needs Review"
    else:
        decision = "Approve"

    if not reasons:
        reasons.append("All vehicle registry and damage consistency checks passed.")

    return decision, reasons