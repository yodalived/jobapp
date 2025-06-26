from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import secrets
from pydantic import BaseModel

from src.core.database import get_db
from src.core.config import settings
from src.core.auth import get_password_hash, authenticate_user, create_access_token
from src.core.email import email_service
from src.api.models.auth import User, TIER_LIMITS
from src.api.models.auth_schemas import UserCreate, User as UserResponse, Token
from src.api.dependencies import get_current_active_user

router = APIRouter(tags=["authentication"])


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    # Check if user exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    
    # Create new user
    db_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        email_verification_token=verification_token,
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    # Send verification email
    email_sent = await email_service.send_verification_email(
        db_user.email, 
        verification_token
    )
    
    if not email_sent:
        # Log verification link if email fails to send
        print(f"📧 Email service not configured. Verification link: http://localhost:3080/verify-email?token={verification_token}")
    
    return db_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login and receive access token"""
    user = await authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user info"""
    return current_user


@router.get("/me/usage")
async def get_usage_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's usage statistics and limits"""
    limits = TIER_LIMITS[current_user.subscription_tier]
    
    return {
        "subscription_tier": current_user.subscription_tier,
        "usage": {
            "applications_count": current_user.applications_count,
            "resumes_generated_count": current_user.resumes_generated_count,
        },
        "limits": limits,
        "subscription_expires_at": current_user.subscription_expires_at,
    }


class EmailVerificationRequest(BaseModel):
    token: str

@router.post("/verify-email")
async def verify_email(
    request: EmailVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify user email with token"""
    # Find user by verification token
    result = await db.execute(
        select(User).where(User.email_verification_token == request.token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Mark email as verified and remove token
    user.email_verified = True
    user.email_verification_token = None
    
    await db.commit()
    
    return {"message": "Email verified successfully"}


@router.delete("/delete-test-user")
async def delete_test_user(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete test user - for development/testing only"""
    # Only allow deletion of specific test email
    if email != "yodalives@gmail.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only test user deletion allowed"
        )
    
    # Check if user exists first
    result = await db.execute(
        select(User.id).where(User.email == email)
    )
    user_id = result.scalar_one_or_none()
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test user not found"
        )
    
    # Use raw SQL to delete user to avoid cascade issues with missing tables
    from sqlalchemy import text
    await db.execute(text("DELETE FROM users WHERE email = :email"), {"email": email})
    await db.commit()
    
    return {"message": f"Test user {email} deleted successfully"}
