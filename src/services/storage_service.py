"""
Super simple storage service for application use.
The application doesn't need to know about backends, migrations, or any complexity.
"""

from typing import BinaryIO, Optional, Dict, Any, Union
import io
from fastapi import UploadFile

from src.core.storage.manager import StorageManager


class SimpleStorageService:
    """
    Dead simple interface for the application.
    Just save and retrieve - nothing else matters.
    """
    
    def __init__(self):
        self.manager = StorageManager()
    
    async def save(
        self,
        file: Union[UploadFile, BinaryIO, bytes],
        filename: str,
        user_id: int,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Save any file. Returns a unique file ID.
        
        That's it. The storage layer handles everything else.
        """
        # Convert to BinaryIO if needed
        if isinstance(file, UploadFile):
            content = await file.read()
            file_obj = io.BytesIO(content)
        elif isinstance(file, bytes):
            file_obj = io.BytesIO(file)
        else:
            file_obj = file
        
        # Generate storage key (backend decides the actual storage path)
        key = f"users/{user_id}/{filename}"
        
        # Add user context to metadata
        if metadata is None:
            metadata = {}
        metadata['user_id'] = str(user_id)
        metadata['original_filename'] = filename
        
        # Save using the storage manager
        result = await self.manager.save(key, file_obj, metadata)
        
        # Return just the key as the file ID
        return key
    
    async def retrieve(self, file_id: str, user_id: int) -> BinaryIO:
        """
        Get a file by ID.
        
        The storage layer knows where it is and how to get it.
        """
        # Verify user owns this file (simple check)
        if not file_id.startswith(f"users/{user_id}/"):
            raise PermissionError("Access denied")
        
        return await self.manager.retrieve(file_id)
    
    async def delete(self, file_id: str, user_id: int) -> bool:
        """Delete a file."""
        # Verify user owns this file
        if not file_id.startswith(f"users/{user_id}/"):
            raise PermissionError("Access denied")
        
        return await self.manager.delete(file_id)
    
    async def get_download_url(
        self,
        file_id: str,
        user_id: int,
        expires_in: int = 3600
    ) -> str:
        """Get a temporary download URL."""
        # Verify user owns this file
        if not file_id.startswith(f"users/{user_id}/"):
            raise PermissionError("Access denied")
        
        return await self.manager.get_url(file_id, expires_in)


# Global instance
storage = SimpleStorageService()


# Example usage in your application:
"""
# In your resume generator:
async def generate_resume(user_id: int, job_data: dict):
    # Generate PDF
    pdf_content = await create_pdf(job_data)
    
    # Save it - that's all!
    file_id = await storage.save(
        file=pdf_content,
        filename=f"resume_{job_data['id']}.pdf",
        user_id=user_id,
        metadata={"job_id": str(job_data['id'])}
    )
    
    return file_id


# In your API endpoint:
@router.post("/upload")
async def upload_file(
    file: UploadFile,
    current_user: User = Depends(get_current_user)
):
    # Just save it
    file_id = await storage.save(
        file=file,
        filename=file.filename,
        user_id=current_user.id
    )
    
    return {"file_id": file_id}


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user)
):
    # Just get the URL
    url = await storage.get_download_url(
        file_id=file_id,
        user_id=current_user.id
    )
    
    return {"download_url": url}
"""


# Configuration examples for different environments:
"""
# Development (local files):
BACKENDS_CONFIG = {
    "local": {
        "type": "local",
        "base_path": "./storage"
    }
}
PRIMARY_BACKEND = "local"


# Testing (MinIO):
BACKENDS_CONFIG = {
    "minio": {
        "type": "minio",
        "endpoint_url": "http://localhost:9000",
        "access_key": "minioadmin",
        "secret_key": "minioadmin",
        "bucket_name": "test-bucket"
    }
}
PRIMARY_BACKEND = "minio"


# Production (Multiple backends):
BACKENDS_CONFIG = {
    "aws_hot": {
        "type": "aws_s3",
        "bucket_name": "myapp-hot",
        "region": "us-east-1",
        "storage_class": "STANDARD"
    },
    "aws_cold": {
        "type": "aws_s3", 
        "bucket_name": "myapp-archive",
        "region": "us-east-1",
        "storage_class": "GLACIER"
    },
    "azure_backup": {
        "type": "azure_blob",
        "container_name": "backup",
        "tier": "Archive"
    }
}
PRIMARY_BACKEND = "aws_hot"


# When migrating:
async def migrate_to_new_backend():
    # This runs separately from your app
    migrator = storage.manager.create_migrator(
        source_backend="minio",
        target_backend="aws_hot",
        db_session_factory=get_db
    )
    
    # Migrate everything
    results = await migrator.migrate_all(
        filter_criteria={"file_type": "resume"},
        delete_source=True
    )
    
    print(f"Migrated {results['total_successful']} files")
"""
