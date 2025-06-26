from typing import BinaryIO, Optional, Dict, Any, List
from datetime import datetime
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.storage.factory import storage
from src.api.models.auth import User

class FileService:
    """Service for handling file operations with proper isolation"""
    
    @staticmethod
    def generate_key(user_id: int, file_type: str, filename: str) -> str:
        """Generate a unique storage key for a file"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid4())[:8]
        safe_filename = filename.replace(" ", "_").replace("/", "_")
        
        return f"users/{user_id}/{file_type}/{timestamp}_{unique_id}_{safe_filename}"
    
    @staticmethod
    async def upload_resume(
        user_id: int,
        file: BinaryIO,
        filename: str,
        job_application_id: Optional[int] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Upload a resume file"""
        key = FileService.generate_key(user_id, "resumes", filename)
        
        # Add metadata
        if metadata is None:
            metadata = {}
        metadata.update({
            "user_id": str(user_id),
            "upload_time": datetime.utcnow().isoformat(),
            "original_filename": filename,
            "file_type": "resume"
        })
        
        if job_application_id:
            metadata["job_application_id"] = str(job_application_id)
        
        # Upload to storage
        storage_url = await storage.upload(key, file, metadata)
        
        return {
            "key": key,
            "storage_url": storage_url,
            "filename": filename,
            "uploaded_at": datetime.utcnow()
        }
    
    @staticmethod
    async def get_user_files(
        user_id: int,
        file_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all files for a user"""
        prefix = f"users/{user_id}/"
        if file_type:
            prefix += f"{file_type}/"
        
        files = await storage.list_files(prefix, limit)
        return files
    
    @staticmethod
    async def get_download_url(
        user_id: int,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Get a temporary download URL for a file"""
        # Verify the key belongs to the user
        if not key.startswith(f"users/{user_id}/"):
            raise PermissionError("Access denied to this file")
        
        return await storage.get_presigned_url(key, expires_in)
    
    @staticmethod
    async def delete_file(user_id: int, key: str) -> bool:
        """Delete a file"""
        # Verify the key belongs to the user
        if not key.startswith(f"users/{user_id}/"):
            raise PermissionError("Access denied to this file")
        
        return await storage.delete(key)
