import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agent import run_analysis
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

@app.post("/analyze", response_model=schemas.AnalyzeResponse)
def analyze(request: schemas.AnalyzeRequest):
    logger.info("Analysis request received")
    try:
        result = run_analysis(request.resume, request.job_description)
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Analysis service temporarily unavailable"
        )