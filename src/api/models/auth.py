from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from src.core.database import Base


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Profile
    full_name = Column(String)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    
    # SaaS features
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_expires_at = Column(DateTime(timezone=True))
    
    # Usage tracking
    applications_count = Column(Integer, default=0)
    resumes_generated_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    
    # Relationships
    job_applications = relationship("JobApplication", back_populates="user", cascade="all, delete-orphan")
    resume_versions = relationship("ResumeVersion", back_populates="user", cascade="all, delete-orphan")
    

# Usage limits per tier
TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "monthly_applications": 50,
        "monthly_resumes": 20,
        "can_use_auto_apply": False,
        "can_use_ai_suggestions": True,
        "max_tracked_companies": 25,
    },
    SubscriptionTier.STARTER: {
        "monthly_applications": 200,
        "monthly_resumes": 100,
        "can_use_auto_apply": False,
        "can_use_ai_suggestions": True,
        "max_tracked_companies": 100,
    },
    SubscriptionTier.PROFESSIONAL: {
        "monthly_applications": 1000,
        "monthly_resumes": 500,
        "can_use_auto_apply": True,
        "can_use_ai_suggestions": True,
        "max_tracked_companies": 500,
    },
    SubscriptionTier.ENTERPRISE: {
        "monthly_applications": -1,  # Unlimited
        "monthly_resumes": -1,
        "can_use_auto_apply": True,
        "can_use_ai_suggestions": True,
        "max_tracked_companies": -1,
    },
}
