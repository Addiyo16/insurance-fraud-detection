def generate_explanation(domain, fraud_score, reasons):

    try:
        reason_text = "\n- ".join(reasons) if reasons else "No major rule violations"

        explanation = f"""
📌 Domain: {domain}

⚠ Fraud Risk Score: {fraud_score}%

🧾 Key Reasons:
- {reason_text}

🧠 Decision Logic:
- Based on rule engine + machine learning model
- Higher score indicates higher fraud probability
"""

        return explanation.strip()

    except Exception as e:
        return f"Explanation error: {str(e)}"