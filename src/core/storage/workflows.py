"""
Event-driven workflows for storage operations
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio

from .events import StorageEvent, StorageEventType, EventHandler


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """A step in a workflow"""
    name: str
    handler: callable
    on_success: Optional[str] = None  # Next step
    on_failure: Optional[str] = None  # Error step
    retry_count: int = 0
    timeout_seconds: int = 300


class StorageWorkflow:
    """Define and execute storage workflows triggered by events"""
    
    def __init__(self, name: str):
        self.name = name
        self.steps: Dict[str, WorkflowStep] = {}
        self.entry_point: Optional[str] = None
        self.context: Dict[str, Any] = {}
    
    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow"""
        self.steps[step.name] = step
        if not self.entry_point:
            self.entry_point = step.name
    
    async def execute(self, event: StorageEvent) -> Dict[str, Any]:
        """Execute the workflow"""
        self.context = {
            "event": event,
            "status": WorkflowStatus.RUNNING,
            "current_step": self.entry_point,
            "results": {}
        }
        
        current_step_name = self.entry_point
        
        while current_step_name:
            step = self.steps.get(current_step_name)
            if not step:
                break
            
            try:
                # Execute step with timeout
                result = await asyncio.wait_for(
                    step.handler(self.context),
                    timeout=step.timeout_seconds
                )
                
                self.context["results"][step.name] = result
                current_step_name = step.on_success
                
            except asyncio.TimeoutError:
                self.context["status"] = WorkflowStatus.FAILED
                self.context["error"] = f"Step {step.name} timed out"
                current_step_name = step.on_failure
                
            except Exception as e:
                self.context["status"] = WorkflowStatus.FAILED
                self.context["error"] = str(e)
                
                # Retry logic
                if step.retry_count > 0:
                    step.retry_count -= 1
                    continue
                
                current_step_name = step.on_failure
        
        if self.context["status"] == WorkflowStatus.RUNNING:
            self.context["status"] = WorkflowStatus.COMPLETED
        
        return self.context


# Example Workflows

class ResumeProcessingWorkflow(StorageWorkflow):
    """Workflow for processing uploaded resumes"""
    
    def __init__(self, services):
        super().__init__("resume_processing")
        self.services = services
        self._build_workflow()
    
    def _build_workflow(self):
        # Step 1: Validate file
        self.add_step(WorkflowStep(
            name="validate",
            handler=self._validate_resume,
            on_success="extract_text",
            on_failure="notify_invalid"
        ))
        
        # Step 2: Extract text
        self.add_step(WorkflowStep(
            name="extract_text",
            handler=self._extract_text,
            on_success="analyze",
            on_failure="notify_extraction_failed",
            retry_count=2
        ))
        
        # Step 3: Analyze content
        self.add_step(WorkflowStep(
            name="analyze",
            handler=self._analyze_content,
            on_success="index",
            on_failure="skip_indexing"
        ))
        
        # Step 4: Index for search
        self.add_step(WorkflowStep(
            name="index",
            handler=self._index_resume,
            on_success="match_jobs",
            timeout_seconds=60
        ))
        
        # Step 5: Match with jobs
        self.add_step(WorkflowStep(
            name="match_jobs",
            handler=self._match_jobs,
            on_success="notify_complete"
        ))
        
        # Success notification
        self.add_step(WorkflowStep(
            name="notify_complete",
            handler=self._notify_success
        ))
        
        # Error handlers
        self.add_step(WorkflowStep(
            name="notify_invalid",
            handler=self._notify_invalid_file
        ))
        
        self.add_step(WorkflowStep(
            name="notify_extraction_failed",
            handler=self._notify_extraction_failed
        ))
    
    async def _validate_resume(self, context: Dict[str, Any]):
        """Validate the uploaded resume"""
        event = context["event"]
        file_id = event.file_id
        
        # Check file type, size, format
        file_info = await self.services.storage.get_metadata(file_id)
        
        if file_info["size"] > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError("File too large")
        
        if not file_info["filename"].endswith(('.pdf', '.docx', '.txt')):
            raise ValueError("Invalid file format")
        
        return {"valid": True, "format": file_info["filename"].split('.')[-1]}
    
    async def _extract_text(self, context: Dict[str, Any]):
        """Extract text from resume"""
        event = context["event"]
        file_id = event.file_id
        
        # Download and extract text
        file_data = await self.services.storage.retrieve(file_id, event.user_id)
        text = await self.services.text_extractor.extract(file_data)
        
        return {"text": text, "word_count": len(text.split())}
    
    async def _analyze_content(self, context: Dict[str, Any]):
        """Analyze resume content"""
        text = context["results"]["extract_text"]["text"]
        
        # Extract skills, experience, education
        analysis = await self.services.resume_analyzer.analyze(text)
        
        return {
            "skills": analysis["skills"],
            "years_experience": analysis["years_experience"],
            "education_level": analysis["education_level"],
            "keywords": analysis["keywords"]
        }
    
    async def _index_resume(self, context: Dict[str, Any]):
        """Index resume for search"""
        event = context["event"]
        analysis = context["results"]["analyze"]
        
        await self.services.search_index.index_document(
            doc_id=event.file_id,
            user_id=event.user_id,
            content={
                "text": context["results"]["extract_text"]["text"],
                "skills": analysis["skills"],
                "keywords": analysis["keywords"]
            }
        )
        
        return {"indexed": True}
    
    async def _match_jobs(self, context: Dict[str, Any]):
        """Match resume with available jobs"""
        event = context["event"]
        analysis = context["results"]["analyze"]
        
        # Find matching jobs
        matches = await self.services.job_matcher.find_matches(
            skills=analysis["skills"],
            experience=analysis["years_experience"],
            user_id=event.user_id
        )
        
        # Queue applications for top matches
        for job in matches[:5]:
            await self.services.application_queue.add(
                user_id=event.user_id,
                job_id=job["id"],
                resume_id=event.file_id
            )
        
        return {"matched_jobs": len(matches), "queued": min(5, len(matches))}
    
    async def _notify_success(self, context: Dict[str, Any]):
        """Send success notification"""
        event = context["event"]
        results = context["results"]
        
        await self.services.notifications.send(
            user_id=event.user_id,
            type="resume_processed",
            data={
                "file_id": event.file_id,
                "jobs_matched": results.get("match_jobs", {}).get("matched_jobs", 0),
                "skills_found": len(results.get("analyze", {}).get("skills", []))
            }
        )
        
        return {"notified": True}
    
    async def _notify_invalid_file(self, context: Dict[str, Any]):
        """Notify about invalid file"""
        event = context["event"]
        error = context.get("error", "Unknown error")
        
        await self.services.notifications.send(
            user_id=event.user_id,
            type="resume_invalid",
            data={
                "file_id": event.file_id,
                "error": error
            }
        )
        
        return {"notified": True}


class StorageCleanupWorkflow(StorageWorkflow):
    """Workflow for cleaning up old files"""
    
    def __init__(self, services):
        super().__init__("storage_cleanup")
        self.services = services
        self._build_workflow()
    
    def _build_workflow(self):
        self.add_step(WorkflowStep(
            name="identify_old_files",
            handler=self._identify_old_files,
            on_success="archive_files"
        ))
        
        self.add_step(WorkflowStep(
            name="archive_files",
            handler=self._archive_files,
            on_success="delete_originals"
        ))
        
        self.add_step(WorkflowStep(
            name="delete_originals",
            handler=self._delete_originals,
            on_success="update_metrics"
        ))
        
        self.add_step(WorkflowStep(
            name="update_metrics",
            handler=self._update_metrics
        ))


# Workflow event handler
class WorkflowEventHandler(EventHandler):
    """Execute workflows based on events"""
    
    def __init__(self):
        self.workflows: Dict[StorageEventType, List[StorageWorkflow]] = {}
    
    def register_workflow(
        self,
        event_type: StorageEventType,
        workflow: StorageWorkflow
    ):
        """Register a workflow for an event type"""
        if event_type not in self.workflows:
            self.workflows[event_type] = []
        self.workflows[event_type].append(workflow)
    
    async def handle(self, event: StorageEvent):
        """Execute workflows for the event"""
        workflows = self.workflows.get(event.event_type, [])
        
        # Execute workflows in parallel
        tasks = [workflow.execute(event) for workflow in workflows]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log results
        for workflow, result in zip(workflows, results):
            if isinstance(result, Exception):
                print(f"Workflow {workflow.name} failed: {result}")
            else:
                print(f"Workflow {workflow.name} completed: {result['status']}")
    
    def can_handle(self, event_type: StorageEventType) -> bool:
        return event_type in self.workflows


# Usage example
"""
# Set up workflows
resume_workflow = ResumeProcessingWorkflow(services)
cleanup_workflow = StorageCleanupWorkflow(services)

# Create workflow handler
workflow_handler = WorkflowEventHandler()
workflow_handler.register_workflow(
    StorageEventType.FILE_UPLOADED,
    resume_workflow
)

# Register with event bus
event_bus.register_handler(
    StorageEventType.FILE_UPLOADED,
    workflow_handler
)

# Now when a resume is uploaded:
# 1. File is saved to storage
# 2. FILE_UPLOADED event is emitted
# 3. Workflow handler catches the event
# 4. Resume processing workflow executes:
#    - Validates file
#    - Extracts text
#    - Analyzes content
#    - Indexes for search
#    - Matches with jobs
#    - Sends notifications
# 5. All happens asynchronously without blocking the upload
"""
