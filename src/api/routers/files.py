# src/api/routers/files.py
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import io

from src.core.database import get_db
from src.api.dependencies import get_current_active_user
from src.api.models.auth import User
from src.services.file_service import FileService
from src.core.config import settings

router = APIRouter()

@router.post("/upload/resume")
async def upload_resume(
    file: UploadFile = File(...),
    job_application_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a resume file"""
    # Validate file type
    if not any(file.filename.endswith(ext) for ext in settings.allowed_file_types):
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {settings.allowed_file_types}"
        )
    
    # Validate file size
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)
    if file_size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
        )
    
    # Reset file pointer
    file_obj = io.BytesIO(contents)
    
    try:
        result = await FileService.upload_resume(
            user_id=current_user.id,
            file=file_obj,
            filename=file.filename,
            job_application_id=job_application_id,
            metadata={
                "content_type": file.content_type,
                "size": str(len(contents))
            }
        )
        
        return {
            "success": True,
            "file": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/list")
async def list_files(
    file_type: Optional[str] = Query(None, description="Filter by file type (resumes, uploads, etc)"),
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """List user's files"""
    try:
        files = await FileService.get_user_files(
            user_id=current_user.id,
            file_type=file_type,
            limit=limit
        )
        
        return {
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@router.get("/download-url/{file_key:path}")
async def get_download_url(
    file_key: str,
    expires_in: int = Query(3600, description="URL expiration time in seconds"),
    current_user: User = Depends(get_current_active_user)
):
    """Get a temporary download URL for a file"""
    try:
        url = await FileService.get_download_url(
            user_id=current_user.id,
            key=file_key,
            expires_in=expires_in
        )
        
        return {
            "url": url,
            "expires_in": expires_in
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate URL: {str(e)}")

@router.delete("/{file_key:path}")
async def delete_file(
    file_key: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a file"""
    try:
        success = await FileService.delete_file(
            user_id=current_user.id,
            key=file_key
        )
        
        return {
            "success": success,
            "message": "File deleted successfully" if success else "File not found"
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")
