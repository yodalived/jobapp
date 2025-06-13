from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, Optional
from pydantic import BaseModel

from src.core.database import get_db
from src.api.dependencies import get_current_active_user
from src.api.models.auth import User, TIER_LIMITS
from src.api.models.schema import JobApplication, ResumeVersion
from src.generator.resume_generator import ResumeGenerator
from src.generator.resume_customizer import ResumeCustomizer, JobAnalyzer
from src.generator.example_data import FULL_RESUME_DATA, MINIMAL_RESUME_DATA


router = APIRouter(tags=["generator"])

generator = ResumeGenerator()
customizer = ResumeCustomizer()
job_analyzer = JobAnalyzer()


class GenerateResumeRequest(BaseModel):
    application_id: int
    master_resume_data: Dict[str, Any]
    customize_with_ai: bool = True
    template_name: str = "modern_professional"


class AnalyzeJobRequest(BaseModel):
    job_description: str


@router.post("/generate-customized")
async def generate_customized_resume(
    request: GenerateResumeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a resume customized for a specific job application"""
    
    # Check AI features access
    limits = TIER_LIMITS[current_user.subscription_tier]
    if request.customize_with_ai and not limits.get("can_use_ai_suggestions", True):
        raise HTTPException(
            status_code=403,
            detail=f"AI customization not available in {current_user.subscription_tier} tier"
        )
    
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
    
    # Check resume generation limits
    monthly_limit = limits.get("monthly_resumes", 20)
    if monthly_limit != -1 and current_user.resumes_generated_count >= monthly_limit:
        raise HTTPException(
            status_code=403,
            detail=f"Monthly resume limit ({monthly_limit}) reached"
        )
    
    try:
        # Customize with AI if requested and job description available
        if request.customize_with_ai and application.job_description:
            resume_data = await customizer.customize_resume_for_job(
                master_resume_data=request.master_resume_data,
                job_description=application.job_description,
                job_title=application.position,
                company=application.company
            )
        else:
            resume_data = request.master_resume_data
        
        # Generate the PDF
        resume_version = await generator.generate_resume(
            user=current_user,
            job_application=application,
            resume_data=resume_data,
            template_name=request.template_name,
            db=db
        )
        
        # Update counts
        current_user.resumes_generated_count += 1
        await db.commit()
        
        return {
            "id": resume_version.id,
            "version_name": resume_version.version_name,
            "file_url": resume_version.file_url,
            "customized": request.customize_with_ai,
            "message": "Resume generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-job")
async def analyze_job_description(
    request: AnalyzeJobRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Analyze a job description to extract key requirements"""
    
    # Check if user has AI access
    limits = TIER_LIMITS[current_user.subscription_tier]
    if not limits.get("can_use_ai_suggestions", True):
        raise HTTPException(
            status_code=403,
            detail=f"AI analysis not available in {current_user.subscription_tier} tier"
        )
    
    try:
        analysis = await job_analyzer.analyze_job(request.job_description)
        return {
            "analysis": analysis,
            "recommendations": {
                "skills_to_highlight": analysis.get("required_skills", [])[:5],
                "keywords_to_include": analysis.get("important_keywords", [])[:10],
                "experience_level": analysis.get("experience_level", "unknown")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preview-customization")
async def preview_resume_customization(
    request: GenerateResumeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Preview how AI would customize your resume without generating PDF"""
    
    # Check AI access
    limits = TIER_LIMITS[current_user.subscription_tier]
    if not limits.get("can_use_ai_suggestions", True):
        raise HTTPException(
            status_code=403,
            detail=f"AI customization not available in {current_user.subscription_tier} tier"
        )
    
    # Get job application
    result = await db.execute(
        select(JobApplication).where(
            JobApplication.id == request.application_id,
            JobApplication.user_id == current_user.id
        )
    )
    application = result.scalar_one_or_none()
    
    if not application or not application.job_description:
        raise HTTPException(
            status_code=400,
            detail="Application not found or missing job description"
        )
    
    try:
        # Get customized content without generating PDF
        customized_data = await customizer.customize_resume_for_job(
            master_resume_data=request.master_resume_data,
            job_description=application.job_description,
            job_title=application.position,
            company=application.company
        )
        
        return {
            "original": request.master_resume_data,
            "customized": customized_data,
            "changes": {
                "summary_changed": customized_data.get("summary") != request.master_resume_data.get("summary"),
                "skills_reordered": True,  # Always true with AI
                "bullets_customized": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
