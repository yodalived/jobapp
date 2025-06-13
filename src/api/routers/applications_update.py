# Add these imports to your existing applications.py
from src.api.dependencies import get_current_active_user
from src.api.models.auth import User

# Update all endpoints to include user dependency and filter by user_id
# Example for create_application:

@router.post("/", response_model=JobApplicationResponse)
async def create_application(
    application: JobApplicationCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new job application"""
    # Check if URL already exists for this user
    existing = await db.execute(
        select(JobApplication).where(
            JobApplication.url == application.url,
            JobApplication.user_id == current_user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Application with this URL already exists")
    
    db_application = JobApplication(
        **application.model_dump(),
        user_id=current_user.id  # Add user_id
    )
    db.add(db_application)
    
    # Update user's application count
    current_user.applications_count += 1
    
    await db.commit()
    await db.refresh(db_application)
    return db_application

# Similar updates needed for all other endpoints - always filter by user_id
