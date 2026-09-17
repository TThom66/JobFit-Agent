import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import schemas

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="JobFit Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "name": "JobFit Agent",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    logger.info("Health check called")
    return {"status": "ok"}

@app.post("/analyze", response_model=schemas.AnalyzeResponse)
def analyze(request: schemas.AnalyzeRequest):
    # Placeholder - agent logic goes here
    return {
        "match_score": 0,
        "matched_requirements": [],
        "missing_requirements": [],
        "company_research": "",
        "cover_letter": "",
        "resume_suggestions": []
    }