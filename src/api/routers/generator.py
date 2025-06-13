from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any

from src.core.database import get_db
from src.api.dependencies import get_current_active_user
from src.api.models.auth import User
from src.api.models.schema import JobApplication, ResumeVersion
from src.generator.resume_generator import ResumeGenerator
from src.generator.example_data import FULL_RESUME_DATA as EXAMPLE_RESUME_DATA
from pydantic import BaseModel


router = APIRouter(tags=["generator"])

generator = ResumeGenerator()


class GenerateResumeRequest(BaseModel):
    application_id: int
    resume_data: Dict[str, Any]
    template_name: str = "modern_professional"


class GenerateResumeResponse(BaseModel):
    id: int
    version_name: str
    file_url: str
    content_hash: str
    
    class Config:
        from_attributes = True


@router.post("/generate", response_model=GenerateResumeResponse)
async def generate_resume(
    request: GenerateResumeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a customized resume for a job application"""
    
    # Get the job application
    result = await db.execute(
        select(JobApplication).where(
            JobApplication.id == request.application_id,
            JobApplication.user_id == current_user.id
        )
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check user limits
    limits = TIER_LIMITS[current_user.subscription_tier]
    monthly_limit = limits.get("monthly_resumes", 20)
    
    if monthly_limit != -1 and current_user.resumes_generated_count >= monthly_limit:
        raise HTTPException(
            status_code=403,
            detail=f"Monthly resume generation limit ({monthly_limit}) reached for {current_user.subscription_tier} tier"
        )
    
    try:
        # Generate the resume
        resume_version = await generator.generate_resume(
            user=current_user,
            job_application=application,
            resume_data=request.resume_data,
            template_name=request.template_name,
            db=db
        )
        
        # Update user's resume count
        current_user.resumes_generated_count += 1
        await db.commit()
        
        return resume_version
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume generation failed: {str(e)}")


@router.get("/example-data")
async def get_example_resume_data(
    current_user: User = Depends(get_current_active_user)
):
    """Get example resume data structure"""
    return {
        "template_names": ["modern_professional"],
        "example_data": EXAMPLE_RESUME_DATA
    }


@router.get("/templates")
async def list_templates(
    current_user: User = Depends(get_current_active_user)
):
    """List available resume templates"""
    templates_dir = Path(__file__).parent.parent / "generator" / "templates"
    templates = [f.stem for f in templates_dir.glob("*.tex")]
    
    return {
        "templates": templates,
        "default": "modern_professional"
    }
