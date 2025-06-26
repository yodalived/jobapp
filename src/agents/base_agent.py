# src/agents/base_agent.py
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.core.events import BaseEvent, EventType
from src.core.event_bus import event_bus
from src.core.kafka_client import KafkaEventConsumer

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents in the system
    
    Agents are specialized components that:
    - Listen for specific event types
    - Process events according to their domain logic
    - Publish result events to trigger next steps
    - Maintain their own health and error handling
    """
    
    def __init__(self, agent_id: str, cell_id: str = "cell-001"):
        self.agent_id = agent_id
        self.cell_id = cell_id
        self.consumer: Optional[KafkaEventConsumer] = None
        self.running = False
        self.health_status = "initializing"
        
        # Metrics
        self.events_processed = 0
        self.events_failed = 0
        self.last_activity = None
        
        logger.info(f"🤖 Agent {self.agent_id} initialized for cell {self.cell_id}")
    
    @property
    @abstractmethod
    def subscribed_events(self) -> List[EventType]:
        """Return list of event types this agent subscribes to"""
        pass
    
    @property
    @abstractmethod
    def consumer_group_id(self) -> str:
        """Return the Kafka consumer group ID for this agent"""
        pass
    
    @abstractmethod
    async def process_event(self, event: BaseEvent) -> None:
        """
        Process an incoming event
        
        Args:
            event: The event to process
        """
        pass
    
    async def start(self):
        """Start the agent and begin consuming events"""
        if self.running:
            return
        
        try:
            # Create topics list from subscribed events
            topics = [f"resume-automation.{event_type.value}" for event_type in self.subscribed_events]
            
            # Create consumer
            self.consumer = event_bus.create_consumer(
                group_id=self.consumer_group_id,
                topics=topics
            )
            
            # Register event handlers
            for event_type in self.subscribed_events:
                self.consumer.register_handler(event_type, self._handle_event)
            
            # Start consumer
            await self.consumer.start()
            
            self.running = True
            self.health_status = "healthy"
            
            logger.info(f"✅ Agent {self.agent_id} started, subscribed to: {[et.value for et in self.subscribed_events]}")
            
            # Start consuming events
            await self.consumer.consume_events()
            
        except Exception as e:
            self.health_status = "failed"
            logger.error(f"❌ Failed to start agent {self.agent_id}: {e}")
            raise
    
    async def stop(self):
        """Stop the agent"""
        self.running = False
        self.health_status = "stopped"
        
        if self.consumer:
            await self.consumer.stop()
        
        logger.info(f"👋 Agent {self.agent_id} stopped")
    
    async def _handle_event(self, event: BaseEvent):
        """Internal event handler that wraps process_event with error handling and metrics"""
        try:
            logger.debug(f"🎯 Agent {self.agent_id} processing event {event.event_id}")
            
            # Update activity
            from datetime import datetime
            self.last_activity = datetime.utcnow()
            
            # Process the event
            await self.process_event(event)
            
            # Update metrics
            self.events_processed += 1
            
            logger.debug(f"✅ Agent {self.agent_id} completed event {event.event_id}")
            
        except Exception as e:
            self.events_failed += 1
            logger.error(f"❌ Agent {self.agent_id} failed to process event {event.event_id}: {e}")
            
            # Publish error event for monitoring
            await self._publish_error_event(event, str(e))
    
    async def _publish_error_event(self, original_event: BaseEvent, error_message: str):
        """Publish an error event for monitoring and alerting"""
        try:
            from src.core.events import BaseEvent, EventType
            
            error_event = BaseEvent(
                event_type=EventType.AGENT_HEALTH_CHECK,  # We'll use this for errors too
                user_id=original_event.user_id,
                cell_id=self.cell_id,
                correlation_id=original_event.event_id,
                data={
                    "agent_id": self.agent_id,
                    "error": error_message,
                    "original_event_id": original_event.event_id,
                    "original_event_type": original_event.event_type
                },
                metadata={
                    "severity": "error",
                    "component": "agent"
                }
            )
            
            await event_bus.publish(error_event)
            
        except Exception as e:
            # Don't let error publishing fail the agent
            logger.error(f"Failed to publish error event: {e}")
    
    async def publish_event(self, event: BaseEvent) -> bool:
        """
        Publish an event via the event bus
        
        Args:
            event: The event to publish
            
        Returns:
            bool: True if published successfully
        """
        return await event_bus.publish(event)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Return agent health status for monitoring"""
        return {
            "agent_id": self.agent_id,
            "cell_id": self.cell_id,
            "status": self.health_status,
            "running": self.running,
            "events_processed": self.events_processed,
            "events_failed": self.events_failed,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "subscribed_events": [et.value for et in self.subscribed_events]
        }