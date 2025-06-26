# src/core/event_bus.py
"""
Event Bus - High-level interface for event-driven architecture
Provides easy-to-use methods for publishing and subscribing to events
"""
import asyncio
import logging
from typing import Callable, List, Optional

from src.core.events import BaseEvent, EventType
from src.core.kafka_client import KafkaEventConsumer, get_event_producer

logger = logging.getLogger(__name__)


class EventBus:
    """
    Central event bus for the application
    Provides unified interface for event publishing and subscription
    """
    
    def __init__(self):
        self.consumers: List[KafkaEventConsumer] = []
        self.running = False
    
    async def publish(self, event: BaseEvent) -> bool:
        """
        Publish an event to the event bus
        
        Args:
            event: The event to publish
            
        Returns:
            bool: True if published successfully
        """
        try:
            producer = await get_event_producer()
            return await producer.publish_event(event)
        except Exception as e:
            logger.error(f"❌ Failed to publish event: {e}")
            return False
    
    def create_consumer(self, group_id: str, topics: List[str]) -> KafkaEventConsumer:
        """
        Create a new event consumer
        
        Args:
            group_id: Consumer group ID
            topics: List of topics to subscribe to
            
        Returns:
            KafkaEventConsumer: The created consumer
        """
        consumer = KafkaEventConsumer(group_id, topics)
        self.consumers.append(consumer)
        return consumer
    
    async def start_consumers(self):
        """Start all registered consumers"""
        if self.running:
            return
            
        self.running = True
        
        # Start all consumers
        for consumer in self.consumers:
            await consumer.start()
        
        # Start consumption tasks
        tasks = []
        for consumer in self.consumers:
            task = asyncio.create_task(consumer.consume_events())
            tasks.append(task)
        
        logger.info(f"✅ Started {len(self.consumers)} event consumers")
        
        # Wait for all tasks (they run indefinitely)
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop_consumers(self):
        """Stop all consumers"""
        self.running = False
        
        for consumer in self.consumers:
            await consumer.stop()
        
        logger.info("👋 All event consumers stopped")


# Global event bus instance
event_bus = EventBus()


# Convenience functions for common event operations
async def publish_job_discovered(user_id: int, job_url: str, company: str, position: str, **kwargs):
    """Publish a job discovered event"""
    from src.core.events import JobDiscoveredEvent
    
    event = JobDiscoveredEvent(
        user_id=user_id,
        job_url=job_url,
        company=company,
        position=position,
        **kwargs
    )
    return await event_bus.publish(event)


async def publish_resume_generation_requested(user_id: int, job_id: int, template: str = "modern_professional", **kwargs):
    """Publish a resume generation requested event"""
    from src.core.events import ResumeGenerationRequestedEvent
    
    event = ResumeGenerationRequestedEvent(
        user_id=user_id,
        job_id=job_id,
        template=template,
        **kwargs
    )
    return await event_bus.publish(event)


async def publish_resume_generated(user_id: int, job_id: int, resume_url: str, version_name: str, **kwargs):
    """Publish a resume generated event"""
    from src.core.events import ResumeGeneratedEvent
    
    event = ResumeGeneratedEvent(
        user_id=user_id,
        job_id=job_id,
        resume_url=resume_url,
        version_name=version_name,
        **kwargs
    )
    return await event_bus.publish(event)


async def publish_workflow_started(user_id: int, workflow_id: str, workflow_type: str, **kwargs):
    """Publish a workflow started event"""
    from src.core.events import WorkflowStartedEvent
    
    event = WorkflowStartedEvent(
        user_id=user_id,
        workflow_id=workflow_id,
        workflow_type=workflow_type,
        **kwargs
    )
    return await event_bus.publish(event)


async def publish_workflow_completed(user_id: int, workflow_id: str, results: dict, **kwargs):
    """Publish a workflow completed event"""
    from src.core.events import WorkflowCompletedEvent
    
    event = WorkflowCompletedEvent(
        user_id=user_id,
        workflow_id=workflow_id,
        results=results,
        **kwargs
    )
    return await event_bus.publish(event)