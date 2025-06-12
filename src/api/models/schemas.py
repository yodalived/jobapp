# src/api/models/schemas.py
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ApplicationStatusEnum(str, Enum):
    DISCOVERED = "discovered"
    QUEUED = "queued"
    APPLIED = "applied"
    ACKNOWLEDGED = "acknowledged"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class JobTypeEnum(str, Enum):
    TECHNICAL = "technical"
    MANAGEMENT = "management"
    HYBRID = "hybrid"

# Base schemas
class JobApplicationBase(BaseModel):
    company: str
    position: str
    job_type: Optional[JobTypeEnum] = JobTypeEnum.TECHNICAL
    url: str
    job_description: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    location: Optional[str] = None
    remote: bool = False
    source: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = {}  # renamed from metadata

class JobApplicationCreate(JobApplicationBase):
    pass

class JobApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatusEnum] = None
    resume_version: Optional[str] = None
    resume_url: Optional[str] = None
    cover_letter_url: Optional[str] = None
    notes: Optional[str] = None

class JobApplicationInDB(JobApplicationBase):
    id: int
    status: ApplicationStatusEnum
    confidence_score: Optional[float] = None
    auto_applied: bool = False
    discovered_at: datetime
    applied_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class JobApplicationResponse(JobApplicationInDB):
    pass

# For creating notes
class ApplicationNoteCreate(BaseModel):
    note: str

class ApplicationNoteResponse(BaseModel):
    id: int
    note: str
    created_at: datetime
    
    class Config:
        from_attributes = True
