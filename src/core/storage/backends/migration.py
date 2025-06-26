"""
Storage migration utilities
"""

from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
import logging

from .base import StorageBackend, FileMetadata
# TODO: Implement proper database models for file tracking
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select

logger = logging.getLogger(__name__)


class StorageMigrator:
    """Handle migrations between storage backends"""
    
    def __init__(
        self,
        source_backend: StorageBackend,
        target_backend: StorageBackend,
        db_session_factory=None
    ):
        self.source = source_backend
        self.target = target_backend
        self.db_session_factory = db_session_factory
    
    async def migrate_file(
        self,
        key: str,
        delete_source: bool = False
    ) -> Dict[str, Any]:
        """Migrate a single file between backends"""
        try:
            # Check if file exists in source
            if not await self.source.exists(key):
                raise ValueError(f"File {key} not found in source backend")
            
            # Get file from source
            logger.info(f"Migrating {key} from {self.source.name} to {self.target.name}")
            file_data = await self.source.retrieve(key)
            
            # Get metadata from source
            source_metadata = await self.source.get_metadata(key)
            metadata = source_metadata.custom_metadata if source_metadata else None
            
            # Save to target
            result = await self.target.save(key, file_data, metadata)
            
            # Delete from source if requested
            if delete_source:
                await self.source.delete(key)
                logger.info(f"Deleted {key} from source")
            
            return {
                "key": key,
                "status": "success",
                "source_backend": self.source.name,
                "target_backend": self.target.name,
                "deleted_source": delete_source
            }
        
        except Exception as e:
            logger.error(f"Failed to migrate {key}: {str(e)}")
            return {
                "key": key,
                "status": "failed",
                "error": str(e)
            }
    
    async def migrate_batch(
        self,
        keys: List[str],
        delete_source: bool = False,
        parallel: int = 5
    ) -> Dict[str, Any]:
        """Migrate multiple files in parallel"""
        results = []
        
        # Process in batches
        for i in range(0, len(keys), parallel):
            batch = keys[i:i + parallel]
            
            tasks = [
                self.migrate_file(key, delete_source)
                for key in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({
                        "key": "unknown",
                        "status": "failed",
                        "error": str(result)
                    })
                else:
                    results.append(result)
        
        # Summarize results
        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "failed"]
        
        return {
            "total": len(keys),
            "successful": len(successful),
            "failed": len(failed),
            "results": results
        }
    
    async def migrate_all(
        self,
        filter_criteria: Optional[Dict[str, Any]] = None,
        delete_source: bool = False,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """Migrate all files from source to target backend"""
        # List all files in source backend
        source_files = await self.source.list_files()
        
        # Apply filters if provided
        keys_to_migrate = []
        for file_meta in source_files:
            if filter_criteria:
                # Simple filtering by prefix
                if "prefix" in filter_criteria:
                    if not file_meta.key.startswith(filter_criteria["prefix"]):
                        continue
                # Could add more filter criteria here
            keys_to_migrate.append(file_meta.key)
        
        logger.info(f"Starting migration of {len(keys_to_migrate)} files")
        
        # Migrate in batches
        all_results = []
        for i in range(0, len(keys_to_migrate), batch_size):
            batch = keys_to_migrate[i:i + batch_size]
            logger.info(f"Migrating batch {i//batch_size + 1}/{(len(keys_to_migrate) + batch_size - 1)//batch_size}")
            
            batch_results = await self.migrate_batch(
                batch,
                delete_source=delete_source
            )
            all_results.append(batch_results)
        
        # Aggregate results
        total_successful = sum(r["successful"] for r in all_results)
        total_failed = sum(r["failed"] for r in all_results)
        
        return {
            "total_files": len(keys_to_migrate),
            "total_successful": total_successful,
            "total_failed": total_failed,
            "batches": len(all_results),
            "batch_results": all_results
        }
