def generate_indicators(domain, data):

    indicators = {}

    try:
        if domain == "Health":
            indicators["high_cost"] = data["financial"]["total_bill"] > 100000
            indicators["non_network"] = not data["hospital"].get("network", True)

        elif domain == "Vehicle":
            indicators["high_damage"] = data["damage"]["estimated_cost"] > 50000
            indicators["no_police_report"] = not data["documents"].get("police_report", True)

        elif domain == "Life":
            indicators["early_claim"] = data["policy"]["duration"] < 1
            cause = data["incident"].get("cause", "")
            indicators["unknown_cause"] = "unknown" in cause.lower()

        elif domain == "Financial":
            income = data["financial"].get("income", 0)
            loan = data["financial"].get("loan_amount", 0)

            indicators["income_mismatch"] = loan > income * 5 if income > 0 else False

    except Exception as e:
        print("Indicator error:", e)

    return indicators