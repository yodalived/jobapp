# src/api/models/schema.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Text, Float, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from src.core.database import Base

class ApplicationStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    QUEUED = "queued"
    APPLIED = "applied"
    ACKNOWLEDGED = "acknowledged"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

class JobType(str, enum.Enum):
    TECHNICAL = "technical"
    MANAGEMENT = "management"
    HYBRID = "hybrid"

class JobApplication(Base):
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User Information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="job_applications")

    # Job Information
    company = Column(String, nullable=False, index=True)
    position = Column(String, nullable=False)
    job_type = Column(Enum(JobType), default=JobType.TECHNICAL)
    url = Column(String, unique=True, nullable=False)
    job_description = Column(Text)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    location = Column(String)
    remote = Column(Boolean, default=False)
    
    # Application Status
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.DISCOVERED, index=True)
    confidence_score = Column(Float)
    auto_applied = Column(Boolean, default=False)
    
    # Application Materials
    resume_version = Column(String)
    resume_url = Column(String)
    cover_letter_url = Column(String)
    
    # Timestamps
    discovered_at = Column(DateTime(timezone=True), server_default=func.now())
    applied_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Source Information
    source = Column(String)  # linkedin, indeed, etc
    source_job_id = Column(String)  # ID from the source platform
    
    # Extra Data - renamed from metadata
    extra_data = Column(JSON, default={})  # Store any extra data
    application_questions = Column(JSON, default=[])  # Questions asked during application
    
    # Relationships
    status_history = relationship("ApplicationStatusHistory", back_populates="application")
    notes = relationship("ApplicationNote", back_populates="application")

class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("job_applications.id"))
    old_status = Column(Enum(ApplicationStatus))
    new_status = Column(Enum(ApplicationStatus))
    changed_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)
    
    # Relationship
    application = relationship("JobApplication", back_populates="status_history")

class ApplicationNote(Base):
    __tablename__ = "application_notes"

    # User Information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="companies")
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("job_applications.id"))
    note = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    application = relationship("JobApplication", back_populates="notes")

class Company(Base):
    __tablename__ = "companies"

    # User Information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="companies")
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    website = Column(String)
    linkedin_url = Column(String)
    industry = Column(String)
    size = Column(String)  # e.g., "50-200", "1000-5000"
    extra_data = Column(JSON, default={})  # renamed from metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    # User Information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="resume_versions")
    
    id = Column(Integer, primary_key=True, index=True)
    version_name = Column(String, nullable=False)
    template_name = Column(String)
    file_url = Column(String)
    content_hash = Column(String)  # To detect duplicates
    job_type = Column(Enum(JobType))
    
    # Performance metrics
    times_used = Column(Integer, default=0)
    response_rate = Column(Float)  # Calculated metric
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    extra_data = Column(JSON, default={})  # renamed from metadata
