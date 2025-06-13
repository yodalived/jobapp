from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any, Optional
from pydantic import BaseModel

from src.core.database import get_db
from src.api.dependencies import get_current_active_user
from src.api.models.auth import User, TIER_LIMITS
from src.api.models.schema import JobApplication
from src.api.models.resume_customization import IndustryType
from src.generator.resume_generator import ResumeGenerator
from src.generator.resume_customizer_rag import ResumeCustomizerWithRAG
from src.generator.llm_interface import LLMService


router = APIRouter(tags=["generator"])

generator = ResumeGenerator()
customizer = ResumeCustomizerWithRAG()


class GenerateResumeRAGRequest(BaseModel):
    application_id: int
    master_resume_data: Dict[str, Any]
    customize_with_ai: bool = True
    system_prompt_id: Optional[int] = None
    industry: Optional[IndustryType] = None
    llm_provider: Optional[str] = None
    template_name: str = "modern_professional"


@router.post("/generate-with-rag")
async def generate_resume_with_rag(
    request: GenerateResumeRAGRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a resume using industry-specific prompts and RAG"""
    
    # Check permissions and limits
    limits = TIER_LIMITS[current_user.subscription_tier]
    if request.customize_with_ai and not limits.get("can_use_ai_suggestions", True):
        raise HTTPException(status_code=403, detail="AI customization not available in your tier")
    
    # Get job application
    result = await db.execute(
        select(JobApplication).where(
            JobApplication.id == request.application_id,
            JobApplication.user_id == current_user.id
        )
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    try:
        # Customize with RAG-enhanced system
        if request.customize_with_ai and application.job_description:
            resume_data = await customizer.customize_resume_for_job(
                db=db,
                master_resume_data=request.master_resume_data,
                job_description=application.job_description,
                job_title=application.position,
                company=application.company,
                industry=request.industry,
                system_prompt_id=request.system_prompt_id,
                user_id=current_user.id,
                provider=request.llm_provider
            )
        else:
            resume_data = request.master_resume_data
        
        # Generate PDF
        resume_version = await generator.generate_resume(
            user=current_user,
            job_application=application,
            resume_data=resume_data,
            template_name=request.template_name,
            db=db
        )
        
        # Update user count
        current_user.resumes_generated_count += 1
        await db.commit()
        
        return {
            "id": resume_version.id,
            "version_name": resume_version.version_name,
            "file_url": resume_version.file_url,
            "customized": request.customize_with_ai,
            "industry": request.industry,
            "message": "Resume generated successfully with RAG enhancement"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
