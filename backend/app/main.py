from fastapi import FastAPI
from backend.app.predict_api import router

app = FastAPI(
    title="Insurance Fraud Detection API",
    version="1.0"
)

app.include_router(router)

@app.get("/")
def health():
    return {"status": "API is running"}
