from typing import Optional
from . import StorageBackend
from .s3 import S3StorageBackend
from .local import LocalStorageBackend
from ..config import settings

class StorageFactory:
    """Factory for creating storage backends"""
    
    @staticmethod
    def create_backend(backend_type: Optional[str] = None) -> StorageBackend:
        """Create a storage backend based on configuration"""
        
        backend_type = backend_type or settings.storage_backend
        
        if backend_type == "s3" or backend_type == "minio":
            return S3StorageBackend(
                endpoint_url=settings.s3_endpoint_url,
                access_key_id=settings.s3_access_key_id,
                secret_access_key=settings.s3_secret_access_key,
                bucket_name=settings.s3_bucket_name,
                region=settings.s3_region,
                secure=settings.s3_secure
            )
        elif backend_type == "local":
            return LocalStorageBackend(
                base_path=settings.local_storage_path
            )
        # Add more backends here (Azure, GCS, etc.)
        else:
            raise ValueError(f"Unknown storage backend: {backend_type}")

# Singleton instance
storage = StorageFactory.create_backend()
