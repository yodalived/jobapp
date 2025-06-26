import os
import shutil
import aiofiles
from pathlib import Path
from typing import BinaryIO, Optional, List, Dict, Any
from datetime import datetime
import io
from . import StorageBackend

class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend for development"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_full_path(self, key: str) -> Path:
        """Get full filesystem path for a key"""
        return self.base_path / key
    
    async def upload(self, key: str, file: BinaryIO, metadata: Optional[Dict[str, str]] = None) -> str:
        """Upload a file to local storage"""
        try:
            full_path = self._get_full_path(key)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            file.seek(0)
            async with aiofiles.open(full_path, 'wb') as f:
                await f.write(file.read())
            
            # Write metadata if provided
            if metadata:
                meta_path = full_path.with_suffix(full_path.suffix + '.meta')
                async with aiofiles.open(meta_path, 'w') as f:
                    import json
                    await f.write(json.dumps(metadata))
            
            return f"file://{full_path}"
        except Exception as e:
            raise Exception(f"Failed to upload file: {str(e)}")
    
    async def download(self, key: str) -> BinaryIO:
        """Download a file from local storage"""
        try:
            full_path = self._get_full_path(key)
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {key}")
            
            async with aiofiles.open(full_path, 'rb') as f:
                content = await f.read()
                return io.BytesIO(content)
        except Exception as e:
            raise Exception(f"Failed to download file: {str(e)}")
    
    async def delete(self, key: str) -> bool:
        """Delete a file from local storage"""
        try:
            full_path = self._get_full_path(key)
            if full_path.exists():
                full_path.unlink()
                
                # Delete metadata if exists
                meta_path = full_path.with_suffix(full_path.suffix + '.meta')
                if meta_path.exists():
                    meta_path.unlink()
                
                return True
            return False
        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")
    
    async def exists(self, key: str) -> bool:
        """Check if a file exists"""
        return self._get_full_path(key).exists()
    
    async def list_files(self, prefix: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """List files with optional prefix"""
        try:
            path = self.base_path / prefix if prefix else self.base_path
            files = []
            count = 0
            
            for file_path in path.rglob('*'):
                if file_path.is_file() and not file_path.suffix == '.meta':
                    if count >= limit:
                        break
                    
                    stat = file_path.stat()
                    files.append({
                        'key': str(file_path.relative_to(self.base_path)),
                        'size': stat.st_size,
                        'last_modified': datetime.fromtimestamp(stat.st_mtime),
                        'etag': None
                    })
                    count += 1
            
            return files
        except Exception as e:
            raise Exception(f"Failed to list files: {str(e)}")
    
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a URL for local file access"""
        # For local storage, just return the file path
        # In production, you might implement a temporary link system
        full_path = self._get_full_path(key)
        return f"file://{full_path}"

