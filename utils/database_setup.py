import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# Define separate database file paths
DB_PATHS = {
    "insurance": os.path.join(DB_DIR, "insurance_company.db"),
    "medical": os.path.join(DB_DIR, "medical_registry.db"),
    "motor": os.path.join(DB_DIR, "motor_registry.db"),
    "death": os.path.join(DB_DIR, "death_registry.db"),
    "credit": os.path.join(DB_DIR, "credit_registry.db")
}

def init_distributed_dbs():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    # ---------------- 1. INSURANCE COMPANY DATABASE ----------------
    conn = sqlite3.connect(DB_PATHS["insurance"])
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policyholders (
        kyc_id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        credit_score INTEGER,
        email TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policies (
        policy_number TEXT PRIMARY KEY,
        kyc_id TEXT NOT NULL,
        domain TEXT NOT NULL,
        status TEXT NOT NULL,
        sum_assured REAL,
        inception_date TEXT,
        tenure_months INTEGER,
        FOREIGN KEY (kyc_id) REFERENCES policyholders(kyc_id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claims_log (
        claim_id TEXT PRIMARY KEY,
        policy_number TEXT NOT NULL,
        claim_date TEXT,
        claim_amount REAL,
        status TEXT
    )
    """)
    
    # Pre-populate
    cursor.execute("DELETE FROM policies")
    cursor.execute("DELETE FROM policyholders")
    cursor.execute("DELETE FROM claims_log")
    
    policyholders = [
        ("KYC_HEALTH_101", "Adarsh Sharma", 29, "Male", 780, "adarsh@example.com"),
        ("KYC_VEHICLE_201", "Sarah Jenkins", 45, "Female", 520, "sarah@example.com"),
        ("KYC_LIFE_301", "Robert Mercer", 62, "Male", 680, "robert@example.com"),
        ("KYC_FIN_401", "Robert Mercer", 62, "Male", 680, "robert@example.com"),
        ("KYC_BAD_ACTOR", "John Doe", 35, "Male", 400, "johndoe@example.com")
    ]
    cursor.executemany("INSERT INTO policyholders VALUES (?,?,?,?,?,?)", policyholders)

    policies = [
        ("POL_H_1001", "KYC_HEALTH_101", "Health", "Active", 500000.0, "2024-01-15", 36),
        ("POL_V_2002", "KYC_VEHICLE_201", "Vehicle", "Active", 300000.0, "2025-05-10", 12),
        ("POL_L_3003", "KYC_LIFE_301", "Life", "Active", 1000000.0, "2023-08-20", 120),
        ("POL_F_4004", "KYC_FIN_401", "Financial", "Active", 1500000.0, "2024-11-01", 60),
        ("POL_L_LAPSED", "KYC_BAD_ACTOR", "Life", "Lapsed", 200000.0, "2020-01-01", 24)
    ]
    cursor.executemany("INSERT INTO policies VALUES (?,?,?,?,?,?,?)", policies)
    
    conn.commit()
    conn.close()

    # ---------------- 2. MEDICAL REGISTRY DATABASE ----------------
    conn = sqlite3.connect(DB_PATHS["medical"])
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctor_registry (
        license_number TEXT PRIMARY KEY,
        doctor_name TEXT NOT NULL,
        specialty TEXT,
        status TEXT NOT NULL,
        blacklist_flag INTEGER DEFAULT 0
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hospital_registry (
        hospital_id TEXT PRIMARY KEY,
        hospital_name TEXT NOT NULL,
        address TEXT,
        network_flag INTEGER DEFAULT 1,
        blacklist_flag INTEGER DEFAULT 0
    )
    """)
    
    cursor.execute("DELETE FROM doctor_registry")
    cursor.execute("DELETE FROM hospital_registry")
    
    doctors = [
        ("DOC_12345", "Dr. Alice Vance", "Cardiology", "Active", 0),
        ("DOC_67890", "Dr. David Banner", "General Surgery", "Active", 0),
        ("DOC_55555", "Dr. Fake McDoc", "Internal Medicine", "Suspended", 1)
    ]
    cursor.executemany("INSERT INTO doctor_registry VALUES (?,?,?,?,?)", doctors)

    hospitals = [
        ("HOSP_101", "City Hospital", "123 Main St", 1, 0),
        ("HOSP_102", "Apex Clinic", "456 Oak Rd", 0, 0),
        ("HOSP_103", "Blacklisted Wellness Center", "789 Dark Alley", 0, 1)
    ]
    cursor.executemany("INSERT INTO hospital_registry VALUES (?,?,?,?,?)", hospitals)
    
    conn.commit()
    conn.close()

    # ---------------- 3. MOTOR VEHICLE REGISTRY (RTO) DATABASE ----------------
    conn = sqlite3.connect(DB_PATHS["motor"])
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicle_registry (
        license_plate TEXT PRIMARY KEY,
        registered_owner_name TEXT NOT NULL,
        vehicle_model TEXT,
        engine_number TEXT,
        chassis_number TEXT,
        registration_status TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS police_reports (
        report_id TEXT PRIMARY KEY,
        license_plate TEXT NOT NULL,
        incident_date TEXT,
        incident_location TEXT,
        severity TEXT,
        police_notes TEXT,
        FOREIGN KEY (license_plate) REFERENCES vehicle_registry(license_plate)
    )
    """)
    
    cursor.execute("DELETE FROM vehicle_registry")
    cursor.execute("DELETE FROM police_reports")
    
    vehicles = [
        ("KA-01-MA-1234", "Sarah Jenkins", "Car", "ENG123456", "CHAS123456", "Active"),
        ("MH-12-AB-5678", "Michael Chang", "Bike", "ENG789012", "CHAS789012", "Active"),
        ("DL-03-XY-9999", "John Doe", "Truck", "ENG999999", "CHAS999999", "Stolen")
    ]
    cursor.executemany("INSERT INTO vehicle_registry VALUES (?,?,?,?,?,?)", vehicles)

    police_reports = [
        ("POLICE_2001", "KA-01-MA-1234", "2026-06-01", "Bengaluru", "Major", "Vehicle collided with barrier. Severe front damage."),
        ("POLICE_2002", "MH-12-AB-5678", "2026-06-05", "Pune", "Minor", "Minor rear-end collision, scratch on bumper.")
    ]
    cursor.executemany("INSERT INTO police_reports VALUES (?,?,?,?,?,?)", police_reports)
    
    conn.commit()
    conn.close()

    # ---------------- 4. NATIONAL DEATH REGISTRY DATABASE ----------------
    conn = sqlite3.connect(DB_PATHS["death"])
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS death_registry (
        death_certificate_id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        date_of_death TEXT,
        cause_of_death TEXT,
        certified_by_doctor_license TEXT
    )
    """)
    
    cursor.execute("DELETE FROM death_registry")
    
    deaths = [
        ("DEATH_CERT_3001", "Robert Mercer", "2026-06-03", "Natural Causes", "DOC_12345"),
        ("DEATH_CERT_3002", "John Doe", "2026-05-20", "Suicide", "DOC_55555")
    ]
    cursor.executemany("INSERT INTO death_registry VALUES (?,?,?,?,?)", deaths)
    
    conn.commit()
    conn.close()

    # ---------------- 5. CREDIT BUREAU / BANK LOANS DATABASE ----------------
    conn = sqlite3.connect(DB_PATHS["credit"])
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loan_registry (
        loan_id TEXT PRIMARY KEY,
        policy_number TEXT NOT NULL,
        lender_name TEXT,
        loan_type TEXT,
        loan_amount REAL,
        tenure_months INTEGER,
        emi_amount REAL
    )
    """)
    
    cursor.execute("DELETE FROM loan_registry")
    
    loans = [
        ("LOAN_4001", "POL_F_4004", "Apex Capital", "Home", 1200000.0, 180, 15000.0),
        ("LOAN_4002", "POL_F_4004", "Fast Finance", "Personal", 500000.0, 36, 18000.0)
    ]
    cursor.executemany("INSERT INTO loan_registry VALUES (?,?,?,?,?,?,?)", loans)
    
    conn.commit()
    conn.close()
    
    print("Distributed sandboxed databases initialized successfully!")

if __name__ == "__main__":
    init_distributed_dbs()
