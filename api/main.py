import sqlite3
import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any

app = FastAPI(
    title="ShieldAI Registry API Service",
    description="REST API service representing central government & corporate databases for insurance validation",
    version="1.0.0"
)

# Resolve DB directory relative to this file
API_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(API_DIR)
DB_DIR = os.path.join(ROOT_DIR, "data")

DB_PATHS = {
    "insurance": os.path.join(DB_DIR, "insurance_company.db"),
    "medical": os.path.join(DB_DIR, "medical_registry.db"),
    "motor": os.path.join(DB_DIR, "motor_registry.db"),
    "death": os.path.join(DB_DIR, "death_registry.db"),
    "credit": os.path.join(DB_DIR, "credit_registry.db")
}

def _get_conn(db_key: str):
    conn = sqlite3.connect(DB_PATHS[db_key])
    conn.row_factory = sqlite3.Row
    return conn

# --- REQUEST BODY MODELS ---
class ClaimLogRequest(BaseModel):
    claim_id: str
    policy_number: str
    claim_amount: float
    status: str

class OnboardPolicyholderRequest(BaseModel):
    kyc_id: str
    full_name: str
    age: int
    gender: str
    credit_score: int
    email: str
    policy_number: str
    domain: str
    sum_assured: float
    tenure_months: int = 12

class OnboardVehicleRequest(BaseModel):
    license_plate: str
    registered_owner_name: str
    vehicle_model: str
    engine_number: str
    chassis_number: str
    registration_status: str

class OnboardLoanRequest(BaseModel):
    loan_id: str
    policy_number: str
    lender_name: str
    loan_type: str
    loan_amount: float
    tenure_months: int
    emi_amount: float

# ==========================================================
# 🛡️ 1. INSURANCE COMPANY ENDPOINTS
# ==========================================================

@app.get("/api/policy/{policy_number}", response_model=Optional[Dict[str, Any]])
def get_policy_details(policy_number: str):
    try:
        conn = _get_conn("insurance")
        cursor = conn.cursor()
        query = """
        SELECT p.policy_number, p.domain, p.status, p.sum_assured, p.inception_date, p.tenure_months,
               ph.full_name, ph.age, ph.gender, ph.credit_score, ph.email
        FROM policies p
        JOIN policyholders ph ON p.kyc_id = ph.kyc_id
        WHERE p.policy_number = ?
        """
        cursor.execute(query, (policy_number,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/insurance/duplicate_claim", response_model=bool)
def check_duplicate_claim(
    policy_number: str = Query(..., description="The policy number"),
    claim_amount: float = Query(..., description="The claim amount")
):
    try:
        conn = _get_conn("insurance")
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM claims_log WHERE policy_number = ? AND claim_amount = ?"
        cursor.execute(query, (policy_number, claim_amount))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/insurance/claim_history_count/{policy_number}", response_model=int)
def get_claim_history_count(policy_number: str):
    try:
        conn = _get_conn("insurance")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM claims_log WHERE policy_number = ?", (policy_number,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/insurance/log_claim", response_model=bool)
def log_claim(request: ClaimLogRequest):
    try:
        conn = _get_conn("insurance")
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO claims_log (claim_id, policy_number, claim_date, claim_amount, status)
        VALUES (?, ?, date('now'), ?, ?)
        """, (request.claim_id, request.policy_number, request.claim_amount, request.status))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/insurance/onboard", response_model=bool)
def onboard_policyholder(request: OnboardPolicyholderRequest):
    try:
        conn = _get_conn("insurance")
        cursor = conn.cursor()
        # Insert policyholder
        cursor.execute("""
        INSERT INTO policyholders (kyc_id, full_name, age, gender, credit_score, email)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (request.kyc_id, request.full_name, request.age, request.gender, request.credit_score, request.email))
        
        # Insert policy
        cursor.execute("""
        INSERT INTO policies (policy_number, kyc_id, domain, status, sum_assured, inception_date, tenure_months)
        VALUES (?, ?, ?, ?, ?, date('now'), ?)
        """, (request.policy_number, request.kyc_id, request.domain, "Active", request.sum_assured, request.tenure_months))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==========================================================
# 🏥 2. MEDICAL REGISTRY ENDPOINTS
# ==========================================================

@app.get("/api/medical/doctor/{license_number}", response_model=Optional[Dict[str, Any]])
def verify_doctor(license_number: str):
    try:
        conn = _get_conn("medical")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doctor_registry WHERE license_number = ?", (license_number,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/medical/hospital/{hospital_name}", response_model=Optional[Dict[str, Any]])
def verify_hospital(hospital_name: str):
    try:
        conn = _get_conn("medical")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM hospital_registry WHERE LOWER(hospital_name) = LOWER(?)", (hospital_name.strip(),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==========================================================
# 🚗 3. MOTOR VEHICLE REGISTRY ENDPOINTS
# ==========================================================

@app.get("/api/motor/vehicle/{license_plate}", response_model=Optional[Dict[str, Any]])
def verify_vehicle(license_plate: str):
    try:
        conn = _get_conn("motor")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicle_registry WHERE LOWER(license_plate) = LOWER(?)", (license_plate.strip(),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/api/motor/police_report/{license_plate}", response_model=Optional[Dict[str, Any]])
def get_police_report(license_plate: str):
    try:
        conn = _get_conn("motor")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM police_reports WHERE LOWER(license_plate) = LOWER(?)", (license_plate.strip(),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/motor/onboard", response_model=bool)
def onboard_vehicle(request: OnboardVehicleRequest):
    try:
        conn = _get_conn("motor")
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO vehicle_registry (license_plate, registered_owner_name, vehicle_model, engine_number, chassis_number, registration_status)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (request.license_plate, request.registered_owner_name, request.vehicle_model, request.engine_number, request.chassis_number, request.registration_status))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==========================================================
# 👤 4. DEATH REGISTRY ENDPOINTS
# ==========================================================

@app.get("/api/death/record/{certificate_id}", response_model=Optional[Dict[str, Any]])
def get_death_record(certificate_id: str):
    try:
        conn = _get_conn("death")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM death_registry WHERE death_certificate_id = ?", (certificate_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ==========================================================
# 💰 5. CREDIT BUREAU ENDPOINTS
# ==========================================================

@app.get("/api/credit/loan/{loan_id}", response_model=Optional[Dict[str, Any]])
def get_loan_details(loan_id: str):
    try:
        conn = _get_conn("credit")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM loan_registry WHERE loan_id = ?", (loan_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/credit/onboard", response_model=bool)
def onboard_loan(request: OnboardLoanRequest):
    try:
        conn = _get_conn("credit")
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO loan_registry (loan_id, policy_number, lender_name, loan_type, loan_amount, tenure_months, emi_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (request.loan_id, request.policy_number, request.lender_name, request.loan_type, request.loan_amount, request.tenure_months, request.emi_amount))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
