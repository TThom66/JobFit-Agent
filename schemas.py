from pydantic import BaseModel, field_validator
from typing import List


class AnalyzeRequest(BaseModel):
    job_description: str
    
    @field_validator("job_description")
    @classmethod
    def job_description_not_empty(cls, v):
        if len(v.strip()) < 50:
            raise ValueError(
                "Job description must be at least 50 characters"
            )
        return v

class RequirementMatch(BaseModel):
    requirement: str
    met: bool
    notes: str

class AnalyzeResponse(BaseModel):
    match_score: int
    matched_requirements: List[str]
    missing_requirements: List[str]
    company_research: str
    cover_letter: str
    resume_suggestions: List[str]