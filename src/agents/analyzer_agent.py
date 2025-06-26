# src/agents/analyzer_agent.py
import asyncio
import logging
from typing import Dict, List, Optional
import json

from src.agents.base_agent import BaseAgent
from src.core.events import BaseEvent, EventType, JobAnalyzedEvent
from src.core.database import AsyncSessionLocal
from src.api.models.schema import JobApplication
from src.generator.llm_interface import get_llm

logger = logging.getLogger(__name__)


class AnalyzerAgent(BaseAgent):
    """
    Agent responsible for analyzing job descriptions using LLMs
    
    Capabilities:
    - Extract key requirements from job descriptions
    - Identify required skills and technologies
    - Determine job seniority level and type
    - Calculate job match score for users
    - Generate analysis summaries for resume customization
    """
    
    def __init__(self, cell_id: str = "cell-001"):
        super().__init__("analyzer-agent", cell_id)
        
        # Analysis cache to avoid re-analyzing similar jobs
        self.analysis_cache = {}
        
        # LLM configuration for analysis
        self.analysis_config = {
            "temperature": 0.1,  # Low temperature for consistent analysis
            "max_tokens": 1000,
            "model": "gpt-3.5-turbo"  # Cheaper model for analysis
        }
    
    @property
    def subscribed_events(self) -> List[EventType]:
        return [EventType.JOB_ANALYZED]  # Listen for job analysis requests
    
    @property
    def consumer_group_id(self) -> str:
        return f"{self.cell_id}-analyzer-group"
    
    async def process_event(self, event: BaseEvent) -> None:
        """
        Process job analysis request events
        
        Args:
            event: Job analysis request event
        """
        try:
            job_id = event.data.get("job_id")
            job_description = event.data.get("job_description")
            company = event.data.get("company")
            position = event.data.get("position")
            
            if not all([job_id, job_description]):
                logger.error(f"❌ Missing required data in analysis event {event.event_id}")
                return
            
            logger.info(f"🔍 Analyzing job {job_id} for user {event.user_id}")
            
            # Perform job analysis
            analysis_result = await self._analyze_job_description(
                job_description=job_description,
                company=company,
                position=position
            )
            
            # Store analysis results
            await self._store_analysis_results(job_id, analysis_result)
            
            # Emit job analyzed event
            await self._emit_job_analyzed_event(event.user_id, job_id, analysis_result)
            
            logger.info(f"✅ Completed analysis for job {job_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze job: {e}")
            raise
    
    async def _analyze_job_description(
        self, 
        job_description: str, 
        company: str, 
        position: str
    ) -> Dict:
        """
        Analyze job description using LLM
        
        Args:
            job_description: The job description text
            company: Company name
            position: Job position title
            
        Returns:
            Dict containing analysis results
        """
        try:
            # Check cache first
            cache_key = self._get_cache_key(job_description)
            if cache_key in self.analysis_cache:
                logger.debug("📋 Using cached analysis result")
                return self.analysis_cache[cache_key]
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(job_description, company, position)
            
            # Get LLM response
            llm = get_llm()
            response = await llm.agenerate([prompt])
            analysis_text = response.generations[0][0].text.strip()
            
            # Parse LLM response
            analysis_result = self._parse_analysis_response(analysis_text)
            
            # Cache result
            self.analysis_cache[cache_key] = analysis_result
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ LLM analysis failed: {e}")
            # Return fallback analysis
            return self._create_fallback_analysis(job_description, company, position)
    
    def _get_cache_key(self, job_description: str) -> str:
        """Create cache key from job description"""
        import hashlib
        return hashlib.md5(job_description.encode()).hexdigest()
    
    def _create_analysis_prompt(self, job_description: str, company: str, position: str) -> str:
        """Create prompt for job analysis"""
        return f"""
Analyze the following job posting and extract key information in JSON format.

Company: {company}
Position: {position}

Job Description:
{job_description}

Please provide a JSON response with the following structure:
{{
    "required_skills": ["skill1", "skill2", ...],
    "preferred_skills": ["skill1", "skill2", ...],
    "technologies": ["tech1", "tech2", ...],
    "experience_level": "junior|mid|senior|lead",
    "job_type": "technical|management|hybrid",
    "key_responsibilities": ["resp1", "resp2", ...],
    "education_requirements": "bachelor|master|phd|none",
    "remote_friendly": true|false,
    "salary_indicators": "low|medium|high|not_specified",
    "company_size": "startup|small|medium|large|enterprise",
    "industry": "technology|finance|healthcare|other",
    "match_keywords": ["keyword1", "keyword2", ...],
    "red_flags": ["flag1", "flag2", ...],
    "summary": "Brief summary of the role and key requirements"
}}

Focus on extracting specific, actionable information that would help customize a resume.
"""
    
    def _parse_analysis_response(self, analysis_text: str) -> Dict:
        """Parse LLM analysis response"""
        try:
            # Try to extract JSON from response
            start = analysis_text.find('{')
            end = analysis_text.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = analysis_text[start:end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"⚠️ Failed to parse LLM response as JSON: {e}")
            # Return structured fallback
            return self._extract_keywords_fallback(analysis_text)
    
    def _extract_keywords_fallback(self, analysis_text: str) -> Dict:
        """Extract keywords as fallback when JSON parsing fails"""
        # Simple keyword extraction
        common_skills = [
            "python", "javascript", "java", "react", "node.js", "aws", "docker",
            "kubernetes", "sql", "postgresql", "mongodb", "redis", "git",
            "machine learning", "ai", "data science", "backend", "frontend",
            "full-stack", "devops", "cloud", "microservices", "api"
        ]
        
        text_lower = analysis_text.lower()
        found_skills = [skill for skill in common_skills if skill in text_lower]
        
        return {
            "required_skills": found_skills[:5],
            "preferred_skills": [],
            "technologies": found_skills,
            "experience_level": "mid",
            "job_type": "technical",
            "key_responsibilities": [],
            "education_requirements": "bachelor",
            "remote_friendly": "remote" in text_lower,
            "salary_indicators": "not_specified",
            "company_size": "medium",
            "industry": "technology",
            "match_keywords": found_skills,
            "red_flags": [],
            "summary": "Job analysis completed with keyword extraction fallback"
        }
    
    def _create_fallback_analysis(self, job_description: str, company: str, position: str) -> Dict:
        """Create fallback analysis when LLM fails"""
        return {
            "required_skills": ["python", "sql", "api development"],
            "preferred_skills": ["aws", "docker"],
            "technologies": ["python", "postgresql", "rest api"],
            "experience_level": "mid",
            "job_type": "technical",
            "key_responsibilities": ["software development", "code review", "testing"],
            "education_requirements": "bachelor",
            "remote_friendly": True,
            "salary_indicators": "not_specified",
            "company_size": "medium",
            "industry": "technology",
            "match_keywords": ["python", "software", "development"],
            "red_flags": [],
            "summary": f"Basic analysis for {position} at {company} (LLM analysis failed)",
            "fallback": True
        }
    
    async def _store_analysis_results(self, job_id: int, analysis_result: Dict):
        """Store analysis results in database"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select, update
            
            # Update job application with analysis results
            stmt = (
                update(JobApplication)
                .where(JobApplication.id == job_id)
                .values(
                    extra_data=JobApplication.extra_data.op('||')({
                        'analysis': analysis_result,
                        'analyzed_at': str(asyncio.get_event_loop().time())
                    })
                )
            )
            
            await session.execute(stmt)
            await session.commit()
            
            logger.info(f"💾 Stored analysis results for job {job_id}")
    
    async def _emit_job_analyzed_event(self, user_id: int, job_id: int, analysis_result: Dict):
        """Emit job analyzed event"""
        event = JobAnalyzedEvent(
            user_id=user_id,
            job_id=job_id,
            analysis_result=analysis_result
        )
        
        await self.publish_event(event)
        logger.info(f"📤 Published job analyzed event for job {job_id}")
    
    async def get_analysis_stats(self) -> Dict:
        """Get analysis statistics"""
        return {
            "agent_id": self.agent_id,
            "cache_size": len(self.analysis_cache),
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "analysis_config": self.analysis_config
        }
    
    def clear_cache(self):
        """Clear analysis cache"""
        self.analysis_cache.clear()
        logger.info("🧹 Analysis cache cleared")