# src/agents/optimizer_agent.py
import asyncio
import logging
from typing import Dict, List, Optional
import statistics

from src.agents.base_agent import BaseAgent
from src.core.events import BaseEvent, EventType
from src.core.database import AsyncSessionLocal
from src.api.models.schema import JobApplication, ResumeVersion, ApplicationStatus
from src.generator.llm_interface import get_llm

logger = logging.getLogger(__name__)


class OptimizerAgent(BaseAgent):
    """
    Agent responsible for optimizing resume effectiveness
    
    Capabilities:
    - Analyze resume performance metrics
    - A/B test different resume versions
    - Learn from application outcomes
    - Suggest resume improvements
    - Optimize for ATS systems
    - Track success patterns across users
    """
    
    def __init__(self, cell_id: str = "cell-001"):
        super().__init__("optimizer-agent", cell_id)
        
        # Performance tracking
        self.optimization_cache = {}
        self.success_patterns = {}
        
        # Optimization thresholds
        self.min_applications_for_analysis = 5
        self.success_rate_threshold = 0.2  # 20% response rate is good
        
        # Optimization statistics
        self.optimizations_performed = 0
        self.patterns_discovered = 0
    
    @property
    def subscribed_events(self) -> List[EventType]:
        return [
            EventType.RESUME_GENERATED,
            EventType.APPLICATION_STATUS_UPDATED,
            EventType.RESUME_OPTIMIZATION_REQUESTED
        ]
    
    @property
    def consumer_group_id(self) -> str:
        return f"{self.cell_id}-optimizer-group"
    
    async def process_event(self, event: BaseEvent) -> None:
        """
        Process optimization-related events
        
        Args:
            event: Event to process
        """
        try:
            if event.event_type == EventType.RESUME_GENERATED:
                await self._handle_resume_generated(event)
            elif event.event_type == EventType.APPLICATION_STATUS_UPDATED:
                await self._handle_application_status_update(event)
            elif event.event_type == EventType.RESUME_OPTIMIZATION_REQUESTED:
                await self._handle_optimization_request(event)
            else:
                logger.warning(f"⚠️ Unknown event type: {event.event_type}")
                
        except Exception as e:
            logger.error(f"❌ Failed to process optimization event: {e}")
            raise
    
    async def _handle_resume_generated(self, event: BaseEvent):
        """Handle new resume generation - track for future optimization"""
        user_id = event.user_id
        job_id = event.data.get("job_id")
        version_name = event.data.get("version_name")
        
        logger.info(f"📊 Tracking new resume for optimization: {version_name}")
        
        # Initialize tracking for this resume
        await self._initialize_resume_tracking(user_id, job_id, version_name)
        
        # Check if user has enough data for optimization suggestions
        await self._check_optimization_opportunity(user_id)
    
    async def _handle_application_status_update(self, event: BaseEvent):
        """Handle application status updates - learn from outcomes"""
        user_id = event.user_id
        job_id = event.data.get("job_id")
        old_status = event.data.get("old_status")
        new_status = event.data.get("new_status")
        
        logger.info(f"📈 Processing status update for job {job_id}: {old_status} -> {new_status}")
        
        # Update resume performance metrics
        await self._update_resume_performance(user_id, job_id, new_status)
        
        # Learn success patterns
        await self._learn_success_patterns(user_id, job_id, new_status)
        
        # Trigger optimization if we have enough data
        if new_status in [ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER]:
            await self._analyze_successful_pattern(user_id, job_id)
    
    async def _handle_optimization_request(self, event: BaseEvent):
        """Handle explicit optimization requests"""
        user_id = event.user_id
        optimization_type = event.data.get("optimization_type", "general")
        
        logger.info(f"🔧 Processing optimization request for user {user_id}")
        
        # Perform optimization analysis
        recommendations = await self._generate_optimization_recommendations(
            user_id, optimization_type
        )
        
        # Emit optimization results
        await self._emit_optimization_results(user_id, recommendations)
    
    async def _initialize_resume_tracking(self, user_id: int, job_id: int, version_name: str):
        """Initialize tracking for a new resume"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select, update
            
            # Update resume version with initial tracking data
            stmt = (
                update(ResumeVersion)
                .where(
                    ResumeVersion.user_id == user_id,
                    ResumeVersion.version_name == version_name
                )
                .values(
                    extra_data=ResumeVersion.extra_data.op('||')({
                        'tracking': {
                            'created_at': str(asyncio.get_event_loop().time()),
                            'job_id': job_id,
                            'applications_sent': 0,
                            'responses_received': 0,
                            'interviews_received': 0
                        }
                    })
                )
            )
            
            await session.execute(stmt)
            await session.commit()
    
    async def _update_resume_performance(self, user_id: int, job_id: int, new_status: str):
        """Update performance metrics for the resume used in this application"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select, update
            
            # Find the resume version used for this job
            job_result = await session.execute(
                select(JobApplication).where(JobApplication.id == job_id)
            )
            job = job_result.scalar_one_or_none()
            
            if not job or not job.resume_version:
                return
            
            # Update resume version metrics
            updates = {}
            
            if new_status == ApplicationStatus.ACKNOWLEDGED:
                updates['responses_received'] = ResumeVersion.extra_data['tracking']['responses_received'].astext.cast(int) + 1
            elif new_status in [ApplicationStatus.INTERVIEW, ApplicationStatus.SCREENING]:
                updates['interviews_received'] = ResumeVersion.extra_data['tracking']['interviews_received'].astext.cast(int) + 1
            
            if updates:
                stmt = (
                    update(ResumeVersion)
                    .where(ResumeVersion.version_name == job.resume_version)
                    .values(extra_data=ResumeVersion.extra_data.op('||')({
                        'tracking': updates
                    }))
                )
                
                await session.execute(stmt)
                await session.commit()
                
                logger.debug(f"📊 Updated performance metrics for resume {job.resume_version}")
    
    async def _learn_success_patterns(self, user_id: int, job_id: int, new_status: str):
        """Learn patterns from successful applications"""
        if new_status not in [ApplicationStatus.INTERVIEW, ApplicationStatus.OFFER]:
            return
        
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            
            # Get job and analysis data
            job_result = await session.execute(
                select(JobApplication).where(JobApplication.id == job_id)
            )
            job = job_result.scalar_one_or_none()
            
            if not job or not job.extra_data.get('analysis'):
                return
            
            analysis = job.extra_data['analysis']
            
            # Extract success patterns
            pattern_key = f"{analysis.get('job_type', 'unknown')}_{analysis.get('experience_level', 'unknown')}"
            
            if pattern_key not in self.success_patterns:
                self.success_patterns[pattern_key] = {
                    'successful_applications': 0,
                    'total_applications': 0,
                    'common_skills': {},
                    'successful_templates': {},
                    'success_rate': 0.0
                }
            
            pattern = self.success_patterns[pattern_key]
            pattern['successful_applications'] += 1
            
            # Track successful skills
            for skill in analysis.get('required_skills', []):
                pattern['common_skills'][skill] = pattern['common_skills'].get(skill, 0) + 1
            
            # Track successful template
            if job.resume_version:
                template = job.resume_version.split('_')[-1] if '_' in job.resume_version else 'unknown'
                pattern['successful_templates'][template] = pattern['successful_templates'].get(template, 0) + 1
            
            self.patterns_discovered += 1
            logger.info(f"🎯 Learned success pattern for {pattern_key}")
    
    async def _check_optimization_opportunity(self, user_id: int):
        """Check if user has enough data for optimization suggestions"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select, func
            
            # Count total applications
            result = await session.execute(
                select(func.count(JobApplication.id))
                .where(JobApplication.user_id == user_id)
            )
            total_applications = result.scalar()
            
            if total_applications >= self.min_applications_for_analysis:
                logger.info(f"🔍 User {user_id} has {total_applications} applications - triggering optimization analysis")
                await self._trigger_optimization_analysis(user_id)
    
    async def _trigger_optimization_analysis(self, user_id: int):
        """Trigger optimization analysis for a user"""
        from src.core.events import BaseEvent, EventType
        
        event = BaseEvent(
            event_type=EventType.RESUME_OPTIMIZATION_REQUESTED,
            user_id=user_id,
            data={
                "optimization_type": "performance_analysis",
                "trigger": "automatic"
            }
        )
        
        await self.publish_event(event)
    
    async def _generate_optimization_recommendations(self, user_id: int, optimization_type: str) -> Dict:
        """Generate optimization recommendations for a user"""
        try:
            # Analyze user's application history
            user_stats = await self._analyze_user_performance(user_id)
            
            # Generate recommendations using LLM
            recommendations = await self._generate_llm_recommendations(user_stats)
            
            # Add pattern-based recommendations
            pattern_recommendations = self._get_pattern_recommendations(user_stats)
            recommendations.update(pattern_recommendations)
            
            self.optimizations_performed += 1
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Failed to generate recommendations: {e}")
            return {"error": str(e)}
    
    async def _analyze_user_performance(self, user_id: int) -> Dict:
        """Analyze user's application performance"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select, func
            
            # Get application statistics
            applications_result = await session.execute(
                select(
                    func.count(JobApplication.id).label('total'),
                    func.count(
                        JobApplication.id.case(
                            (JobApplication.status == ApplicationStatus.ACKNOWLEDGED, 1)
                        )
                    ).label('acknowledged'),
                    func.count(
                        JobApplication.id.case(
                            (JobApplication.status.in_([ApplicationStatus.INTERVIEW, ApplicationStatus.SCREENING]), 1)
                        )
                    ).label('interviews'),
                    func.count(
                        JobApplication.id.case(
                            (JobApplication.status == ApplicationStatus.OFFER, 1)
                        )
                    ).label('offers')
                ).where(JobApplication.user_id == user_id)
            )
            
            stats = applications_result.first()
            
            # Calculate rates
            total = stats.total or 1  # Avoid division by zero
            response_rate = (stats.acknowledged or 0) / total
            interview_rate = (stats.interviews or 0) / total
            offer_rate = (stats.offers or 0) / total
            
            return {
                "total_applications": total,
                "response_rate": response_rate,
                "interview_rate": interview_rate,
                "offer_rate": offer_rate,
                "performance_rating": self._calculate_performance_rating(response_rate, interview_rate, offer_rate)
            }
    
    def _calculate_performance_rating(self, response_rate: float, interview_rate: float, offer_rate: float) -> str:
        """Calculate overall performance rating"""
        if offer_rate > 0.1:  # 10%+ offer rate
            return "excellent"
        elif interview_rate > 0.15:  # 15%+ interview rate
            return "good"
        elif response_rate > 0.2:  # 20%+ response rate
            return "average"
        else:
            return "needs_improvement"
    
    async def _generate_llm_recommendations(self, user_stats: Dict) -> Dict:
        """Generate recommendations using LLM"""
        try:
            prompt = f"""
Analyze the following resume performance data and provide optimization recommendations:

Performance Statistics:
- Total Applications: {user_stats['total_applications']}
- Response Rate: {user_stats['response_rate']:.2%}
- Interview Rate: {user_stats['interview_rate']:.2%}
- Offer Rate: {user_stats['offer_rate']:.2%}
- Performance Rating: {user_stats['performance_rating']}

Industry Benchmarks:
- Good Response Rate: 20%+
- Good Interview Rate: 15%+
- Good Offer Rate: 5%+

Please provide specific, actionable recommendations for:
1. Resume content improvements
2. Application strategy adjustments
3. Skills to highlight or develop
4. Template or format changes

Format your response as practical advice.
"""
            
            llm = get_llm()
            response = await llm.agenerate([prompt])
            recommendations_text = response.generations[0][0].text.strip()
            
            return {
                "llm_recommendations": recommendations_text,
                "analysis_timestamp": str(asyncio.get_event_loop().time())
            }
            
        except Exception as e:
            logger.error(f"❌ LLM recommendation generation failed: {e}")
            return {"llm_recommendations": "Unable to generate AI recommendations at this time."}
    
    def _get_pattern_recommendations(self, user_stats: Dict) -> Dict:
        """Get recommendations based on learned success patterns"""
        recommendations = []
        
        # Analyze performance against thresholds
        if user_stats['response_rate'] < self.success_rate_threshold:
            recommendations.append("Consider updating your resume summary to better match job requirements")
            recommendations.append("Try using different templates for different job types")
        
        if user_stats['interview_rate'] < 0.1:
            recommendations.append("Focus on quantifying your achievements with specific metrics")
            recommendations.append("Ensure your skills section matches the most common job requirements")
        
        # Add pattern-based recommendations
        best_patterns = sorted(
            self.success_patterns.items(),
            key=lambda x: x[1].get('success_rate', 0),
            reverse=True
        )[:3]
        
        if best_patterns:
            recommendations.append(f"Consider targeting {best_patterns[0][0]} roles - highest success rate in our data")
        
        return {
            "pattern_recommendations": recommendations,
            "success_patterns_analyzed": len(self.success_patterns)
        }
    
    async def _emit_optimization_results(self, user_id: int, recommendations: Dict):
        """Emit optimization results event"""
        from src.core.events import BaseEvent, EventType
        
        event = BaseEvent(
            event_type=EventType.RESUME_OPTIMIZED,
            user_id=user_id,
            data={
                "recommendations": recommendations,
                "optimization_timestamp": str(asyncio.get_event_loop().time())
            }
        )
        
        await self.publish_event(event)
        logger.info(f"📤 Published optimization results for user {user_id}")
    
    async def _analyze_successful_pattern(self, user_id: int, job_id: int):
        """Analyze a successful application to extract patterns"""
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            
            # Get successful job details
            job_result = await session.execute(
                select(JobApplication).where(JobApplication.id == job_id)
            )
            job = job_result.scalar_one_or_none()
            
            if job and job.extra_data.get('analysis'):
                analysis = job.extra_data['analysis']
                logger.info(f"🎉 Analyzing successful pattern: {analysis.get('job_type')} role at {job.company}")
                
                # This data will be used in future recommendations
                # The pattern learning is handled in _learn_success_patterns
    
    async def get_optimization_stats(self) -> Dict:
        """Get optimization statistics"""
        return {
            "agent_id": self.agent_id,
            "optimizations_performed": self.optimizations_performed,
            "patterns_discovered": self.patterns_discovered,
            "success_patterns_count": len(self.success_patterns),
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "performance_thresholds": {
                "min_applications_for_analysis": self.min_applications_for_analysis,
                "success_rate_threshold": self.success_rate_threshold
            }
        }
    
    def get_success_patterns(self) -> Dict:
        """Get learned success patterns"""
        return self.success_patterns.copy()