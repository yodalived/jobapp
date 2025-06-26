"""
Local filesystem backend for development
"""

import os
from pathlib import Path
from typing import BinaryIO, Optional, List, Dict, Any
from datetime import datetime
import io
import json

from .base import StorageBackend, BackendConfig, BackendCapability, FileMetadata


class LocalBackend(StorageBackend):
    """Local filesystem storage backend"""
    
    @classmethod
    def create_config(
        cls,
        name: str,
        base_path: str
    ) -> BackendConfig:
        """Create a local backend configuration"""
        return BackendConfig(
            name=name,
            backend_type="local",
            capabilities=[
                BackendCapability.VERSIONING,  # Through file naming
                BackendCapability.TAGGING,     # Through metadata files
            ],
            config={
                "base_path": base_path
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize the backend"""
        try:
            if "base_path" not in self.config.config:
                raise ValueError("Missing required config field: base_path")
            
            self.base_path = Path(self.config.config["base_path"])
            self.base_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for organization
            (self.base_path / "data").mkdir(exist_ok=True)
            (self.base_path / "metadata").mkdir(exist_ok=True)
            (self.base_path / "versions").mkdir(exist_ok=True)
            
            self._initialized = True
            return True
        except Exception:
            return False
    
    async def health_check(self) -> bool:
        """Check if the backend is healthy"""
        try:
            return self.base_path.exists() and self.base_path.is_dir()
        except Exception:
            return False
    
    def _get_paths(self, key: str) -> Dict[str, Path]:
        """Get all paths for a given key"""
        safe_key = key.replace("/", "_")
        return {
            "data": self.base_path / "data" / safe_key,
            "metadata": self.base_path / "metadata" / f"{safe_key}.json",
            "versions": self.base_path / "versions" / safe_key
        }
    
    async def save(self, key: str, file: BinaryIO, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Upload file to local storage"""
        try:
            paths = self._get_paths(key)
            
            # Create version if file exists
            if paths["data"].exists():
                version_dir = paths["versions"]
                version_dir.mkdir(exist_ok=True)
                version_file = version_dir / f"{datetime.utcnow().timestamp()}"
                paths["data"].rename(version_file)
            
            # Write file
            file.seek(0)
            with open(paths["data"], 'wb') as f:
                f.write(file.read())
            
            # Write metadata
            file_metadata = {
                "key": key,
                "size": paths["data"].stat().st_size,
                "created_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
                "backend": self.name
            }
            
            with open(paths["metadata"], 'w') as f:
                f.write(json.dumps(file_metadata, indent=2))
            
            return file_metadata
        
        except Exception as e:
            raise Exception(f"Local upload failed: {str(e)}")
    
    async def retrieve(self, key: str) -> BinaryIO:
        """Download file from local storage"""
        try:
            paths = self._get_paths(key)
            
            if not paths["data"].exists():
                raise FileNotFoundError(f"File not found: {key}")
            
            with open(paths["data"], 'rb') as f:
                content = f.read()
                return io.BytesIO(content)
        
        except Exception as e:
            raise Exception(f"Local download failed: {str(e)}")
    
    async def delete(self, key: str) -> bool:
        """Delete file from local storage"""
        try:
            paths = self._get_paths(key)
            
            # Move to versions before deleting
            if paths["data"].exists():
                version_dir = paths["versions"]
                version_dir.mkdir(exist_ok=True)
                version_file = version_dir / f"deleted_{datetime.utcnow().timestamp()}"
                paths["data"].rename(version_file)
                
                # Mark as deleted in metadata
                if paths["metadata"].exists():
                    with open(paths["metadata"], 'r') as f:
                        metadata = json.loads(f.read())
                    
                    metadata["deleted"] = True
                    metadata["deleted_at"] = datetime.utcnow().isoformat()
                    
                    with open(paths["metadata"], 'w') as f:
                        f.write(json.dumps(metadata, indent=2))
                
                return True
            
            return False
        
        except Exception as e:
            raise Exception(f"Local delete failed: {str(e)}")
    
    async def exists(self, key: str) -> bool:
        """Check if file exists"""
        paths = self._get_paths(key)
        return paths["data"].exists()
    
    async def list_files(self, prefix: Optional[str] = None, limit: Optional[int] = None) -> List[FileMetadata]:
        """List files in local storage"""
        try:
            files = []
            count = 0
            max_files = limit or 1000
            
            for file_path in (self.base_path / "data").iterdir():
                if count >= max_files:
                    break
                
                if file_path.is_file():
                    # Reconstruct key from filename
                    key = file_path.name.replace("_", "/")
                    
                    if prefix and not key.startswith(prefix):
                        continue
                    
                    # Get metadata for this file
                    file_metadata = await self.get_metadata(key)
                    if file_metadata:
                        files.append(file_metadata)
                    
                    count += 1
            
            return files
        
        except Exception as e:
            raise Exception(f"Local list failed: {str(e)}")
    
    async def get_metadata(self, key: str) -> Optional[FileMetadata]:
        """Get file metadata"""
        try:
            paths = self._get_paths(key)
            
            if not paths["data"].exists():
                return None
            
            # Load metadata file
            custom_metadata = None
            if paths["metadata"].exists():
                with open(paths["metadata"], 'r') as f:
                    metadata_dict = json.loads(f.read())
                    custom_metadata = metadata_dict.get("metadata", {})
            
            # Generate basic metadata from file stats
            stat = paths["data"].stat()
            return FileMetadata(
                key=key,
                size=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                custom_metadata=custom_metadata
            )
        
        except Exception:
            return None
    
    async def update_metadata(self, key: str, metadata: Dict[str, str]) -> bool:
        """Update file metadata"""
        try:
            paths = self._get_paths(key)
            
            # Load existing metadata
            if paths["metadata"].exists():
                with open(paths["metadata"], 'r') as f:
                    existing = json.loads(f.read())
            else:
                existing = {"metadata": {}}
            
            existing["metadata"].update(metadata)
            existing["updated_at"] = datetime.utcnow().isoformat()
            
            # Write updated metadata
            with open(paths["metadata"], 'w') as f:
                f.write(json.dumps(existing, indent=2))
            
            return True
        
        except Exception as e:
            raise Exception(f"Failed to update metadata: {str(e)}")
    
    async def get_url(self, key: str, expires_in: int = 3600, method: str = "GET") -> str:
        """
        Generate a local file URL. For local backend, this just returns a file path.
        In a real deployment, this might be a served URL through the API.
        """
        # For local development, we could return a path or API endpoint
        # In practice, local files would be served through the API
        return f"/api/v1/files/{key}"
    
    # Local-specific methods
    
    async def get_versions(self, key: str) -> List[Dict[str, Any]]:
        """Get all versions of a file"""
        paths = self._get_paths(key)
        versions = []
        
        if paths["versions"].exists():
            for version_file in paths["versions"].iterdir():
                if version_file.is_file():
                    stat = version_file.stat()
                    versions.append({
                        "version": version_file.name,
                        "size": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
        
        return sorted(versions, key=lambda v: v["created_at"], reverse=True)
