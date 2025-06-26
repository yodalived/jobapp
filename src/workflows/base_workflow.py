# src/workflows/base_workflow.py
import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from src.core.events import BaseEvent
from src.core.event_bus import event_bus

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class WorkflowStep:
    """Individual step in a workflow"""
    
    def __init__(
        self,
        step_id: str,
        name: str,
        handler: str,  # Agent or function to handle this step
        input_data: Dict[str, Any] = None,
        timeout_seconds: int = 300,
        retry_count: int = 3,
        retry_delay: int = 5,
        required: bool = True
    ):
        self.step_id = step_id
        self.name = name
        self.handler = handler
        self.input_data = input_data or {}
        self.timeout_seconds = timeout_seconds
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.required = required
        
        # Runtime state
        self.status = StepStatus.PENDING
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.output_data: Dict[str, Any] = {}
        self.error_message: Optional[str] = None
        self.current_retry = 0
    
    def start(self):
        """Mark step as started"""
        self.status = StepStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete(self, output_data: Dict[str, Any] = None):
        """Mark step as completed"""
        self.status = StepStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.output_data = output_data or {}
    
    def fail(self, error_message: str):
        """Mark step as failed"""
        self.status = StepStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def retry(self):
        """Mark step for retry"""
        self.current_retry += 1
        self.status = StepStatus.RETRYING
        self.error_message = None
    
    def skip(self, reason: str = ""):
        """Mark step as skipped"""
        self.status = StepStatus.SKIPPED
        self.completed_at = datetime.utcnow()
        self.error_message = reason
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate step duration"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def can_retry(self) -> bool:
        """Check if step can be retried"""
        return self.current_retry < self.retry_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary"""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "handler": self.handler,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "current_retry": self.current_retry,
            "max_retries": self.retry_count,
            "error_message": self.error_message,
            "output_data": self.output_data
        }


class BaseWorkflow(ABC):
    """
    Base class for all workflows in the system
    
    Workflows define multi-step processes that coordinate agents
    to accomplish complex tasks like job application automation
    """
    
    def __init__(self, workflow_id: str = None, user_id: int = None):
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.user_id = user_id
        self.status = WorkflowStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        
        # Workflow state
        self.steps: List[WorkflowStep] = []
        self.current_step_index = 0
        self.context: Dict[str, Any] = {}
        self.error_message: Optional[str] = None
        
        # Initialize workflow steps
        self._initialize_steps()
        
        logger.info(f"🔄 Workflow {self.workflow_id} initialized with {len(self.steps)} steps")
    
    @property
    @abstractmethod
    def workflow_type(self) -> str:
        """Return the workflow type name"""
        pass
    
    @abstractmethod
    def _initialize_steps(self):
        """Initialize the workflow steps - implemented by subclasses"""
        pass
    
    def add_step(
        self,
        step_id: str,
        name: str,
        handler: str,
        input_data: Dict[str, Any] = None,
        **kwargs
    ):
        """Add a step to the workflow"""
        step = WorkflowStep(
            step_id=step_id,
            name=name,
            handler=handler,
            input_data=input_data or {},
            **kwargs
        )
        self.steps.append(step)
    
    async def start(self, initial_context: Dict[str, Any] = None):
        """Start workflow execution"""
        if self.status != WorkflowStatus.PENDING:
            raise RuntimeError(f"Workflow {self.workflow_id} is not in pending state")
        
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.context.update(initial_context or {})
        
        logger.info(f"🚀 Starting workflow {self.workflow_id} ({self.workflow_type})")
        
        # Emit workflow started event
        await self._emit_workflow_event("started", {"initial_context": initial_context})
        
        # Start execution
        await self._execute_next_step()
    
    async def _execute_next_step(self):
        """Execute the next step in the workflow"""
        if self.current_step_index >= len(self.steps):
            await self._complete_workflow()
            return
        
        current_step = self.steps[self.current_step_index]
        
        try:
            logger.info(f"▶️ Executing step {current_step.step_id}: {current_step.name}")
            
            # Start the step
            current_step.start()
            
            # Emit step started event
            await self._emit_step_event(current_step, "started")
            
            # Execute the step
            await self._execute_step(current_step)
            
        except Exception as e:
            logger.error(f"❌ Step {current_step.step_id} failed: {e}")
            await self._handle_step_failure(current_step, str(e))
    
    async def _execute_step(self, step: WorkflowStep):
        """Execute a specific step"""
        try:
            # Prepare step input data
            step_input = {
                **step.input_data,
                **self.context,
                "workflow_id": self.workflow_id,
                "step_id": step.step_id
            }
            
            # Execute step based on handler type
            if step.handler.endswith("-agent"):
                await self._execute_agent_step(step, step_input)
            else:
                await self._execute_function_step(step, step_input)
                
        except asyncio.TimeoutError:
            raise Exception(f"Step timed out after {step.timeout_seconds} seconds")
        except Exception as e:
            raise Exception(f"Step execution failed: {e}")
    
    async def _execute_agent_step(self, step: WorkflowStep, step_input: Dict[str, Any]):
        """Execute a step handled by an agent"""
        # Create event for the agent to process
        from src.core.events import BaseEvent, EventType
        
        # Map step handlers to event types
        event_type_map = {
            "scraper-agent": EventType.JOB_DISCOVERED,
            "analyzer-agent": EventType.JOB_ANALYZED,
            "generator-agent": EventType.RESUME_GENERATION_REQUESTED,
            "optimizer-agent": EventType.RESUME_OPTIMIZATION_REQUESTED
        }
        
        event_type = event_type_map.get(step.handler)
        if not event_type:
            raise Exception(f"Unknown agent handler: {step.handler}")
        
        # Create and publish event
        event = BaseEvent(
            event_type=event_type,
            user_id=self.user_id,
            data=step_input,
            metadata={
                "workflow_id": self.workflow_id,
                "step_id": step.step_id
            }
        )
        
        success = await event_bus.publish(event)
        if not success:
            raise Exception("Failed to publish event to agent")
        
        # Wait for step completion (simulated for now)
        # In a real implementation, this would wait for response events
        await asyncio.sleep(2)  # Simulate processing time
        
        # Mark step as completed (agents will handle the actual work)
        step.complete({"event_id": event.event_id})
    
    async def _execute_function_step(self, step: WorkflowStep, step_input: Dict[str, Any]):
        """Execute a step handled by a function"""
        # This would call specific functions based on step.handler
        # For now, just simulate completion
        await asyncio.sleep(1)
        step.complete({"result": "function executed"})
    
    async def _handle_step_failure(self, step: WorkflowStep, error_message: str):
        """Handle step failure with retry logic"""
        step.fail(error_message)
        
        # Emit step failed event
        await self._emit_step_event(step, "failed", {"error": error_message})
        
        # Check if we can retry
        if step.can_retry and step.required:
            logger.info(f"🔄 Retrying step {step.step_id} (attempt {step.current_retry + 1})")
            step.retry()
            
            # Wait before retry
            await asyncio.sleep(step.retry_delay)
            
            # Retry the step
            await self._execute_step(step)
        else:
            # Check if step is required
            if step.required:
                # Fail the entire workflow
                await self._fail_workflow(f"Required step {step.step_id} failed: {error_message}")
            else:
                # Skip and continue
                logger.warning(f"⏭️ Skipping failed optional step {step.step_id}")
                step.skip(f"Failed but optional: {error_message}")
                await self._step_completed(step)
    
    async def _step_completed(self, step: WorkflowStep):
        """Handle step completion"""
        logger.info(f"✅ Step {step.step_id} completed in {step.duration_seconds:.2f}s")
        
        # Update context with step output
        self.context.update(step.output_data)
        
        # Emit step completed event
        await self._emit_step_event(step, "completed", step.output_data)
        
        # Move to next step
        self.current_step_index += 1
        await self._execute_next_step()
    
    async def _complete_workflow(self):
        """Complete the workflow"""
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        
        logger.info(f"🎉 Workflow {self.workflow_id} completed in {self.duration_seconds:.2f}s")
        
        # Emit workflow completed event
        await self._emit_workflow_event("completed", {"final_context": self.context})
    
    async def _fail_workflow(self, error_message: str):
        """Fail the workflow"""
        self.status = WorkflowStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        
        logger.error(f"💥 Workflow {self.workflow_id} failed: {error_message}")
        
        # Emit workflow failed event
        await self._emit_workflow_event("failed", {"error": error_message})
    
    async def cancel(self, reason: str = ""):
        """Cancel the workflow"""
        self.status = WorkflowStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.error_message = reason
        
        logger.info(f"🛑 Workflow {self.workflow_id} cancelled: {reason}")
        
        # Emit workflow cancelled event
        await self._emit_workflow_event("cancelled", {"reason": reason})
    
    async def pause(self):
        """Pause the workflow"""
        if self.status == WorkflowStatus.RUNNING:
            self.status = WorkflowStatus.PAUSED
            logger.info(f"⏸️ Workflow {self.workflow_id} paused")
    
    async def resume(self):
        """Resume the workflow"""
        if self.status == WorkflowStatus.PAUSED:
            self.status = WorkflowStatus.RUNNING
            logger.info(f"▶️ Workflow {self.workflow_id} resumed")
            await self._execute_next_step()
    
    async def _emit_workflow_event(self, event_name: str, data: Dict[str, Any] = None):
        """Emit workflow-level events"""
        from src.core.events import BaseEvent, EventType
        
        event_type_map = {
            "started": EventType.WORKFLOW_STARTED,
            "completed": EventType.WORKFLOW_COMPLETED,
            "failed": EventType.WORKFLOW_FAILED,
            "cancelled": EventType.WORKFLOW_FAILED  # Use same type with different data
        }
        
        event = BaseEvent(
            event_type=event_type_map.get(event_name, EventType.WORKFLOW_STARTED),
            user_id=self.user_id,
            data={
                "workflow_id": self.workflow_id,
                "workflow_type": self.workflow_type,
                "status": self.status.value,
                **(data or {})
            }
        )
        
        await event_bus.publish(event)
    
    async def _emit_step_event(self, step: WorkflowStep, event_name: str, data: Dict[str, Any] = None):
        """Emit step-level events"""
        from src.core.events import BaseEvent, EventType
        
        event = BaseEvent(
            event_type=EventType.WORKFLOW_STEP_COMPLETED,
            user_id=self.user_id,
            data={
                "workflow_id": self.workflow_id,
                "step_id": step.step_id,
                "step_name": step.name,
                "step_status": step.status.value,
                "event_name": event_name,
                **(data or {})
            }
        )
        
        await event_bus.publish(event)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate workflow duration"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def progress_percentage(self) -> float:
        """Calculate workflow progress percentage"""
        if not self.steps:
            return 0.0
        
        completed_steps = sum(1 for step in self.steps if step.status == StepStatus.COMPLETED)
        return (completed_steps / len(self.steps)) * 100
    
    def get_current_step(self) -> Optional[WorkflowStep]:
        """Get the current step being executed"""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "user_id": self.user_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "progress_percentage": self.progress_percentage,
            "current_step_index": self.current_step_index,
            "total_steps": len(self.steps),
            "context": self.context,
            "error_message": self.error_message,
            "steps": [step.to_dict() for step in self.steps]
        }