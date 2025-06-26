# src/api/routers/applications.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime

from src.core.database import get_db
from src.api.models.schema import JobApplication, ApplicationNote
from src.api.models.schemas import (
   JobApplicationCreate,
   JobApplicationUpdate,
   JobApplicationResponse,
   ApplicationNoteCreate,
   ApplicationNoteResponse,
   ApplicationStatusEnum
)
from src.api.dependencies import get_current_active_user, get_verified_user
from src.api.models.auth import User

router = APIRouter(tags=["applications"])


@router.get("/stats/summary")
async def get_application_stats(
   current_user: User = Depends(get_current_active_user),
   db: AsyncSession = Depends(get_db)
):
   """Get summary statistics of applications for current user"""
   # Count by status
   status_counts = await db.execute(
       select(
           JobApplication.status,
           func.count(JobApplication.id).label("count")
       ).where(
           JobApplication.user_id == current_user.id
       ).group_by(JobApplication.status)
   )
   
   # Total applications
   total = await db.execute(
       select(func.count(JobApplication.id)).where(
           JobApplication.user_id == current_user.id
       )
   )
   
   # Applications this week
   from datetime import datetime, timedelta
   week_ago = datetime.utcnow() - timedelta(days=7)
   
   recent = await db.execute(
       select(func.count(JobApplication.id)).where(
           JobApplication.user_id == current_user.id,
           JobApplication.discovered_at >= week_ago
       )
   )
   
   return {
       "total_applications": total.scalar(),
       "applications_this_week": recent.scalar(),
       "by_status": {row.status: row.count for row in status_counts}
   }


@router.post("/", response_model=JobApplicationResponse)
async def create_application(
   application: JobApplicationCreate,
   current_user: User = Depends(get_verified_user),
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
       user_id=current_user.id
   )
   db.add(db_application)
   
   # Update user's application count
   current_user.applications_count += 1
   
   await db.commit()
   await db.refresh(db_application)
   return db_application


@router.get("/", response_model=List[JobApplicationResponse])
async def list_applications(
   skip: int = Query(0, ge=0),
   limit: int = Query(20, ge=1, le=100),
   status: Optional[ApplicationStatusEnum] = None,
   company: Optional[str] = None,
   current_user: User = Depends(get_current_active_user),
   db: AsyncSession = Depends(get_db)
):
   """List all job applications for current user with optional filtering"""
   query = select(JobApplication).where(JobApplication.user_id == current_user.id)
   
   if status:
       query = query.where(JobApplication.status == status)
   if company:
       query = query.where(JobApplication.company.ilike(f"%{company}%"))
   
   query = query.offset(skip).limit(limit).order_by(JobApplication.discovered_at.desc())
   
   result = await db.execute(query)
   return result.scalars().all()


@router.get("/{application_id}", response_model=JobApplicationResponse)
async def get_application(
   application_id: int,
   current_user: User = Depends(get_current_active_user),
   db: AsyncSession = Depends(get_db)
):
   """Get a specific job application"""
   result = await db.execute(
       select(JobApplication).where(
           JobApplication.id == application_id,
           JobApplication.user_id == current_user.id
       )
   )
   application = result.scalar_one_or_none()
   
   if not application:
       raise HTTPException(status_code=404, detail="Application not found")
   
   return application


@router.patch("/{application_id}", response_model=JobApplicationResponse)
async def update_application(
   application_id: int,
   application_update: JobApplicationUpdate,
   current_user: User = Depends(get_current_active_user),
   db: AsyncSession = Depends(get_db)
):
   """Update a job application"""
   result = await db.execute(
       select(JobApplication).where(
           JobApplication.id == application_id,
           JobApplication.user_id == current_user.id
       )
   )
   application = result.scalar_one_or_none()
   
   if not application:
       raise HTTPException(status_code=404, detail="Application not found")
   
   # Update fields
   update_data = application_update.model_dump(exclude_unset=True)
   for field, value in update_data.items():
       setattr(application, field, value)
   
   # Set applied_at if status changed to applied
   if application_update.status == ApplicationStatusEnum.APPLIED and not application.applied_at:
       application.applied_at = datetime.utcnow()
   
   await db.commit()
   await db.refresh(application)
   return application


@router.delete("/{application_id}")
async def delete_application(
   application_id: int,
   current_user: User = Depends(get_current_active_user),
   db: AsyncSession = Depends(get_db)
):
   """Delete a job application"""
   result = await db.execute(
       select(JobApplication).where(
           JobApplication.id == application_id,
           JobApplication.user_id == current_user.id
       )
   )
   application = result.scalar_one_or_none()
   
   if not application:
       raise HTTPException(status_code=404, detail="Application not found")
   
   await db.delete(application)
   
   # Update user's application count
   current_user.applications_count -= 1
   
   await db.commit()
   return {"message": "Application deleted successfully"}


@router.post("/{application_id}/notes", response_model=ApplicationNoteResponse)
async def add_note(
   application_id: int,
   note: ApplicationNoteCreate,
   current_user: User = Depends(get_current_active_user),
   db: AsyncSession = Depends(get_db)
):
   """Add a note to an application"""
   # Verify application exists and belongs to user
   result = await db.execute(
       select(JobApplication).where(
           JobApplication.id == application_id,
           JobApplication.user_id == current_user.id
       )
   )
   if not result.scalar_one_or_none():
       raise HTTPException(status_code=404, detail="Application not found")
   
   db_note = ApplicationNote(
       application_id=application_id,
       note=note.note,
       user_id=current_user.id
   )
   db.add(db_note)
   await db.commit()
   await db.refresh(db_note)
   return db_note
