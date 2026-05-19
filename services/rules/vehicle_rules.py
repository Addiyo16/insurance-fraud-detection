from services.rules.evidence import (
    add_amount_mismatch,
    final_decision,
    missing_document_facts,
    missing_facts_reason,
    normalize_vehicle_number,
    number,
    score_band,
)


def run(data):
    reasons = []
    risk_score = 0

    vehicle = data.get("vehicle", {})
    damage = data.get("damage", {})
    incident = data.get("incident", {})
    docs = data.get("documents", {})
    policy = data.get("policy", {})
    history = number(data.get("history", 0))
    document_info = data.get("document_info", {})

    idv = number(vehicle.get("idv"))
    estimated_cost = number(damage.get("estimated_cost"))
    accident_type = str(incident.get("type", "")).lower()
    vehicle_type = str(vehicle.get("type", "")).lower()
    report_delay_hours = number(incident.get("report_delay_hours"))
    policy_age_months = number(policy.get("age_months", 12))

    if idv <= 0:
        return "Needs Review", ["Vehicle IDV is missing or invalid, so coverage cannot be verified"], 55

    if estimated_cost <= 0:
        return "Needs Review", ["Repair estimate is missing or invalid"], 50

    damage_ratio = estimated_cost / idv

    required_docs = ["rc", "police", "images"]
    missing = [doc for doc in required_docs if not docs.get(doc)]
    if missing:
        return "Needs Review", [f"Missing vehicle claim evidence: {', '.join(missing)}"], 65

    missing_facts = missing_document_facts(document_info, ["vehicle_number", "idv", "estimated_cost"])
    if missing_facts:
        return "Needs Review", [missing_facts_reason("Vehicle", missing_facts)], 70

    rc_vehicle_number = document_info.get("vehicle_number")
    if normalize_vehicle_number(vehicle.get("number")) != normalize_vehicle_number(rc_vehicle_number):
        return "Reject", ["Invalid claim details: vehicle number on RC does not match the claim form"], 98

    risk_score += add_amount_mismatch(
        reasons,
        "IDV",
        idv,
        document_info.get("idv"),
        tolerance=0.03,
        risk_points=35,
    )
    risk_score += add_amount_mismatch(
        reasons,
        "repair estimate",
        estimated_cost,
        document_info.get("estimated_cost"),
        tolerance=0.08,
        risk_points=30,
    )

    doc_accident_type = str(document_info.get("accident_type", "")).lower()
    if doc_accident_type and accident_type and doc_accident_type != accident_type:
        return "Reject", [
            f"Invalid claim details: accident severity mismatch. Claim says {accident_type}, document says {doc_accident_type}"
        ], 92

    if estimated_cost > idv:
        return "Reject", ["Claimed repair cost exceeds insured declared value (IDV)"], 98

    if accident_type == "minor" and damage_ratio >= 0.75:
        reasons.append(
            "Minor accident has repair cost above 75% of IDV, close to constructive total-loss behavior"
        )
        risk_score += 75
    elif accident_type == "minor" and damage_ratio >= 0.50:
        reasons.append(
            "Minor accident has repair cost above 50% of IDV; do not auto-approve without independent surveyor validation and image-to-estimate matching"
        )
        risk_score += score_band(damage_ratio, [(0.50, 45), (0.60, 55), (0.70, 65)])
    elif accident_type == "minor" and idv < 200000 and damage_ratio >= 0.40:
        reasons.append(
            "Minor accident on a low-IDV vehicle has a high repair-to-IDV ratio, which is inconsistent with normal claim severity"
        )
        risk_score += 40
    elif accident_type == "minor" and damage_ratio >= 0.35:
        reasons.append("Minor accident repair estimate is high relative to IDV")
        risk_score += score_band(damage_ratio, [(0.35, 20), (0.45, 30)])

    if accident_type == "major" and damage_ratio < 0.08:
        reasons.append("Major accident has unusually low repair cost relative to IDV")
        risk_score += 25

    if damage_ratio >= 0.85:
        reasons.append("Repair estimate is close to total-loss level and requires salvage/assessment review")
        risk_score += 30
    elif damage_ratio >= 0.60:
        reasons.append("Repair estimate is materially high compared with IDV")
        risk_score += 10

    if report_delay_hours > 72:
        reasons.append("Accident was reported after 72 hours")
        risk_score += 25
    elif report_delay_hours > 48:
        reasons.append("Accident was reported late")
        risk_score += 10

    if policy_age_months < 1 and damage_ratio > 0.35:
        reasons.append("High-value claim occurred within the first policy month")
        risk_score += 30

    if history >= 3:
        reasons.append("Multiple previous vehicle claims are linked to this policy/customer")
        risk_score += 20

    if vehicle_type == "bike" and damage_ratio > 0.55:
        reasons.append("Two-wheeler repair estimate is unusually high relative to IDV")
        risk_score += 20

    return final_decision(
        risk_score,
        reasons,
        "Vehicle claim is within IDV, accident severity, timing, document, and history tolerances",
    )
