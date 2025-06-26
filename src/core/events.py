# src/core/events.py
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import uuid


class EventType(str, Enum):
    # Job discovery events
    JOB_DISCOVERED = "job.discovered"
    JOB_ANALYZED = "job.analyzed"
    
    # Resume events
    RESUME_GENERATION_REQUESTED = "resume.generation.requested"
    RESUME_GENERATED = "resume.generated"
    RESUME_OPTIMIZATION_REQUESTED = "resume.optimization.requested"
    RESUME_OPTIMIZED = "resume.optimized"
    
    # Application events
    APPLICATION_SUBMITTED = "application.submitted"
    APPLICATION_RESPONSE_RECEIVED = "application.response.received"
    APPLICATION_STATUS_UPDATED = "application.status.updated"
    
    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_STEP_COMPLETED = "workflow.step.completed"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    
    # System events
    AGENT_HEALTH_CHECK = "agent.health.check"
    CELL_STATUS_UPDATE = "cell.status.update"


class BaseEvent(BaseModel):
    """Base event structure for all events in the system"""
    
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: int
    cell_id: str = "cell-001"  # Default for Phase 1
    correlation_id: Optional[str] = None  # For tracking related events
    
    # Event payload
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        use_enum_values = True


# Specific event schemas
class JobDiscoveredEvent(BaseEvent):
    event_type: EventType = EventType.JOB_DISCOVERED
    
    def __init__(self, user_id: int, job_url: str, company: str, position: str, **kwargs):
        super().__init__(
            user_id=user_id,
            data={
                "job_url": job_url,
                "company": company,
                "position": position,
                **kwargs.get("data", {})
            },
            **{k: v for k, v in kwargs.items() if k != "data"}
        )


class JobAnalyzedEvent(BaseEvent):
    event_type: EventType = EventType.JOB_ANALYZED
    
    def __init__(self, user_id: int, job_id: int, analysis_result: dict, **kwargs):
        super().__init__(
            user_id=user_id,
            data={
                "job_id": job_id,
                "analysis_result": analysis_result,
                **kwargs.get("data", {})
            },
            **{k: v for k, v in kwargs.items() if k != "data"}
        )


class ResumeGenerationRequestedEvent(BaseEvent):
    event_type: EventType = EventType.RESUME_GENERATION_REQUESTED
    
    def __init__(self, user_id: int, job_id: int, template: str = "modern_professional", **kwargs):
        super().__init__(
            user_id=user_id,
            data={
                "job_id": job_id,
                "template": template,
                **kwargs.get("data", {})
            },
            **{k: v for k, v in kwargs.items() if k != "data"}
        )


class ResumeGeneratedEvent(BaseEvent):
    event_type: EventType = EventType.RESUME_GENERATED
    
    def __init__(self, user_id: int, job_id: int, resume_url: str, version_name: str, **kwargs):
        super().__init__(
            user_id=user_id,
            data={
                "job_id": job_id,
                "resume_url": resume_url,
                "version_name": version_name,
                **kwargs.get("data", {})
            },
            **{k: v for k, v in kwargs.items() if k != "data"}
        )


class WorkflowStartedEvent(BaseEvent):
    event_type: EventType = EventType.WORKFLOW_STARTED
    
    def __init__(self, user_id: int, workflow_id: str, workflow_type: str, **kwargs):
        super().__init__(
            user_id=user_id,
            data={
                "workflow_id": workflow_id,
                "workflow_type": workflow_type,
                **kwargs.get("data", {})
            },
            **{k: v for k, v in kwargs.items() if k != "data"}
        )


class WorkflowCompletedEvent(BaseEvent):
    event_type: EventType = EventType.WORKFLOW_COMPLETED
    
    def __init__(self, user_id: int, workflow_id: str, results: dict, **kwargs):
        super().__init__(
            user_id=user_id,
            data={
                "workflow_id": workflow_id,
                "results": results,
                **kwargs.get("data", {})
            },
            **{k: v for k, v in kwargs.items() if k != "data"}
        )