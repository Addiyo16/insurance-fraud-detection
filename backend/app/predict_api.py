from fastapi import APIRouter
from backend.app.schemas import ClaimRequest, PredictionResponse

from ml.src.predict import predict_fraud
from ml.src.eligibility_rules import check_eligibility
from ml.src.reason_engine import generate_reasons

router = APIRouter(prefix="/predict", tags=["Fraud Prediction"])


@router.post("/", response_model=PredictionResponse)
def predict_claim(data: ClaimRequest):

    input_data = data.dict()

    eligible, eligibility_reasons = check_eligibility(input_data)

    if not eligible:
        return PredictionResponse(
            prediction=0,
            probability=0.0,
            reasons=eligibility_reasons
        )

    prediction, probability = predict_fraud(input_data)

    reasons = []
    if prediction == 1:
        reasons = generate_reasons(input_data)

    return PredictionResponse(
        prediction=prediction,
        probability=probability,
        reasons=reasons
    )
