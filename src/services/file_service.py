# src/services/file_service.py
from typing import BinaryIO, Optional, Dict, Any, List
import io
from fastapi import UploadFile

from src.services.storage_service import storage


class FileService:
    """
    High-level file service that uses the storage service.
    Provides specific functionality for the file management API.
    """
    
    @staticmethod
    async def upload_resume(
        user_id: int,
        file: BinaryIO,
        filename: str,
        job_application_id: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Upload a resume file"""
        if metadata is None:
            metadata = {}
        
        # Add specific metadata for resumes
        metadata.update({
            "file_type": "resume",
            "job_application_id": str(job_application_id) if job_application_id else None
        })
        
        # Save using storage service
        file_key = await storage.save(file, filename, user_id, metadata)
        
        return {
            "key": file_key,
            "filename": filename,
            "file_type": "resume",
            "job_application_id": job_application_id
        }
    
    @staticmethod
    async def get_user_files(
        user_id: int,
        file_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get list of user's files"""
        # For now, return a simple structure
        # In a real implementation, you'd query a database of file metadata
        # Since we don't have that yet, return an empty list
        return []
    
    @staticmethod
    async def get_download_url(
        user_id: int,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Get a temporary download URL for a file"""
        return await storage.get_download_url(key, user_id, expires_in)
    
    @staticmethod
    async def delete_file(user_id: int, key: str) -> bool:
        """Delete a file"""
        return await storage.delete(key, user_id)