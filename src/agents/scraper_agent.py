# src/agents/scraper_agent.py
import asyncio
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

from src.agents.base_agent import BaseAgent
from src.core.events import BaseEvent, EventType, JobDiscoveredEvent, JobAnalyzedEvent
from src.core.database import AsyncSessionLocal
from src.api.models.schema import JobApplication, ApplicationStatus

logger = logging.getLogger(__name__)


class ScraperAgent(BaseAgent):
    """
    Agent responsible for discovering jobs from various job boards
    
    Capabilities:
    - Monitor job boards for new postings
    - Parse job descriptions and requirements
    - Filter jobs based on user preferences
    - Emit job discovery events
    """
    
    def __init__(self, cell_id: str = "cell-001"):
        super().__init__("scraper-agent", cell_id)
        
        # Job board configurations
        self.job_boards = {
            "linkedin": {
                "enabled": True,
                "base_url": "https://www.linkedin.com/jobs/search",
                "rate_limit": 5  # requests per minute
            },
            "indeed": {
                "enabled": False,  # Implement later
                "base_url": "https://www.indeed.com/jobs",
                "rate_limit": 10
            },
            "glassdoor": {
                "enabled": False,  # Implement later
                "base_url": "https://www.glassdoor.com/Job",
                "rate_limit": 3
            }
        }
    
    @property
    def subscribed_events(self) -> List[EventType]:
        """This agent doesn't subscribe to events - it generates them via scheduled scraping"""
        return []
    
    @property
    def consumer_group_id(self) -> str:
        return f"{self.cell_id}-scraper-group"
    
    async def process_event(self, event: BaseEvent) -> None:
        """ScraperAgent generates events, doesn't process them"""
        pass
    
    async def start_scraping(self, user_id: int, search_terms: List[str], location: str = "Remote"):
        """
        Start scraping jobs for a specific user
        
        Args:
            user_id: User ID to scrape jobs for
            search_terms: List of job titles/keywords to search for
            location: Job location preference
        """
        logger.info(f"🔍 Starting job scraping for user {user_id}")
        
        try:
            for board_name, config in self.job_boards.items():
                if not config["enabled"]:
                    continue
                
                logger.info(f"📋 Scraping {board_name} for user {user_id}")
                
                # Scrape jobs from this board
                jobs = await self._scrape_job_board(
                    board=board_name,
                    config=config,
                    search_terms=search_terms,
                    location=location,
                    user_id=user_id
                )
                
                # Process discovered jobs
                for job_data in jobs:
                    await self._process_discovered_job(user_id, job_data)
                
                # Rate limiting between boards
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"❌ Scraping failed for user {user_id}: {e}")
    
    async def _scrape_job_board(
        self, 
        board: str, 
        config: Dict, 
        search_terms: List[str], 
        location: str,
        user_id: int
    ) -> List[Dict]:
        """
        Scrape jobs from a specific job board
        
        Args:
            board: Job board name
            config: Board configuration
            search_terms: Search terms
            location: Location preference
            user_id: User ID
            
        Returns:
            List of job data dictionaries
        """
        jobs = []
        
        if board == "linkedin":
            # Mock LinkedIn scraping - replace with real implementation
            jobs = await self._mock_linkedin_scraper(search_terms, location)
        
        logger.info(f"📊 Found {len(jobs)} jobs on {board} for user {user_id}")
        return jobs
    
    async def _mock_linkedin_scraper(self, search_terms: List[str], location: str) -> List[Dict]:
        """
        Mock LinkedIn scraper - replace with real scraping logic
        
        For now, returns sample job data to test the system
        """
        # Simulate network delay
        await asyncio.sleep(1)
        
        # Mock job data - replace with real scraping
        mock_jobs = [
            {
                "title": f"Senior {term} Engineer",
                "company": f"TechCorp Inc",
                "location": location,
                "url": f"https://linkedin.com/jobs/view/123456{i}",
                "description": f"We are looking for an experienced {term} engineer to join our team...",
                "posted_date": "2024-01-15",
                "job_type": "Full-time",
                "remote": location.lower() == "remote",
                "salary_min": 80000,
                "salary_max": 120000,
                "requirements": [
                    f"5+ years {term} experience",
                    "Bachelor's degree in Computer Science",
                    "Strong problem-solving skills"
                ]
            }
            for i, term in enumerate(search_terms[:3])  # Limit to 3 jobs for testing
        ]
        
        return mock_jobs
    
    async def _process_discovered_job(self, user_id: int, job_data: Dict):
        """
        Process a discovered job and emit events
        
        Args:
            user_id: User ID
            job_data: Job data dictionary
        """
        try:
            # Check if job already exists
            if await self._job_already_exists(job_data["url"], user_id):
                logger.debug(f"⏭️ Job already exists: {job_data['url']}")
                return
            
            # Store job in database
            job_id = await self._store_job_application(user_id, job_data)
            
            # Emit job discovered event
            await self._emit_job_discovered_event(user_id, job_id, job_data)
            
            # Emit job analysis request event
            await self._emit_job_analysis_request(user_id, job_id, job_data)
            
        except Exception as e:
            logger.error(f"❌ Failed to process job {job_data.get('url')}: {e}")
    
    async def _job_already_exists(self, job_url: str, user_id: int) -> bool:
        """Check if job already exists for user"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            
            result = await session.execute(
                select(JobApplication).where(
                    JobApplication.url == job_url,
                    JobApplication.user_id == user_id
                )
            )
            return result.scalar_one_or_none() is not None
    
    async def _store_job_application(self, user_id: int, job_data: Dict) -> int:
        """Store job application in database"""
        async with AsyncSessionLocal() as session:
            job_app = JobApplication(
                user_id=user_id,
                company=job_data["company"],
                position=job_data["title"],
                url=job_data["url"],
                job_description=job_data["description"],
                salary_min=job_data.get("salary_min"),
                salary_max=job_data.get("salary_max"),
                location=job_data["location"],
                remote=job_data.get("remote", False),
                status=ApplicationStatus.DISCOVERED,
                source="linkedin",  # TODO: make dynamic
                extra_data={
                    "requirements": job_data.get("requirements", []),
                    "job_type": job_data.get("job_type"),
                    "posted_date": job_data.get("posted_date")
                }
            )
            
            session.add(job_app)
            await session.commit()
            await session.refresh(job_app)
            
            logger.info(f"💾 Stored job application {job_app.id} for user {user_id}")
            return job_app.id
    
    async def _emit_job_discovered_event(self, user_id: int, job_id: int, job_data: Dict):
        """Emit job discovered event"""
        event = JobDiscoveredEvent(
            user_id=user_id,
            job_url=job_data["url"],
            company=job_data["company"],
            position=job_data["title"],
            data={
                "job_id": job_id,
                "location": job_data["location"],
                "remote": job_data.get("remote", False),
                "salary_range": f"{job_data.get('salary_min', 0)}-{job_data.get('salary_max', 0)}",
                "source": "linkedin"
            }
        )
        
        await self.publish_event(event)
        logger.info(f"📤 Published job discovered event for job {job_id}")
    
    async def _emit_job_analysis_request(self, user_id: int, job_id: int, job_data: Dict):
        """Emit job analysis request event for the analyzer agent"""
        from src.core.events import BaseEvent, EventType
        
        event = BaseEvent(
            event_type=EventType.JOB_ANALYZED,  # Will be processed by AnalyzerAgent
            user_id=user_id,
            data={
                "job_id": job_id,
                "job_description": job_data["description"],
                "requirements": job_data.get("requirements", []),
                "company": job_data["company"],
                "position": job_data["title"]
            }
        )
        
        await self.publish_event(event)
        logger.info(f"📤 Published job analysis request for job {job_id}")
    
    async def get_scraping_stats(self) -> Dict:
        """Get scraping statistics"""
        return {
            "agent_id": self.agent_id,
            "job_boards": self.job_boards,
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }