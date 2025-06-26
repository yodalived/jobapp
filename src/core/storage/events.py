"""
Storage event definitions and integration
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import asyncio
from abc import ABC, abstractmethod


class StorageEventType(Enum):
    """Types of storage events"""
    # File lifecycle events
    FILE_UPLOADED = "file.uploaded"
    FILE_DOWNLOADED = "file.downloaded"
    FILE_DELETED = "file.deleted"
    FILE_UPDATED = "file.updated"
    
    # Storage operations
    FILE_MIGRATED = "file.migrated"
    FILE_COMPRESSED = "file.compressed"
    FILE_TIER_CHANGED = "file.tier_changed"
    FILE_EXPIRED = "file.expired"
    
    # Access events
    FILE_ACCESS_DENIED = "file.access_denied"
    FILE_URL_GENERATED = "file.url_generated"
    
    # Error events
    UPLOAD_FAILED = "upload.failed"
    DOWNLOAD_FAILED = "download.failed"
    MIGRATION_FAILED = "migration.failed"
    
    # Analytics events
    STORAGE_QUOTA_WARNING = "storage.quota_warning"
    STORAGE_QUOTA_EXCEEDED = "storage.quota_exceeded"


@dataclass
class StorageEvent:
    """Storage event data structure"""
    event_type: StorageEventType
    timestamp: datetime
    user_id: Optional[int]
    file_id: Optional[str]
    backend: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


class EventHandler(ABC):
    """Abstract base class for event handlers"""
    
    @abstractmethod
    async def handle(self, event: StorageEvent) -> None:
        """Handle a storage event"""
        pass
    
    @abstractmethod
    def can_handle(self, event_type: StorageEventType) -> bool:
        """Check if this handler can handle the event type"""
        pass


class StorageEventBus:
    """Event bus for storage events"""
    
    def __init__(self):
        self._handlers: Dict[StorageEventType, List[EventHandler]] = {}
        self._async_handlers: Dict[StorageEventType, List[EventHandler]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
    
    def register_handler(
        self,
        event_type: StorageEventType,
        handler: EventHandler,
        async_processing: bool = True
    ):
        """Register an event handler"""
        if async_processing:
            if event_type not in self._async_handlers:
                self._async_handlers[event_type] = []
            self._async_handlers[event_type].append(handler)
        else:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
    
    async def emit(self, event: StorageEvent):
        """Emit a storage event"""
        # Handle synchronous handlers immediately
        sync_handlers = self._handlers.get(event.event_type, [])
        for handler in sync_handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                # Log error but don't stop processing
                print(f"Handler error: {e}")
        
        # Queue async handlers
        async_handlers = self._async_handlers.get(event.event_type, [])
        if async_handlers:
            await self._event_queue.put((event, async_handlers))
    
    async def start_processing(self):
        """Start processing async events"""
        self._running = True
        while self._running:
            try:
                event, handlers = await asyncio.wait_for(
                    self._event_queue.get(), timeout=1.0
                )
                
                # Process handlers concurrently
                tasks = [handler.handle(event) for handler in handlers]
                await asyncio.gather(*tasks, return_exceptions=True)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Event processing error: {e}")
    
    def stop_processing(self):
        """Stop processing events"""
        self._running = False


# Event-aware storage manager
class EventAwareStorageManager:
    """Storage manager with event emission"""
    
    def __init__(self, storage_manager, event_bus: StorageEventBus):
        self._storage = storage_manager
        self._event_bus = event_bus
    
    async def save(
        self,
        file: Any,
        filename: str,
        user_id: int,
        metadata: Optional[Dict[str, str]] = None
    ) -> str:
        """Save file with event emission"""
        start_time = datetime.utcnow()
        
        try:
            # Perform the save
            file_id = await self._storage.save(file, filename, user_id, metadata)
            
            # Emit success event
            await self._event_bus.emit(StorageEvent(
                event_type=StorageEventType.FILE_UPLOADED,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                file_id=file_id,
                backend=self._storage.manager._primary_backend,
                metadata={
                    "filename": filename,
                    "size": len(file.read()) if hasattr(file, 'read') else 0,
                    "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000,
                    "custom_metadata": metadata
                }
            ))
            
            return file_id
            
        except Exception as e:
            # Emit failure event
            await self._event_bus.emit(StorageEvent(
                event_type=StorageEventType.UPLOAD_FAILED,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                file_id=None,
                backend=self._storage.manager._primary_backend,
                metadata={
                    "filename": filename,
                    "error": str(e),
                    "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
                }
            ))
            raise
    
    async def retrieve(self, file_id: str, user_id: int) -> Any:
        """Retrieve file with event emission"""
        start_time = datetime.utcnow()
        
        try:
            # Perform the retrieval
            file = await self._storage.retrieve(file_id, user_id)
            
            # Emit download event
            await self._event_bus.emit(StorageEvent(
                event_type=StorageEventType.FILE_DOWNLOADED,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                file_id=file_id,
                backend=self._storage.manager._primary_backend,
                metadata={
                    "duration_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
                }
            ))
            
            return file
            
        except PermissionError:
            # Emit access denied event
            await self._event_bus.emit(StorageEvent(
                event_type=StorageEventType.FILE_ACCESS_DENIED,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                file_id=file_id,
                backend=self._storage.manager._primary_backend,
                metadata={
                    "reason": "User does not own file"
                }
            ))
            raise
        except Exception as e:
            # Emit failure event
            await self._event_bus.emit(StorageEvent(
                event_type=StorageEventType.DOWNLOAD_FAILED,
                timestamp=datetime.utcnow(),
                user_id=user_id,
                file_id=file_id,
                backend=self._storage.manager._primary_backend,
                metadata={
                    "error": str(e)
                }
            ))
            raise


# Example event handlers

class AnalyticsEventHandler(EventHandler):
    """Track storage analytics"""
    
    def __init__(self, analytics_service):
        self.analytics = analytics_service
    
    async def handle(self, event: StorageEvent):
        """Record analytics for storage events"""
        if event.event_type == StorageEventType.FILE_UPLOADED:
            await self.analytics.track_upload(
                user_id=event.user_id,
                file_size=event.metadata.get('size', 0),
                duration=event.metadata.get('duration_ms', 0)
            )
        elif event.event_type == StorageEventType.FILE_DOWNLOADED:
            await self.analytics.track_download(
                user_id=event.user_id,
                file_id=event.file_id
            )
    
    def can_handle(self, event_type: StorageEventType) -> bool:
        return event_type in [
            StorageEventType.FILE_UPLOADED,
            StorageEventType.FILE_DOWNLOADED,
            StorageEventType.FILE_DELETED
        ]


class ResumeProcessingHandler(EventHandler):
    """Handle resume-specific events"""
    
    def __init__(self, resume_service, job_service):
        self.resume_service = resume_service
        self.job_service = job_service
    
    async def handle(self, event: StorageEvent):
        """Process resume uploads"""
        if event.event_type == StorageEventType.FILE_UPLOADED:
            metadata = event.metadata.get('custom_metadata', {})
            
            # If it's a resume upload, trigger processing
            if metadata.get('file_type') == 'resume':
                job_id = metadata.get('job_id')
                if job_id:
                    # Queue resume for job matching
                    await self.job_service.queue_resume_matching(
                        file_id=event.file_id,
                        job_id=job_id,
                        user_id=event.user_id
                    )
                
                # Extract resume content for indexing
                await self.resume_service.index_resume(
                    file_id=event.file_id,
                    user_id=event.user_id
                )
    
    def can_handle(self, event_type: StorageEventType) -> bool:
        return event_type == StorageEventType.FILE_UPLOADED


class QuotaEnforcementHandler(EventHandler):
    """Enforce storage quotas"""
    
    def __init__(self, quota_service, notification_service):
        self.quota_service = quota_service
        self.notification_service = notification_service
    
    async def handle(self, event: StorageEvent):
        """Check and enforce quotas"""
        if event.event_type == StorageEventType.FILE_UPLOADED:
            # Check user's storage usage
            usage = await self.quota_service.get_user_usage(event.user_id)
            quota = await self.quota_service.get_user_quota(event.user_id)
            
            usage_percent = (usage / quota) * 100
            
            if usage_percent >= 90:
                # Emit quota warning
                await self.notification_service.send_quota_warning(
                    user_id=event.user_id,
                    usage_percent=usage_percent
                )
            
            if usage > quota:
                # Delete the file and notify
                await self.quota_service.handle_quota_exceeded(
                    user_id=event.user_id,
                    file_id=event.file_id
                )
    
    def can_handle(self, event_type: StorageEventType) -> bool:
        return event_type == StorageEventType.FILE_UPLOADED


class AuditLogHandler(EventHandler):
    """Log all storage events for audit trail"""
    
    def __init__(self, audit_service):
        self.audit_service = audit_service
    
    async def handle(self, event: StorageEvent):
        """Log event to audit trail"""
        await self.audit_service.log_storage_event(
            event_type=event.event_type.value,
            user_id=event.user_id,
            file_id=event.file_id,
            backend=event.backend,
            timestamp=event.timestamp,
            metadata=event.metadata
        )
    
    def can_handle(self, event_type: StorageEventType) -> bool:
        # Log everything
        return True


# Integration with the application
"""
# In your application startup:

# Create event bus
event_bus = StorageEventBus()

# Register handlers
event_bus.register_handler(
    StorageEventType.FILE_UPLOADED,
    AnalyticsEventHandler(analytics_service)
)

event_bus.register_handler(
    StorageEventType.FILE_UPLOADED,
    ResumeProcessingHandler(resume_service, job_service)
)

event_bus.register_handler(
    StorageEventType.FILE_UPLOADED,
    QuotaEnforcementHandler(quota_service, notification_service)
)

# Audit everything
audit_handler = AuditLogHandler(audit_service)
for event_type in StorageEventType:
    event_bus.register_handler(event_type, audit_handler)

# Wrap storage service
storage = EventAwareStorageManager(
    SimpleStorageService(),
    event_bus
)

# Start event processing
asyncio.create_task(event_bus.start_processing())
"""

