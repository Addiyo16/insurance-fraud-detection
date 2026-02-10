import streamlit as st
import requests

# CONFIG

st.set_page_config(
    page_title="Insurance Fraud Detection",
    layout="centered"
)

API_URL = "https://insurance-fraud-detection-2-f459.onrender.com/predict"

# UI HEADER

st.title("🛡️ Insurance Fraud Detection System")
st.write(
    "Submit an insurance claim. The system checks eligibility, "
    "detects fraud risk, and provides explainable decisions."
)

# INPUT MODE

input_mode = st.radio(
    "Choose input method:",
    ["Claim Details (Structured)", "Claim Description (Text)"]
)

# FORM INPUTS

submitted = False

if input_mode == "Claim Description (Text)":

    with st.form("text_claim_form"):
        st.subheader("📝 Claim Description")

        claim_text = st.text_area(
            "Describe the claim",
            placeholder="Example: Accident occurred last month, claimed 150000 for vehicle repair..."
        )

        insurance_type = st.selectbox(
            "Insurance Type", ["health", "vehicle", "life", "finance"]
        )
        policy_type = st.selectbox(
            "Policy Type", ["basic", "premium"]
        )
        incident_type = st.selectbox(
            "Incident Type",
            ["accident", "illness", "theft", "death", "financial_loss"]
        )
        payment_method = st.selectbox(
            "Payment Method", ["cash", "online", "cheque"]
        )
        region = st.selectbox(
            "Region", ["north", "south", "east", "west"]
        )

        claim_amount = st.number_input(
            "Claim Amount", min_value=0, value=50000
        )
        customer_age = st.number_input(
            "Customer Age", min_value=18, value=35
        )
        policy_tenure_days = st.number_input(
            "Policy Tenure (days)", min_value=1, value=180
        )
        num_previous_claims = st.number_input(
            "Previous Claims", min_value=0, value=0
        )
        days_since_last_claim = st.number_input(
            "Days Since Last Claim", min_value=0, value=200
        )
        claim_processing_days = st.number_input(
            "Claim Processing Days", min_value=1, value=10
        )

        submitted = st.form_submit_button("🔍 Evaluate Claim")

else:

    with st.form("structured_claim_form"):
        st.subheader("📋 Claim Details")

        insurance_type = st.selectbox(
            "Insurance Type", ["health", "vehicle", "life", "finance"]
        )
        policy_type = st.selectbox(
            "Policy Type", ["basic", "premium"]
        )
        incident_type = st.selectbox(
            "Incident Type",
            ["accident", "illness", "theft", "death", "financial_loss"]
        )
        payment_method = st.selectbox(
            "Payment Method", ["cash", "online", "cheque"]
        )
        region = st.selectbox(
            "Region", ["north", "south", "east", "west"]
        )

        claim_amount = st.number_input(
            "Claim Amount", min_value=0, value=50000
        )
        customer_age = st.number_input(
            "Customer Age", min_value=18, value=35
        )
        policy_tenure_days = st.number_input(
            "Policy Tenure (days)", min_value=1, value=180
        )
        num_previous_claims = st.number_input(
            "Previous Claims", min_value=0, value=0
        )
        days_since_last_claim = st.number_input(
            "Days Since Last Claim", min_value=0, value=200
        )
        claim_processing_days = st.number_input(
            "Claim Processing Days", min_value=1, value=10
        )

        submitted = st.form_submit_button("🔍 Evaluate Claim")

# API CALL & RESULT

if submitted:

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

    try:
        with st.spinner("Analyzing claim..."):
            response = requests.post(
                API_URL,
                json=input_data,
                timeout=30
            )

        result = response.json()

        st.subheader("📊 Decision Result")

        if not result["eligible"]:
            st.error("❌ Claim Not Eligible")
            for r in result["reasons"]:
                st.write("•", r)

        else:
            if result["fraud"]:
                st.error("🚨 Fraudulent Claim Detected")
                st.write("**Action:** Investigate / Reject")
            else:
                st.success("✅ Claim Appears Legitimate")
                st.write("**Action:** Approve")

            st.write(f"**Fraud Probability:** `{result['probability']}`")

            if result["reasons"]:
                st.write("**Risk Factors:**")
                for r in result["reasons"]:
                    st.write("•", r)

    except Exception as e:
        st.error("⚠️ Backend is not responding. Please try again in a moment.")
        st.caption(str(e))

st.markdown("---")
st.caption("End-to-end insurance fraud detection system using Streamlit + FastAPI + ML")








