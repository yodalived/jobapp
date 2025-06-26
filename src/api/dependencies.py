from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.core.auth import decode_access_token
from src.api.models.auth import User, TIER_LIMITS

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    
    if email is None or user_id is None:
        raise credentials_exception
    
    result = await db.execute(
        select(User).where(User.id == user_id, User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user


async def get_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Ensure the user has verified their email"""
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please check your email to verify your account."
        )
    return current_user


async def check_resume_generation_limit(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Check if unverified users have reached their resume generation limit"""
    if not current_user.email_verified and current_user.resumes_generated_count >= 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Resume generation limit reached (2 resumes for unverified accounts). Please verify your email to continue."
        )
    return current_user


def check_user_limits(limit_name: str):
    """Decorator to check if user has access to a feature based on their tier"""
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        limits = TIER_LIMITS[current_user.subscription_tier]
        
        if limit_name in limits:
            limit_value = limits[limit_name]
            
            # Boolean permissions
            if isinstance(limit_value, bool) and not limit_value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Feature '{limit_name}' not available in {current_user.subscription_tier} tier"
                )
            
            # Numeric limits are checked elsewhere (in the service layer)
            
        return current_user
    
    return permission_checker
