from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum

from src.core.database import get_db
from src.api.dependencies import get_current_active_user
from src.api.models.auth import User, TIER_LIMITS
from src.api.models.schema import JobApplication, ResumeVersion
from src.generator.resume_generator import ResumeGenerator
from src.generator.resume_customizer import ResumeCustomizer, JobAnalyzer
from src.generator.llm_interface import LLMService
from src.generator.example_data import FULL_RESUME_DATA, MINIMAL_RESUME_DATA


router = APIRouter(tags=["generator"])

generator = ResumeGenerator()
customizer = ResumeCustomizer()
job_analyzer = JobAnalyzer()
llm_service = LLMService()


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AUTO = "auto"  # Use any available


class GenerateResumeRequest(BaseModel):
    application_id: int
    master_resume_data: Dict[str, Any]
    customize_with_ai: bool = True
    llm_provider: Optional[LLMProvider] = LLMProvider.AUTO
    template_name: str = "modern_professional"


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


@router.post("/generate-customized")
async def generate_customized_resume(
    request: GenerateResumeRequest,
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
        # Determine which provider to use
        provider = None if request.llm_provider == LLMProvider.AUTO else request.llm_provider.value
        
        # Customize with AI if requested and job description available
        if request.customize_with_ai and application.job_description:
            resume_data = await customizer.customize_resume_for_job(
                master_resume_data=request.master_resume_data,
                job_description=application.job_description,
                job_title=application.position,
                company=application.company,
                provider=provider
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
            "llm_provider": provider or "default",
            "message": "Resume generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-job")
async def analyze_job_description(
    job_description: str = Query(..., description="Job description to analyze"),
    llm_provider: LLMProvider = Query(LLMProvider.AUTO, description="LLM provider to use"),
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
        provider = None if llm_provider == LLMProvider.AUTO else llm_provider.value
        analysis = await job_analyzer.analyze_job(job_description, provider=provider)
        
        return {
            "analysis": analysis,
            "recommendations": {
                "skills_to_highlight": analysis.get("required_skills", [])[:5],
                "keywords_to_include": analysis.get("important_keywords", [])[:10],
                "experience_level": analysis.get("experience_level", "unknown")
            },
            "llm_provider_used": provider or llm_service.default_provider
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare-providers")
async def compare_llm_providers(
    job_description: str = Query(..., description="Job description to analyze"),
    current_user: User = Depends(get_current_active_user)
):
    """Compare outputs from different LLM providers for the same job"""
    
    # Premium feature - could restrict to higher tiers
    limits = TIER_LIMITS[current_user.subscription_tier]
    if not limits.get("can_use_ai_suggestions", True):
        raise HTTPException(status_code=403, detail="Feature not available in your tier")
    
    available_providers = llm_service.get_available_providers()
    if len(available_providers) < 2:
        raise HTTPException(
            status_code=400,
            detail="Need at least 2 LLM providers configured for comparison"
        )
    
    results = {}
    
    for provider in available_providers:
        try:
            analysis = await job_analyzer.analyze_job(job_description, provider=provider)
            results[provider] = {
                "success": True,
                "analysis": analysis
            }
        except Exception as e:
            results[provider] = {
                "success": False,
                "error": str(e)
            }
    
    return {
        "comparison": results,
        "providers_tested": available_providers
    }
