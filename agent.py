import logging
import json
import anthropic
import os
from dotenv import load_dotenv
from typing import Generator

load_dotenv()
logger = logging.getLogger(__name__)
client = anthropic.Anthropic()

def run_analysis_stream(
    resume: str, 
    job_description: str
) -> Generator[str, None, None]:
    """Yields SSE formatted progress updates and final result."""
    
    def send_progress(message: str) -> str:
        return f"data: {json.dumps({'type': 'progress', 'message': message})}\n\n"
    
    def send_result(data: dict) -> str:
        return f"data: {json.dumps({'type': 'result', 'data': data})}\n\n"
    
    def send_error(message: str) -> str:
        return f"data: {json.dumps({'type': 'error', 'message': message})}\n\n"

    try:
        yield send_progress("Analyzing job requirements...")
        requirements_result = analyze_requirements(resume, job_description)
        
        yield send_progress("Extracting company name...")
        company_name = extract_company_name(job_description)
        
        yield send_progress(f"Researching {company_name}...")
        company_research = research_company(company_name)
        
        yield send_progress("Writing tailored cover letter...")
        cover_letter = generate_cover_letter(
            resume,
            job_description,
            company_research,
            requirements_result
        )
        
        yield send_progress("Generating resume suggestions...")
        suggestions = generate_resume_suggestions(
            resume,
            job_description,
            requirements_result
        )
        
        result = {
            "match_score": requirements_result["match_score"],
            "matched_requirements": requirements_result["matched"],
            "missing_requirements": requirements_result["missing"],
            "company_research": company_research,
            "cover_letter": cover_letter,
            "resume_suggestions": suggestions
        }
        
        yield send_result(result)
        
    except Exception as e:
        logger.error(f"Analysis stream failed: {e}")
        yield send_error("Analysis failed. Please try again.")

def run_analysis(resume: str, job_description: str) -> dict:
    logger.info("Starting job fit analysis")

    # Step 1: Extract requirements and score match
    logger.info("Analyzing job requirements")
    requirements_result = analyze_requirements(resume, job_description)

    # Step 2: Research the company using web search
    logger.info("Researching company")
    company_name = extract_company_name(job_description)
    company_research = research_company(company_name)

    # Step 3: Generate cover letter
    logger.info("Generating cover letter")
    cover_letter = generate_cover_letter(
        resume, 
        job_description, 
        company_research,
        requirements_result
    )

    # Step 4: Generate resume suggestions
    logger.info("Generating resume suggestions")
    suggestions = generate_resume_suggestions(
        resume,
        job_description,
        requirements_result
    )

    return {
        "match_score": requirements_result["match_score"],
        "matched_requirements": requirements_result["matched"],
        "missing_requirements": requirements_result["missing"],
        "company_research": company_research,
        "cover_letter": cover_letter,
        "resume_suggestions": suggestions
    }

def analyze_requirements(resume: str, job_description: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Analyze this job description and resume.

Job Description:
{job_description}

Resume:
{resume}

Respond in exactly this JSON format with no other text:
{{
    "match_score": <integer 0-100>,
    "matched": ["requirement 1", "requirement 2"],
    "missing": ["requirement 1", "requirement 2"]
}}"""
        }]
    )

    text = response.content[0].text.strip()
    # Remove markdown code blocks if present
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        logger.error(f"Failed to parse requirements JSON: {text}")
        return {"match_score": 0, "matched": [], "missing": []}

def extract_company_name(job_description: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": f"""Extract only the company name from this job 
description. Respond with just the company name, nothing else.

{job_description}"""
        }]
    )
    return response.content[0].text.strip()

def research_company(company_name: str) -> str:
    logger.info(f"Searching for company: {company_name}")

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search"
        }],
        messages=[{
            "role": "user",
            "content": f"""Search for information about {company_name} 
as a place to work. Find:
1. What the company does
2. Their mission or values
3. Recent news or developments
4. Company culture if available

Provide a concise 2-3 paragraph summary useful for writing a 
job application cover letter."""
        }]
    )

    # Extract text from response which may include tool use blocks
    result = ""
    for block in response.content:
        if hasattr(block, "text"):
            result += block.text

    return result.strip() if result else f"Company research unavailable for {company_name}"

def generate_cover_letter(
    resume: str,
    job_description: str,
    company_research: str,
    requirements: dict
) -> str:
    matched = ", ".join(requirements.get("matched", []))
    missing = ", ".join(requirements.get("missing", []))

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Write a professional cover letter for this 
job application.

Resume:
{resume}

Job Description:
{job_description}

Company Research:
{company_research}

Matched Requirements: {matched}
Requirements to Address: {missing}

Write a tailored cover letter that:
1. Opens with genuine interest in the company based on research
2. Highlights matched requirements with specific examples
3. Addresses missing requirements honestly but positively
4. Keeps a professional but personable tone
5. Is 3-4 paragraphs, under 400 words"""
        }]
    )
    return response.content[0].text.strip()

def generate_resume_suggestions(
    resume: str,
    job_description: str,
    requirements: dict
) -> list:
    missing = ", ".join(requirements.get("missing", []))

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": f"""Given this resume and job description, 
suggest specific improvements to the resume.

Resume:
{resume}

Job Description:
{job_description}

Missing Requirements: {missing}

Respond in exactly this JSON format with no other text:
{{
    "suggestions": [
        "Specific suggestion 1",
        "Specific suggestion 2",
        "Specific suggestion 3"
    ]
}}"""
        }]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]

    try:
        result = json.loads(text.strip())
        return result.get("suggestions", [])
    except json.JSONDecodeError:
        logger.error(f"Failed to parse suggestions JSON: {text}")
        return []