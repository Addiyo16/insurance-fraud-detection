import streamlit as st

from ml.src.predict import predict_fraud
from ml.src.eligibility_rules import check_eligibility
from ml.src.text_extraction import extract_features_from_text
from ml.src.reason_engine import generate_reasons

# Page config

st.set_page_config(page_title="Insurance Fraud Detection", layout="centered")

st.title("🛡️ General Insurance Fraud Detection System")
st.write(
    "Submit a claim using either structured details or a free-text description. "
    "The system evaluates eligibility, fraud risk, and provides explainable decisions."
)

# Input mode selector (OUTSIDE forms)

input_mode = st.radio(
    "Choose input method:",
    ["Claim Details (Structured)", "Claim Description (Text)"]
)

# MODE 1: CLAIM DESCRIPTION (TEXT) — CLEAN

if input_mode == "Claim Description (Text)":

    with st.form("text_claim_form"):
        st.subheader("📝 Claim Description")

        claim_text = st.text_area(
            "Describe the claim",
            placeholder="Example: Accident occurred last month, claimed 150000 for vehicle repair..."
        )

        extracted = extract_features_from_text(claim_text) if claim_text else {}

        if extracted:
            st.info("🔍 Extracted info (review & complete below)")
            st.json(extracted)

        insurance_type = st.selectbox("Insurance Type", ["health", "vehicle", "life", "finance"])
        policy_type = st.selectbox("Policy Type", ["basic", "premium"])
        region = st.selectbox("Region", ["north", "south", "east", "west"])

        claim_amount = st.number_input(
            "Claim Amount",
            min_value=0,
            value=extracted.get("claim_amount", 50000)
        )

        incident_type = extracted.get("incident_type", "accident")
        payment_method = st.selectbox("Payment Method", ["cash", "online", "cheque"])

        customer_age = st.number_input("Customer Age", min_value=18, value=35)
        policy_tenure_days = st.number_input("Policy Tenure (days)", min_value=1, value=180)
        num_previous_claims = st.number_input("Previous Claims", min_value=0, value=0)
        days_since_last_claim = st.number_input("Days Since Last Claim", min_value=0, value=200)
        claim_processing_days = st.number_input("Claim Processing Days", min_value=1, value=10)

        submitted = st.form_submit_button("🔍 Evaluate Claim")

# MODE 2: STRUCTURED CLAIM — CLEAN

else:

    with st.form("structured_claim_form"):
        st.subheader("📋 Claim Details")

        insurance_type = st.selectbox("Insurance Type", ["health", "vehicle", "life", "finance"])
        policy_type = st.selectbox("Policy Type", ["basic", "premium"])
        incident_type = st.selectbox(
            "Incident Type",
            ["accident", "illness", "theft", "death", "financial_loss"]
        )
        payment_method = st.selectbox("Payment Method", ["cash", "online", "cheque"])
        region = st.selectbox("Region", ["north", "south", "east", "west"])

        claim_amount = st.number_input("Claim Amount", min_value=0, value=50000)
        customer_age = st.number_input("Customer Age", min_value=18, value=35)
        policy_tenure_days = st.number_input("Policy Tenure (days)", min_value=1, value=180)
        num_previous_claims = st.number_input("Previous Claims", min_value=0, value=0)
        days_since_last_claim = st.number_input("Days Since Last Claim", min_value=0, value=200)
        claim_processing_days = st.number_input("Claim Processing Days", min_value=1, value=10)

        submitted = st.form_submit_button("🔍 Evaluate Claim")

# Decision logic (RUNS ONLY AFTER SUBMIT)

if "submitted" in locals() and submitted:

    input_data = {
        "insurance_type": insurance_type,
        "policy_type": policy_type,
        "incident_type": incident_type,
        "payment_method": payment_method,
        "region": region,
        "claim_amount": claim_amount,
        "customer_age": customer_age,
        "policy_tenure_days": policy_tenure_days,
        "num_previous_claims": num_previous_claims,
        "days_since_last_claim": days_since_last_claim,
        "claim_processing_days": claim_processing_days,
    }

    eligible, reasons = check_eligibility(input_data)

    if not eligible:
        st.error("❌ Claim Not Eligible")
        for r in reasons:
            st.write("•", r)
    else:
        prediction, probability = predict_fraud(input_data)

        st.subheader("📊 Decision Result")

        if prediction == 1:
            st.error("🚨 Fraudulent Claim Detected")
            st.write("**Action:** Investigate / Reject")

            risk_factors = generate_reasons(input_data)
            if risk_factors:
                st.write("**Risk Factors:**")
                for r in risk_factors:
                    st.write("•", r)
        else:
            st.success("✅ Claim Appears Legitimate")
            st.write("**Action:** Approve")

        st.write(f"**Fraud Probability:** `{probability:.2f}`")

st.markdown("---")
st.caption("Professional insurance fraud detection system with explainable AI.")







