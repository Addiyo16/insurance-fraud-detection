import sqlite3
import os
import requests

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# Separate database file paths mapping
DB_PATHS = {
    "insurance": os.path.join(DB_DIR, "insurance_company.db"),
    "medical": os.path.join(DB_DIR, "medical_registry.db"),
    "motor": os.path.join(DB_DIR, "motor_registry.db"),
    "death": os.path.join(DB_DIR, "death_registry.db"),
    "credit": os.path.join(DB_DIR, "credit_registry.db")
}

API_BASE_URL = "http://127.0.0.1:8000"

def _get_connection(db_key):
    return sqlite3.connect(DB_PATHS[db_key])

def _get_from_api(endpoint, params=None):
    """
    Attempts to fetch data from the FastAPI REST service.
    Returns (data, True) on success, or (None, False) on failure/timeout.
    """
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=1.5)
        if response.status_code == 200:
            return response.json(), True
        return None, False
    except Exception:
        # Fallback silently to direct SQLite
        return None, False

def _post_to_api(endpoint, json_data):
    """
    Attempts to send data to the FastAPI REST service.
    Returns (response_json, True) on success, or (None, False) on failure/timeout.
    """
    try:
        response = requests.post(f"{API_BASE_URL}{endpoint}", json=json_data, timeout=1.5)
        if response.status_code == 200:
            return response.json(), True
        return None, False
    except Exception:
        # Fallback silently to direct SQLite
        return None, False

def get_policy_details(policy_number):
    """
    Query the Insurance Company DB: Fetch policy and linked policyholder details.
    """
    # Try REST API
    data, success = _get_from_api(f"/api/policy/{policy_number}")
    if success:
        return data

    # SQLite Fallback
    try:
        conn = _get_connection("insurance")
        conn.row_factory = sqlite3.Row
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
        print("API Client SQLite Fallback Error (get_policy_details):", e)
        return None

def verify_doctor(license_number):
    """
    Query the Medical Registry DB: Verify doctor credentials.
    """
    # Try REST API
    data, success = _get_from_api(f"/api/medical/doctor/{license_number}")
    if success:
        return data

    # SQLite Fallback
    try:
        conn = _get_connection("medical")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM doctor_registry WHERE license_number = ?", (license_number,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    except Exception as e:
        print("API Client SQLite Fallback Error (verify_doctor):", e)
        return None

def verify_hospital(hospital_name):
    """
    Query the Medical Registry DB: Verify hospital network and accreditation.
    """
    # Try REST API
    data, success = _get_from_api(f"/api/medical/hospital/{hospital_name}")
    if success:
        return data

    # SQLite Fallback
    try:
        conn = _get_connection("medical")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM hospital_registry WHERE LOWER(hospital_name) = LOWER(?)", (hospital_name.strip(),))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    except Exception as e:
        print("API Client SQLite Fallback Error (verify_hospital):", e)
        return None

def verify_vehicle(license_plate):
    """
    Query the Motor Registry DB: Query plate records (Vahan database equivalent).
    """
    # Try REST API
    data, success = _get_from_api(f"/api/motor/vehicle/{license_plate}")
    if success:
        return data

    # SQLite Fallback
    try:
        conn = _get_connection("motor")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM vehicle_registry WHERE LOWER(license_plate) = LOWER(?)", (license_plate.strip(),))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    except Exception as e:
        print("API Client SQLite Fallback Error (verify_vehicle):", e)
        return None

def get_police_report(license_plate):
    """
    Query the Motor Registry DB: Fetch official traffic logs.
    """
    # Try REST API
    data, success = _get_from_api(f"/api/motor/police_report/{license_plate}")
    if success:
        return data

    # SQLite Fallback
    try:
        conn = _get_connection("motor")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM police_reports WHERE LOWER(license_plate) = LOWER(?)", (license_plate.strip(),))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    except Exception as e:
        print("API Client SQLite Fallback Error (get_police_report):", e)
        return None

def get_death_record(certificate_id):
    """
    Query the National Death Registry DB: Verify death certification records.
    """
    # Try REST API
    data, success = _get_from_api(f"/api/death/record/{certificate_id}")
    if success:
        return data

    # SQLite Fallback
    try:
        conn = _get_connection("death")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM death_registry WHERE death_certificate_id = ?", (certificate_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    except Exception as e:
        print("API Client SQLite Fallback Error (get_death_record):", e)
        return None

def get_loan_details(loan_id):
    """
    Query the Credit Bureau DB: Verify outstanding bank loans.
    """
    # Try REST API
    data, success = _get_from_api(f"/api/credit/loan/{loan_id}")
    if success:
        return data

    # SQLite Fallback
    try:
        conn = _get_connection("credit")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM loan_registry WHERE loan_id = ?", (loan_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    except Exception as e:
        print("API Client SQLite Fallback Error (get_loan_details):", e)
        return None

def check_duplicate_claim(policy_number, claim_amount, days_limit=30):
    """
    Query the Insurance Company DB: Check if a duplicate claim was submitted.
    """
    # Try REST API
    data, success = _get_from_api("/api/insurance/duplicate_claim", params={"policy_number": policy_number, "claim_amount": claim_amount})
    if success:
        return data

    # SQLite Fallback
    try:
        conn = _get_connection("insurance")
        cursor = conn.cursor()
        
        query = """
        SELECT COUNT(*) FROM claims_log 
        WHERE policy_number = ? AND claim_amount = ?
        """
        cursor.execute(query, (policy_number, claim_amount))
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    except Exception as e:
        print("API Client SQLite Fallback Error (check_duplicate_claim):", e)
        return False

def get_claim_history_count(policy_number):
    """
    Query the Insurance Company DB: Count previous claims.
    """
    # Try REST API
    data, success = _get_from_api(f"/api/insurance/claim_history_count/{policy_number}")
    if success:
        return data

    # SQLite Fallback
    try:
        conn = _get_connection("insurance")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM claims_log WHERE policy_number = ?", (policy_number,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print("API Client SQLite Fallback Error (get_claim_history_count):", e)
        return 0

def log_claim(claim_id, policy_number, claim_amount, status):
    """
    Query the Insurance Company DB: Log a claim transaction.
    """
    # Try REST API
    payload = {
        "claim_id": claim_id,
        "policy_number": policy_number,
        "claim_amount": claim_amount,
        "status": status
    }
    data, success = _post_to_api("/api/insurance/log_claim", json_data=payload)
    if success:
        return data

    # SQLite Fallback
    try:
        conn = _get_connection("insurance")
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT OR REPLACE INTO claims_log (claim_id, policy_number, claim_date, claim_amount, status)
        VALUES (?, ?, date('now'), ?, ?)
        """, (claim_id, policy_number, claim_amount, status))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("API Client SQLite Fallback Error (log_claim):", e)
        return False

def onboard_policyholder(kyc_id, full_name, age, gender, credit_score, email, policy_number, domain, sum_assured, tenure_months=12):
    """
    Onboards a new policyholder and policy in the insurance DB.
    """
    payload = {
        "kyc_id": kyc_id,
        "full_name": full_name,
        "age": age,
        "gender": gender,
        "credit_score": credit_score,
        "email": email,
        "policy_number": policy_number,
        "domain": domain,
        "sum_assured": sum_assured,
        "tenure_months": tenure_months
    }
    data, success = _post_to_api("/api/insurance/onboard", json_data=payload)
    if success:
        return data

    # SQLite Fallback
    try:
        conn = _get_connection("insurance")
        cursor = conn.cursor()
        
        # Insert policyholder
        cursor.execute("""
        INSERT INTO policyholders (kyc_id, full_name, age, gender, credit_score, email)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (kyc_id, full_name, age, gender, credit_score, email))
        
        # Insert policy
        cursor.execute("""
        INSERT INTO policies (policy_number, kyc_id, domain, status, sum_assured, inception_date, tenure_months)
        VALUES (?, ?, ?, ?, ?, date('now'), ?)
        """, (policy_number, kyc_id, domain, "Active", sum_assured, tenure_months))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("API Client SQLite Fallback Error (onboard_policyholder):", e)
        return False

def onboard_vehicle(license_plate, registered_owner_name, vehicle_model, engine_number, chassis_number, registration_status):
    """
    Onboards a new vehicle in the motor vehicle registry DB.
    """
    payload = {
        "license_plate": license_plate,
        "registered_owner_name": registered_owner_name,
        "vehicle_model": vehicle_model,
        "engine_number": engine_number,
        "chassis_number": chassis_number,
        "registration_status": registration_status
    }
    data, success = _post_to_api("/api/motor/onboard", json_data=payload)
    if success:
        return data

    # SQLite Fallback
    try:
        conn = _get_connection("motor")
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO vehicle_registry (license_plate, registered_owner_name, vehicle_model, engine_number, chassis_number, registration_status)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (license_plate, registered_owner_name, vehicle_model, engine_number, chassis_number, registration_status))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("API Client SQLite Fallback Error (onboard_vehicle):", e)
        return False

def onboard_loan(loan_id, policy_number, lender_name, loan_type, loan_amount, tenure_months, emi_amount):
    """
    Onboards a new loan in the credit bureau DB.
    """
    payload = {
        "loan_id": loan_id,
        "policy_number": policy_number,
        "lender_name": lender_name,
        "loan_type": loan_type,
        "loan_amount": loan_amount,
        "tenure_months": tenure_months,
        "emi_amount": emi_amount
    }
    data, success = _post_to_api("/api/credit/onboard", json_data=payload)
    if success:
        return data

    # SQLite Fallback
    try:
        conn = _get_connection("credit")
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO loan_registry (loan_id, policy_number, lender_name, loan_type, loan_amount, tenure_months, emi_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (loan_id, policy_number, lender_name, loan_type, loan_amount, tenure_months, emi_amount))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("API Client SQLite Fallback Error (onboard_loan):", e)
        return False
