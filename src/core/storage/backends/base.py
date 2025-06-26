"""
Base classes for storage backends
"""

from abc import ABC, abstractmethod
from typing import BinaryIO, Optional, List, Dict, Any, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class BackendCapability(Enum):
    """Capabilities that storage backends can support"""
    VERSIONING = "versioning"
    ENCRYPTION = "encryption"
    COMPRESSION = "compression"
    REPLICATION = "replication"
    LIFECYCLE_MANAGEMENT = "lifecycle_management"
    PRESIGNED_URLS = "presigned_urls"
    METADATA = "metadata"
    TAGGING = "tagging"


@dataclass
class BackendConfig:
    """Configuration for a storage backend"""
    name: str
    backend_type: str
    capabilities: List[BackendCapability]
    config: Dict[str, Any]
    priority: int = 0
    health_check_url: Optional[str] = None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        return self.config.get(key, default)


@dataclass
class FileMetadata:
    """Metadata for a stored file"""
    key: str
    size: int
    content_type: Optional[str] = None
    last_modified: Optional[datetime] = None
    etag: Optional[str] = None
    version_id: Optional[str] = None
    custom_metadata: Optional[Dict[str, str]] = None


class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    def __init__(self, config: BackendConfig):
        self.config = config
        self.name = config.name
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the backend (connect, create buckets, etc.)"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the backend is healthy and accessible"""
        pass
    
    @abstractmethod
    async def save(
        self,
        key: str,
        file: BinaryIO,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Save a file to the backend
        
        Args:
            key: Unique identifier for the file
            file: File-like object to save
            metadata: Optional metadata to store with the file
            
        Returns:
            Dict containing save result info (backend-specific)
        """
        pass
    
    @abstractmethod
    async def retrieve(self, key: str) -> BinaryIO:
        """
        Retrieve a file from the backend
        
        Args:
            key: Unique identifier for the file
            
        Returns:
            File-like object containing the file data
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a file from the backend
        
        Args:
            key: Unique identifier for the file
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a file exists in the backend
        
        Args:
            key: Unique identifier for the file
            
        Returns:
            True if file exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_metadata(self, key: str) -> Optional[FileMetadata]:
        """
        Get metadata for a file
        
        Args:
            key: Unique identifier for the file
            
        Returns:
            FileMetadata object if file exists, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_files(
        self,
        prefix: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[FileMetadata]:
        """
        List files in the backend
        
        Args:
            prefix: Optional prefix to filter files
            limit: Optional limit on number of files to return
            
        Returns:
            List of FileMetadata objects
        """
        pass
    
    async def get_url(
        self,
        key: str,
        expires_in: int = 3600,
        method: str = "GET"
    ) -> str:
        """
        Get a presigned URL for accessing a file (if supported)
        
        Args:
            key: Unique identifier for the file
            expires_in: URL expiration time in seconds
            method: HTTP method (GET, PUT, etc.)
            
        Returns:
            Presigned URL string
            
        Raises:
            NotImplementedError: If backend doesn't support presigned URLs
        """
        if BackendCapability.PRESIGNED_URLS not in self.config.capabilities:
            raise NotImplementedError(f"Backend {self.name} doesn't support presigned URLs")
        
        # Subclasses should override this method
        raise NotImplementedError("get_url method not implemented")

    async def get_download_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """
        Convenience method that matches the README interface.
        Calls get_url with GET method.
        """
        return await self.get_url(key, expires_in, "GET")
    
    async def copy(self, source_key: str, dest_key: str) -> bool:
        """
        Copy a file within the backend (if supported)
        
        Args:
            source_key: Source file identifier
            dest_key: Destination file identifier
            
        Returns:
            True if copied successfully, False otherwise
        """
        # Default implementation using retrieve + save
        try:
            file_data = await self.retrieve(source_key)
            metadata = await self.get_metadata(source_key)
            custom_metadata = metadata.custom_metadata if metadata else None
            
            await self.save(dest_key, file_data, custom_metadata)
            return True
        except Exception:
            return False
    
    def has_capability(self, capability: BackendCapability) -> bool:
        """Check if backend has a specific capability"""
        return capability in self.config.capabilities
    
    @classmethod
    @abstractmethod
    def create_config(cls, name: str, **kwargs) -> BackendConfig:
        """Create a configuration object for this backend type"""
        pass
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', type='{self.config.backend_type}')"


class StorageError(Exception):
    """Base exception for storage operations"""
    pass


class BackendNotAvailableError(StorageError):
    """Raised when a backend is not available or healthy"""
    pass


class FileNotFoundError(StorageError):
    """Raised when a requested file is not found"""
    pass


class ConfigurationError(StorageError):
    """Raised when backend configuration is invalid"""
    pass