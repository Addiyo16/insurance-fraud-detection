import random

import pandas as pd


SEED = 42
ROWS_PER_DOMAIN = 1500
random.seed(SEED)


def chance(probability):
    return random.random() < probability


def build_health_rows():
    rows = []
    diagnoses = ["viral fever", "pneumonia", "infection", "fracture surgery", "cardiac surgery"]
    for _ in range(ROWS_PER_DOMAIN):
        diagnosis = random.choice(diagnoses)
        days = random.randint(1, 12)
        hospital_network = random.choice([0, 1])
        history = random.randint(0, 6)
        per_day = random.randint(5_000, 65_000)
        amount = per_day * days
        medicine_ratio = random.uniform(0.05, 0.85)
        icu_ratio = random.uniform(0, 0.55)

        fraud = int(
            (diagnosis in {"viral fever"} and amount > 80_000)
            or (icu_ratio > 0.35 and diagnosis in {"viral fever", "infection"})
            or (medicine_ratio > 0.7)
            or (hospital_network == 0 and amount > 250_000)
            or history >= 4
        )
        if chance(0.04):
            fraud = 1 - fraud

        rows.append(
            {
                "domain": "Health",
                "amount": amount,
                "history": history,
                "hospital_network": hospital_network,
                "damage_cost": 0,
                "policy_duration": random.uniform(0.5, 12),
                "income": 0,
                "loan_amount": 0,
                "fraud": fraud,
            }
        )
    return rows


def build_vehicle_rows():
    rows = []
    for _ in range(ROWS_PER_DOMAIN):
        idv = random.randint(60_000, 2_500_000)
        damage_cost = random.randint(5_000, int(idv * 1.25))
        history = random.randint(0, 6)
        damage_ratio = damage_cost / idv
        minor_accident = chance(0.55)

        fraud = int(
            damage_cost > idv
            or (minor_accident and damage_ratio > 0.55)
            or damage_ratio > 0.9
            or history >= 4
        )
        if chance(0.04):
            fraud = 1 - fraud

        rows.append(
            {
                "domain": "Vehicle",
                "amount": damage_cost,
                "history": history,
                "hospital_network": 1,
                "damage_cost": damage_cost,
                "policy_duration": random.uniform(0, 10),
                "income": 0,
                "loan_amount": idv,
                "fraud": fraud,
            }
        )
    return rows


def build_life_rows():
    rows = []
    for _ in range(ROWS_PER_DOMAIN):
        sum_assured = random.randint(300_000, 10_000_000)
        policy_duration = random.uniform(0, 20)
        claim_ratio = random.uniform(0.3, 1.05)
        claim_amount = int(sum_assured * claim_ratio)
        history = random.randint(0, 3)

        fraud = int(
            claim_amount > sum_assured
            or (policy_duration < 1 and claim_ratio > 0.8)
            or (policy_duration < 2 and history >= 2)
        )
        if chance(0.04):
            fraud = 1 - fraud

        rows.append(
            {
                "domain": "Life",
                "amount": claim_amount,
                "history": history,
                "hospital_network": 1,
                "damage_cost": 0,
                "policy_duration": policy_duration,
                "income": 0,
                "loan_amount": sum_assured,
                "fraud": fraud,
            }
        )
    return rows


def build_financial_rows():
    rows = []
    for _ in range(ROWS_PER_DOMAIN):
        income = random.randint(15_000, 250_000)
        loan_amount = random.randint(50_000, 8_000_000)
        claim_amount = random.randint(10_000, int(loan_amount * 1.1))
        history = random.randint(0, 6)
        loan_to_annual_income = loan_amount / (income * 12)
        claim_ratio = claim_amount / loan_amount

        fraud = int(
            claim_amount > loan_amount
            or loan_to_annual_income > 6
            or claim_ratio > 0.95
            or history >= 4
        )
        if chance(0.04):
            fraud = 1 - fraud

        rows.append(
            {
                "domain": "Financial",
                "amount": claim_amount,
                "history": history,
                "hospital_network": 1,
                "damage_cost": 0,
                "policy_duration": random.uniform(0, 8),
                "income": income,
                "loan_amount": loan_amount,
                "fraud": fraud,
            }
        )
    return rows


def main():
    rows = (
        build_health_rows()
        + build_vehicle_rows()
        + build_life_rows()
        + build_financial_rows()
    )
    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    df.to_csv("data/raw/claims.csv", index=False)
    print(f"Generated {len(df)} synthetic claims at data/raw/claims.csv")
    print(df.groupby(["domain", "fraud"]).size())


if __name__ == "__main__":
    main()
