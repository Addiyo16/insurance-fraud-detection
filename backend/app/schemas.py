from pydantic import BaseModel
from typing import List

class ClaimRequest(BaseModel):
    insurance_type: str
    policy_type: str
    incident_type: str
    payment_method: str
    region: str
    claim_amount: float
    customer_age: int
    policy_tenure_days: int
    num_previous_claims: int
    days_since_last_claim: int
    claim_processing_days: int


class PredictionResponse(BaseModel):
    prediction: int
    probability: float
    reasons: List[str]
