# src/agents/generator_agent.py
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
import os

from src.agents.base_agent import BaseAgent
from src.core.events import BaseEvent, EventType, ResumeGeneratedEvent
from src.core.database import AsyncSessionLocal
from src.api.models.schema import JobApplication, ResumeVersion
from src.generator.resume_generator import ResumeGenerator
from src.generator.llm_interface import get_llm

logger = logging.getLogger(__name__)


class GeneratorAgent(BaseAgent):
    """
    Agent responsible for generating customized resumes
    
    Capabilities:
    - Generate resumes tailored to specific job descriptions
    - Use multiple templates and formats (LaTeX, HTML, Markdown)
    - Integrate with LLMs for content customization
    - Optimize resume content for ATS systems
    - Generate multiple versions for A/B testing
    """
    
    def __init__(self, cell_id: str = "cell-001"):
        super().__init__("generator-agent", cell_id)
        
        # Initialize resume generator
        self.resume_generator = ResumeGenerator()
        
        # Output directory for generated resumes
        self.output_dir = Path("resume_outputs")
        self.output_dir.mkdir(exist_ok=True)
        
        # Generation statistics
        self.resumes_generated = 0
        self.generation_failures = 0
    
    @property
    def subscribed_events(self) -> List[EventType]:
        return [
            EventType.RESUME_GENERATION_REQUESTED,
            EventType.JOB_ANALYZED  # Auto-generate resumes after job analysis
        ]
    
    @property
    def consumer_group_id(self) -> str:
        return f"{self.cell_id}-generator-group"
    
    async def process_event(self, event: BaseEvent) -> None:
        """
        Process resume generation events
        
        Args:
            event: Resume generation or job analyzed event
        """
        try:
            if event.event_type == EventType.RESUME_GENERATION_REQUESTED:
                await self._handle_resume_generation_request(event)
            elif event.event_type == EventType.JOB_ANALYZED:
                await self._handle_job_analyzed_event(event)
            else:
                logger.warning(f"⚠️ Unknown event type: {event.event_type}")
                
        except Exception as e:
            logger.error(f"❌ Failed to process generation event: {e}")
            self.generation_failures += 1
            raise
    
    async def _handle_resume_generation_request(self, event: BaseEvent):
        """Handle explicit resume generation requests"""
        job_id = event.data.get("job_id")
        template = event.data.get("template", "modern_professional")
        
        if not job_id:
            logger.error(f"❌ Missing job_id in resume generation request {event.event_id}")
            return
        
        logger.info(f"📝 Processing resume generation request for job {job_id}")
        
        # Generate resume
        resume_result = await self._generate_resume_for_job(
            user_id=event.user_id,
            job_id=job_id,
            template=template
        )
        
        if resume_result:
            await self._emit_resume_generated_event(
                user_id=event.user_id,
                job_id=job_id,
                resume_result=resume_result
            )
    
    async def _handle_job_analyzed_event(self, event: BaseEvent):
        """Handle job analyzed events - auto-generate resumes"""
        job_id = event.data.get("job_id")
        analysis_result = event.data.get("analysis_result", {})
        
        if not job_id:
            logger.error(f"❌ Missing job_id in job analyzed event {event.event_id}")
            return
        
        logger.info(f"🤖 Auto-generating resume for analyzed job {job_id}")
        
        # Determine best template based on analysis
        template = self._select_template_from_analysis(analysis_result)
        
        # Generate resume
        resume_result = await self._generate_resume_for_job(
            user_id=event.user_id,
            job_id=job_id,
            template=template,
            analysis_result=analysis_result
        )
        
        if resume_result:
            await self._emit_resume_generated_event(
                user_id=event.user_id,
                job_id=job_id,
                resume_result=resume_result
            )
    
    def _select_template_from_analysis(self, analysis_result: Dict) -> str:
        """Select best template based on job analysis"""
        job_type = analysis_result.get("job_type", "technical")
        experience_level = analysis_result.get("experience_level", "mid")
        industry = analysis_result.get("industry", "technology")
        
        # Simple template selection logic
        if job_type == "management":
            return "executive_professional"
        elif experience_level == "senior" or experience_level == "lead":
            return "senior_professional"
        else:
            return "modern_professional"
    
    async def _generate_resume_for_job(
        self, 
        user_id: int, 
        job_id: int, 
        template: str,
        analysis_result: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Generate a customized resume for a specific job
        
        Args:
            user_id: User ID
            job_id: Job application ID
            template: Template name to use
            analysis_result: Optional job analysis results
            
        Returns:
            Dict with resume generation results or None if failed
        """
        try:
            # Get job details
            job_data = await self._get_job_data(job_id)
            if not job_data:
                logger.error(f"❌ Could not find job {job_id}")
                return None
            
            # Get user profile (mock for now)
            user_profile = await self._get_user_profile(user_id)
            
            # Prepare generation parameters
            generation_params = {
                "user_profile": user_profile,
                "job_description": job_data.job_description,
                "company": job_data.company,
                "position": job_data.position,
                "template": template,
                "analysis_result": analysis_result or {}
            }
            
            # Generate resume content using LLM
            customized_content = await self._customize_resume_content(generation_params)
            
            # Generate PDF using existing resume generator
            output_filename = f"resume_job_{job_id}_user_{user_id}_{template}"
            pdf_path = await self._generate_pdf(customized_content, output_filename)
            
            # Store resume version
            resume_version_id = await self._store_resume_version(
                user_id=user_id,
                job_id=job_id,
                template=template,
                pdf_path=pdf_path,
                content=customized_content
            )
            
            self.resumes_generated += 1
            
            return {
                "resume_version_id": resume_version_id,
                "pdf_path": str(pdf_path),
                "template": template,
                "generation_params": generation_params
            }
            
        except Exception as e:
            logger.error(f"❌ Resume generation failed for job {job_id}: {e}")
            self.generation_failures += 1
            return None
    
    async def _get_job_data(self, job_id: int) -> Optional[JobApplication]:
        """Get job application data"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            
            result = await session.execute(
                select(JobApplication).where(JobApplication.id == job_id)
            )
            return result.scalar_one_or_none()
    
    async def _get_user_profile(self, user_id: int) -> Dict:
        """Get user profile data (mock implementation)"""
        # TODO: Implement real user profile retrieval
        return {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "location": "San Francisco, CA",
            "title": "Senior Software Engineer",
            "summary": "Experienced software engineer with 5+ years in Python and cloud technologies",
            "experience": [
                {
                    "company": "Tech Company",
                    "position": "Software Engineer",
                    "duration": "2020-2024",
                    "description": "Developed scalable web applications using Python and AWS"
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "school": "University of California",
                    "year": "2019"
                }
            ],
            "skills": [
                "Python", "JavaScript", "AWS", "Docker", "PostgreSQL", 
                "React", "FastAPI", "Machine Learning"
            ]
        }
    
    async def _customize_resume_content(self, params: Dict) -> Dict:
        """Use LLM to customize resume content for the specific job"""
        try:
            # Create customization prompt
            prompt = self._create_customization_prompt(params)
            
            # Get LLM response
            llm = get_llm()
            response = await llm.agenerate([prompt])
            customization = response.generations[0][0].text.strip()
            
            # Parse customization suggestions
            suggestions = self._parse_customization_response(customization)
            
            # Apply customizations to user profile
            customized_content = self._apply_customizations(params["user_profile"], suggestions)
            
            return customized_content
            
        except Exception as e:
            logger.error(f"❌ Content customization failed: {e}")
            # Return original profile if customization fails
            return params["user_profile"]
    
    def _create_customization_prompt(self, params: Dict) -> str:
        """Create prompt for resume customization"""
        return f"""
You are a professional resume writer. Customize the following resume for the specific job posting.

Job Details:
Company: {params['company']}
Position: {params['position']}

Job Description:
{params['job_description']}

Current Resume Profile:
Name: {params['user_profile']['name']}
Title: {params['user_profile']['title']}
Summary: {params['user_profile']['summary']}
Skills: {', '.join(params['user_profile']['skills'])}

Please provide customization suggestions in the following format:
- Customize the professional summary to highlight relevant experience
- Prioritize skills that match the job requirements
- Suggest key achievements to emphasize
- Recommend any additional keywords to include

Focus on making the resume more appealing for this specific role while maintaining truthfulness.
"""
    
    def _parse_customization_response(self, customization: str) -> Dict:
        """Parse LLM customization response"""
        # Simple parsing - extract key suggestions
        return {
            "summary_updates": "Enhanced summary based on job requirements",
            "skill_prioritization": [],
            "keyword_suggestions": [],
            "achievement_emphasis": []
        }
    
    def _apply_customizations(self, profile: Dict, suggestions: Dict) -> Dict:
        """Apply customization suggestions to user profile"""
        # Create a copy of the profile
        customized = profile.copy()
        
        # Apply summary updates
        if suggestions.get("summary_updates"):
            customized["summary"] = suggestions["summary_updates"]
        
        # Apply skill prioritization
        if suggestions.get("skill_prioritization"):
            customized["skills"] = suggestions["skill_prioritization"] + customized["skills"]
        
        return customized
    
    async def _generate_pdf(self, content: Dict, filename: str) -> Path:
        """Generate PDF using existing resume generator"""
        try:
            # Use existing resume generator
            pdf_path = await asyncio.to_thread(
                self.resume_generator.generate_resume,
                user_data=content,
                template_name="modern_professional",
                output_filename=filename
            )
            
            return Path(pdf_path)
            
        except Exception as e:
            logger.error(f"❌ PDF generation failed: {e}")
            raise
    
    async def _store_resume_version(
        self, 
        user_id: int, 
        job_id: int, 
        template: str, 
        pdf_path: Path,
        content: Dict
    ) -> int:
        """Store resume version in database"""
        async with AsyncSessionLocal() as session:
            from src.api.models.schema import JobType
            
            resume_version = ResumeVersion(
                user_id=user_id,
                version_name=f"Job_{job_id}_{template}",
                template_name=template,
                file_url=str(pdf_path),
                content_hash=str(hash(str(content))),
                job_type=JobType.TECHNICAL,  # TODO: derive from job analysis
                times_used=0,
                extra_data={
                    "job_id": job_id,
                    "generated_content": content,
                    "generation_timestamp": str(asyncio.get_event_loop().time())
                }
            )
            
            session.add(resume_version)
            await session.commit()
            await session.refresh(resume_version)
            
            logger.info(f"💾 Stored resume version {resume_version.id}")
            return resume_version.id
    
    async def _emit_resume_generated_event(self, user_id: int, job_id: int, resume_result: Dict):
        """Emit resume generated event"""
        event = ResumeGeneratedEvent(
            user_id=user_id,
            job_id=job_id,
            resume_url=resume_result["pdf_path"],
            version_name=f"Job_{job_id}_{resume_result['template']}"
        )
        
        await self.publish_event(event)
        logger.info(f"📤 Published resume generated event for job {job_id}")
    
    async def get_generation_stats(self) -> Dict:
        """Get generation statistics"""
        return {
            "agent_id": self.agent_id,
            "resumes_generated": self.resumes_generated,
            "generation_failures": self.generation_failures,
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "output_directory": str(self.output_dir)
        }