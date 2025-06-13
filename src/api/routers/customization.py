from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from src.core.database import get_db
from src.api.dependencies import get_current_active_user
from src.api.models.auth import User
from src.api.models.resume_customization import SystemPrompt, RAGDocument, IndustryTemplate, IndustryType


router = APIRouter(tags=["customization"])


class SystemPromptCreate(BaseModel):
    name: str
    description: Optional[str] = None
    prompt_text: str
    industry: IndustryType = IndustryType.GENERAL
    is_default: bool = False


class SystemPromptResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    prompt_text: str
    industry: IndustryType
    is_active: bool
    is_default: bool
    usage_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RAGDocumentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    content: str
    document_type: str = "guide"
    industry: IndustryType = IndustryType.GENERAL
    system_prompt_id: Optional[int] = None


class RAGDocumentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    content: str
    document_type: str
    industry: IndustryType
    created_at: datetime
    
    class Config:
        from_attributes = True


class IndustryTemplateResponse(BaseModel):
    id: int
    industry: IndustryType
    name: str
    description: Optional[str]
    suggested_skills: List[str]
    keywords: List[str]
    resume_tips: List[str]
    
    class Config:
        from_attributes = True


@router.get("/prompts", response_model=List[SystemPromptResponse])
async def list_system_prompts(
    industry: Optional[IndustryType] = None,
    include_global: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List available system prompts"""
    query = select(SystemPrompt).where(SystemPrompt.is_active == True)
    
    # Filter by user's prompts + global prompts
    if include_global:
        query = query.where(
            (SystemPrompt.user_id == current_user.id) | 
            (SystemPrompt.user_id == None)
        )
    else:
        query = query.where(SystemPrompt.user_id == current_user.id)
    
    # Filter by industry if specified
    if industry:
        query = query.where(SystemPrompt.industry == industry)
    
    result = await db.execute(query.order_by(SystemPrompt.usage_count.desc()))
    return result.scalars().all()


@router.post("/prompts", response_model=SystemPromptResponse)
async def create_system_prompt(
    prompt: SystemPromptCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a custom system prompt"""
    # Check if user has permission to create prompts
    # For now, all users can create their own prompts
    
    db_prompt = SystemPrompt(
        **prompt.dict(),
        user_id=current_user.id,
        is_active=True
    )
    
    db.add(db_prompt)
    await db.commit()
    await db.refresh(db_prompt)
    
    return db_prompt


@router.get("/prompts/{prompt_id}", response_model=SystemPromptResponse)
async def get_system_prompt(
    prompt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific system prompt"""
    result = await db.execute(
        select(SystemPrompt).where(
            SystemPrompt.id == prompt_id,
            SystemPrompt.is_active == True,
            (SystemPrompt.user_id == current_user.id) | (SystemPrompt.user_id == None)
        )
    )
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        raise HTTPException(status_code=404, detail="System prompt not found")
    
    return prompt


@router.get("/rag-documents", response_model=List[RAGDocumentResponse])
async def list_rag_documents(
    industry: Optional[IndustryType] = None,
    document_type: Optional[str] = None,
    system_prompt_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List available RAG documents"""
    query = select(RAGDocument)
    
    # Filter by user's documents + global documents
    query = query.where(
        (RAGDocument.user_id == current_user.id) | 
        (RAGDocument.user_id == None)
    )
    
    if industry:
        query = query.where(RAGDocument.industry == industry)
    
    if document_type:
        query = query.where(RAGDocument.document_type == document_type)
    
    if system_prompt_id:
        query = query.where(RAGDocument.system_prompt_id == system_prompt_id)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/rag-documents", response_model=RAGDocumentResponse)
async def create_rag_document(
    document: RAGDocumentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a RAG document"""
    db_document = RAGDocument(
        **document.dict(),
        user_id=current_user.id
    )
    
    # TODO: Generate embedding for the document
    # db_document.embedding = generate_embedding(document.content)
    
    db.add(db_document)
    await db.commit()
    await db.refresh(db_document)
    
    return db_document


@router.get("/industries", response_model=List[IndustryTemplateResponse])
async def list_industry_templates(
    db: AsyncSession = Depends(get_db)
):
    """List all industry templates with their configurations"""
    result = await db.execute(select(IndustryTemplate))
    return result.scalars().all()


@router.get("/industries/{industry}", response_model=IndustryTemplateResponse)
async def get_industry_template(
    industry: IndustryType,
    db: AsyncSession = Depends(get_db)
):
    """Get specific industry template"""
    result = await db.execute(
        select(IndustryTemplate).where(IndustryTemplate.industry == industry)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Industry template not found")
    
    return template


# Endpoint to get recommended prompt for a job
@router.post("/recommend-prompt")
async def recommend_system_prompt(
    job_description: str = Query(...),
    industry: Optional[IndustryType] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Recommend the best system prompt for a job description"""
    
    # Get available prompts
    query = select(SystemPrompt).where(
        SystemPrompt.is_active == True,
        (SystemPrompt.user_id == current_user.id) | (SystemPrompt.user_id == None)
    )
    
    if industry:
        query = query.where(SystemPrompt.industry == industry)
    
    result = await db.execute(query)
    prompts = result.scalars().all()
    
    if not prompts:
        raise HTTPException(status_code=404, detail="No prompts available")
    
    # For now, return the most used prompt for the industry
    # TODO: Implement smarter recommendation based on job description analysis
    recommended = max(prompts, key=lambda p: p.usage_count)
    
    return {
        "recommended_prompt": {
            "id": recommended.id,
            "name": recommended.name,
            "description": recommended.description,
            "industry": recommended.industry
        },
        "reason": f"Most successful prompt for {industry or 'general'} positions"
    }
