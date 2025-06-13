from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from src.core.database import Base


class IndustryType(str, enum.Enum):
    TECH = "tech"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    MARKETING = "marketing"
    SALES = "sales"
    EDUCATION = "education"
    GOVERNMENT = "government"
    NONPROFIT = "nonprofit"
    CONSULTING = "consulting"
    LEGAL = "legal"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    HOSPITALITY = "hospitality"
    GENERAL = "general"


class SystemPrompt(Base):
    __tablename__ = "system_prompts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    prompt_text = Column(Text, nullable=False)
    industry = Column(SQLEnum(IndustryType), default=IndustryType.GENERAL)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # User-specific or global
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # NULL = global prompt
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    usage_count = Column(Integer, default=0)
    average_rating = Column(Integer)  # 1-5 rating from users
    
    # Configuration
    config = Column(JSON, default={})  # Store any additional settings
    
    # Relationships
    user = relationship("User", backref="custom_prompts")
    rag_documents = relationship("RAGDocument", back_populates="system_prompt")


class RAGDocument(Base):
    __tablename__ = "rag_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    content = Column(Text, nullable=False)
    document_type = Column(String)  # 'guide', 'example', 'rules', etc.
    industry = Column(SQLEnum(IndustryType), default=IndustryType.GENERAL)
    
    # Associate with system prompt
    system_prompt_id = Column(Integer, ForeignKey("system_prompts.id"), nullable=True)
    
    # User-specific or global
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Vector embedding for similarity search
    embedding = Column(JSON)  # Store vector embedding
    
    # Relationships
    system_prompt = relationship("SystemPrompt", back_populates="rag_documents")
    user = relationship("User", backref="custom_rag_documents")


class IndustryTemplate(Base):
    __tablename__ = "industry_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    industry = Column(SQLEnum(IndustryType), unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Default configurations for this industry
    default_prompt_id = Column(Integer, ForeignKey("system_prompts.id"))
    suggested_skills = Column(JSON, default=[])  # Common skills for this industry
    keywords = Column(JSON, default=[])  # Important keywords
    resume_tips = Column(JSON, default=[])  # Industry-specific tips
    
    # Formatting preferences
    preferred_length = Column(String)  # "1-page", "2-page", etc.
    bullet_style = Column(String)  # "achievement-focused", "responsibility-focused"
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    default_prompt = relationship("SystemPrompt")
