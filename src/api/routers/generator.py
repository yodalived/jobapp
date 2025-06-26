from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies import get_current_active_user, check_resume_generation_limit
from src.api.models.auth import User
from src.core.database import get_db
from src.generator.llm_interface import LLMService

router = APIRouter(tags=["generator"])

llm_service = LLMService()


class JobAnalysisRequest(BaseModel):
    job_description: str


@router.get("/llm-providers")
async def get_available_providers(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available LLM providers"""
    available = llm_service.get_available_providers()
    return {
        "available_providers": available,
        "default_provider": llm_service.default_provider,
        "configured": {
            "openai": "openai" in available,
            "anthropic": "anthropic" in available
        }
    }


@router.post("/analyze-job")
async def analyze_job(
    job_description: str,
    current_user: User = Depends(get_current_active_user)
):
    """Analyze a job description to extract key requirements and skills"""
    try:
        analysis = await llm_service.analyze_job_description(job_description)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job analysis failed: {str(e)}")


@router.post("/generate-resume")
async def generate_resume(
    job_id: int,
    template: str = "modern_professional",
    current_user: User = Depends(check_resume_generation_limit),
    db: AsyncSession = Depends(get_db)
):
    """Generate a resume tailored for a specific job application"""
    try:
        # Increment the resume generation count
        current_user.resumes_generated_count += 1
        await db.commit()
        
        # This would integrate with your resume generation service
        # For now, return a placeholder response
        return {
            "job_id": job_id,
            "template": template,
            "status": "generated",
            "message": "Resume generation would happen here",
            "user_id": current_user.id,
            "resumes_generated": current_user.resumes_generated_count,
            "email_verified": current_user.email_verified
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume generation failed: {str(e)}")