import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from agent import run_analysis, run_analysis_stream
import schemas
import pymupdf
import io

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
async def analyze(
    resume: UploadFile = File(..., description="Resume as PDF"),
    job_description: str = Form(..., description="Job description text")
):
    # Validate file type
    if not resume.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Resume must be a PDF file"
        )

    # Extract text from PDF
    try:
        contents = await resume.read()
        pdf = pymupdf.open(stream=contents, filetype="pdf")
        resume_text = ""
        for page in pdf:
            resume_text += page.get_text()
        pdf.close()

        if len(resume_text.strip()) < 100:
            raise HTTPException(
                status_code=400,
                detail="Could not extract enough text from PDF"
            )

        logger.info(f"Extracted {len(resume_text)} characters from resume")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise HTTPException(
            status_code=400,
            detail="Failed to read PDF file"
        )

    # Run analysis
    try:
        result = run_analysis(resume_text, job_description)
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Analysis service temporarily unavailable"
        )

@app.post("/analyze/stream")
async def analyze_stream(
    resume: UploadFile = File(..., description="Resume as PDF"),
    job_description: str = Form(..., description="Job description text")
):
    if not resume.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Resume must be a PDF file"
        )

    try:
        contents = await resume.read()
        pdf = pymupdf.open(stream=contents, filetype="pdf")
        resume_text = ""
        for page in pdf:
            resume_text += page.get_text()
        pdf.close()

        if len(resume_text.strip()) < 100:
            raise HTTPException(
                status_code=400,
                detail="Could not extract enough text from PDF"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise HTTPException(
            status_code=400,
            detail="Failed to read PDF file"
        )

    return StreamingResponse(
        run_analysis_stream(resume_text, job_description),
        media_type="text/event-stream"
    )