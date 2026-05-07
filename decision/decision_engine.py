def make_decision(score):
    if score >= 70:
        return "Reject"
    elif score >= 40:
        return "Needs Review"
    else:
        return "Approve"
    
def make_final_decision(score, rule_decision):
    """
    Industry-style decision:
    1. Hard rules override
    2. Then use score-based decision
    """

    # 🔴 HARD OVERRIDE
    if rule_decision == "Reject":
        return "Reject"

    # 🟡 If rules already say review → respect it
    if rule_decision == "Needs Review":
        if score < 40:
            return "Needs Review"
    
    # 🧠 fallback to score-based logic
    return make_decision(score)