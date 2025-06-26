# src/workflows/workflow_engine.py
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from src.workflows.base_workflow import BaseWorkflow, WorkflowStatus
from src.workflows.job_application_workflow import create_workflow, WORKFLOW_TEMPLATES
from src.core.event_bus import event_bus
from src.core.events import BaseEvent, EventType

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Workflow Engine manages and orchestrates all workflows in the system
    
    Capabilities:
    - Create and start workflows
    - Monitor workflow progress
    - Handle workflow lifecycle events
    - Provide workflow status and metrics
    - Manage workflow scheduling and retries
    - Handle workflow persistence (future)
    """
    
    def __init__(self, cell_id: str = "cell-001"):
        self.cell_id = cell_id
        self.active_workflows: Dict[str, BaseWorkflow] = {}
        self.completed_workflows: Dict[str, BaseWorkflow] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        
        # Engine statistics
        self.workflows_created = 0
        self.workflows_completed = 0
        self.workflows_failed = 0
        self.total_execution_time = 0.0
        
        # Monitoring and cleanup
        self.max_completed_workflows = 100  # Keep last 100 completed workflows
        self.cleanup_interval = 3600  # Cleanup every hour
        self.last_cleanup = datetime.utcnow()
        
        logger.info(f"🏭 Workflow Engine initialized for cell {self.cell_id}")
    
    async def create_workflow(
        self, 
        workflow_type: str, 
        user_id: int, 
        initial_context: Dict[str, Any] = None,
        workflow_id: str = None
    ) -> str:
        """
        Create a new workflow
        
        Args:
            workflow_type: Type of workflow to create
            user_id: User ID for the workflow
            initial_context: Initial context data
            workflow_id: Optional specific workflow ID
            
        Returns:
            str: The workflow ID
        """
        try:
            # Create workflow instance
            workflow = create_workflow(
                workflow_type=workflow_type,
                user_id=user_id,
                workflow_id=workflow_id
            )
            
            # Store in active workflows
            self.active_workflows[workflow.workflow_id] = workflow
            self.workflows_created += 1
            
            # Update initial context if provided
            if initial_context:
                workflow.context.update(initial_context)
            
            logger.info(f"📋 Created workflow {workflow.workflow_id} ({workflow_type}) for user {user_id}")
            
            return workflow.workflow_id
            
        except Exception as e:
            logger.error(f"❌ Failed to create workflow: {e}")
            raise
    
    async def start_workflow(self, workflow_id: str, initial_context: Dict[str, Any] = None) -> bool:
        """
        Start an existing workflow
        
        Args:
            workflow_id: ID of the workflow to start
            initial_context: Optional initial context
            
        Returns:
            bool: True if started successfully
        """
        try:
            workflow = self.active_workflows.get(workflow_id)
            if not workflow:
                logger.error(f"❌ Workflow {workflow_id} not found")
                return False
            
            logger.info(f"🚀 Starting workflow {workflow_id}")
            
            # Start the workflow
            await workflow.start(initial_context or {})
            
            # Setup monitoring
            asyncio.create_task(self._monitor_workflow(workflow))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start workflow {workflow_id}: {e}")
            return False
    
    async def create_and_start_workflow(
        self, 
        workflow_type: str, 
        user_id: int, 
        initial_context: Dict[str, Any] = None
    ) -> str:
        """
        Create and immediately start a workflow
        
        Args:
            workflow_type: Type of workflow to create
            user_id: User ID for the workflow
            initial_context: Initial context data
            
        Returns:
            str: The workflow ID
        """
        workflow_id = await self.create_workflow(workflow_type, user_id, initial_context)
        await self.start_workflow(workflow_id, initial_context)
        return workflow_id
    
    async def pause_workflow(self, workflow_id: str) -> bool:
        """Pause a running workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if workflow and workflow.status == WorkflowStatus.RUNNING:
            await workflow.pause()
            logger.info(f"⏸️ Paused workflow {workflow_id}")
            return True
        return False
    
    async def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if workflow and workflow.status == WorkflowStatus.PAUSED:
            await workflow.resume()
            logger.info(f"▶️ Resumed workflow {workflow_id}")
            return True
        return False
    
    async def cancel_workflow(self, workflow_id: str, reason: str = "") -> bool:
        """Cancel a workflow"""
        workflow = self.active_workflows.get(workflow_id)
        if workflow and workflow.status in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]:
            await workflow.cancel(reason)
            await self._move_to_completed(workflow)
            logger.info(f"🛑 Cancelled workflow {workflow_id}")
            return True
        return False
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status and details"""
        # Check active workflows first
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            # Check completed workflows
            workflow = self.completed_workflows.get(workflow_id)
        
        if workflow:
            return workflow.to_dict()
        return None
    
    async def list_workflows(
        self, 
        user_id: Optional[int] = None, 
        status: Optional[WorkflowStatus] = None,
        workflow_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List workflows with optional filtering
        
        Args:
            user_id: Filter by user ID
            status: Filter by workflow status
            workflow_type: Filter by workflow type
            
        Returns:
            List of workflow dictionaries
        """
        workflows = []
        
        # Combine active and completed workflows
        all_workflows = {**self.active_workflows, **self.completed_workflows}
        
        for workflow in all_workflows.values():
            # Apply filters
            if user_id and workflow.user_id != user_id:
                continue
            if status and workflow.status != status:
                continue
            if workflow_type and workflow.workflow_type != workflow_type:
                continue
            
            workflows.append(workflow.to_dict())
        
        # Sort by creation time (newest first)
        workflows.sort(key=lambda w: w['created_at'], reverse=True)
        
        return workflows
    
    async def get_user_workflows(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive workflow information for a user"""
        user_workflows = await self.list_workflows(user_id=user_id)
        
        # Calculate statistics
        total = len(user_workflows)
        running = len([w for w in user_workflows if w['status'] == 'running'])
        completed = len([w for w in user_workflows if w['status'] == 'completed'])
        failed = len([w for w in user_workflows if w['status'] == 'failed'])
        
        # Calculate average duration for completed workflows
        completed_workflows = [w for w in user_workflows if w['duration_seconds']]
        avg_duration = sum(w['duration_seconds'] for w in completed_workflows) / len(completed_workflows) if completed_workflows else 0
        
        return {
            "user_id": user_id,
            "total_workflows": total,
            "running_workflows": running,
            "completed_workflows": completed,
            "failed_workflows": failed,
            "average_duration_seconds": avg_duration,
            "workflows": user_workflows[:10]  # Return last 10 workflows
        }
    
    async def _monitor_workflow(self, workflow: BaseWorkflow):
        """Monitor a workflow for completion"""
        try:
            # Wait for workflow to complete
            while workflow.status in [WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]:
                await asyncio.sleep(5)  # Check every 5 seconds
            
            # Move completed/failed workflow to completed list
            await self._move_to_completed(workflow)
            
        except Exception as e:
            logger.error(f"❌ Error monitoring workflow {workflow.workflow_id}: {e}")
    
    async def _move_to_completed(self, workflow: BaseWorkflow):
        """Move workflow from active to completed"""
        if workflow.workflow_id in self.active_workflows:
            del self.active_workflows[workflow.workflow_id]
        
        self.completed_workflows[workflow.workflow_id] = workflow
        
        # Update statistics
        if workflow.status == WorkflowStatus.COMPLETED:
            self.workflows_completed += 1
        elif workflow.status == WorkflowStatus.FAILED:
            self.workflows_failed += 1
        
        # Add to history
        self.workflow_history.append({
            "workflow_id": workflow.workflow_id,
            "workflow_type": workflow.workflow_type,
            "user_id": workflow.user_id,
            "status": workflow.status.value,
            "duration_seconds": workflow.duration_seconds,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
        })
        
        # Cleanup if needed
        await self._cleanup_completed_workflows()
        
        logger.info(f"📁 Moved workflow {workflow.workflow_id} to completed (status: {workflow.status.value})")
    
    async def _cleanup_completed_workflows(self):
        """Cleanup old completed workflows"""
        current_time = datetime.utcnow()
        
        # Check if cleanup is needed
        if (current_time - self.last_cleanup).seconds < self.cleanup_interval:
            return
        
        # Remove excess completed workflows
        if len(self.completed_workflows) > self.max_completed_workflows:
            # Sort by completion time and keep most recent
            workflows_by_completion = sorted(
                self.completed_workflows.values(),
                key=lambda w: w.completed_at or datetime.min,
                reverse=True
            )
            
            # Keep only the most recent workflows
            workflows_to_keep = workflows_by_completion[:self.max_completed_workflows]
            keep_ids = {w.workflow_id for w in workflows_to_keep}
            
            # Remove old workflows
            self.completed_workflows = {
                wid: workflow for wid, workflow in self.completed_workflows.items()
                if wid in keep_ids
            }
            
            logger.info(f"🧹 Cleaned up old workflows, kept {len(workflows_to_keep)} most recent")
        
        self.last_cleanup = current_time
    
    def get_engine_stats(self) -> Dict[str, Any]:
        """Get workflow engine statistics"""
        active_count = len(self.active_workflows)
        completed_count = len(self.completed_workflows)
        
        # Calculate success rate
        total_finished = self.workflows_completed + self.workflows_failed
        success_rate = (self.workflows_completed / total_finished * 100) if total_finished > 0 else 0
        
        # Active workflow breakdown by status
        status_breakdown = {}
        for workflow in self.active_workflows.values():
            status = workflow.status.value
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        return {
            "cell_id": self.cell_id,
            "active_workflows": active_count,
            "completed_workflows": completed_count,
            "total_created": self.workflows_created,
            "total_completed": self.workflows_completed,
            "total_failed": self.workflows_failed,
            "success_rate_percentage": round(success_rate, 2),
            "average_execution_time": self.total_execution_time / self.workflows_completed if self.workflows_completed > 0 else 0,
            "active_status_breakdown": status_breakdown,
            "workflow_templates": list(WORKFLOW_TEMPLATES.keys())
        }
    
    def get_workflow_templates(self) -> Dict[str, Any]:
        """Get available workflow templates"""
        return WORKFLOW_TEMPLATES.copy()
    
    async def handle_workflow_event(self, event: BaseEvent):
        """Handle workflow-related events from the event bus"""
        try:
            workflow_id = event.data.get("workflow_id")
            if not workflow_id:
                return
            
            workflow = self.active_workflows.get(workflow_id)
            if not workflow:
                return
            
            if event.event_type == EventType.WORKFLOW_STEP_COMPLETED:
                # Handle step completion
                step_id = event.data.get("step_id")
                step_status = event.data.get("step_status")
                
                logger.debug(f"🔄 Workflow {workflow_id} step {step_id} status: {step_status}")
                
                # Update workflow state based on step completion
                # This would trigger the next step in the workflow
                
        except Exception as e:
            logger.error(f"❌ Error handling workflow event: {e}")


# Global workflow engine instance
workflow_engine = WorkflowEngine()


# Convenience functions for common operations
async def start_job_search_workflow(user_id: int, search_terms: List[str], location: str = "Remote") -> str:
    """Start a complete job search workflow"""
    return await workflow_engine.create_and_start_workflow(
        workflow_type="job_application",
        user_id=user_id,
        initial_context={
            "search_terms": search_terms,
            "location": location,
            "workflow_trigger": "user_initiated"
        }
    )


async def start_quick_resume_workflow(user_id: int, job_id: int) -> str:
    """Start a quick resume generation workflow for a specific job"""
    return await workflow_engine.create_and_start_workflow(
        workflow_type="quick_resume",
        user_id=user_id,
        initial_context={
            "job_id": job_id,
            "workflow_trigger": "job_specific"
        }
    )


async def start_optimization_workflow(user_id: int) -> str:
    """Start a resume optimization workflow"""
    return await workflow_engine.create_and_start_workflow(
        workflow_type="optimization",
        user_id=user_id,
        initial_context={
            "workflow_trigger": "optimization_request"
        }
    )