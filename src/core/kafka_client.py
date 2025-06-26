# src/core/kafka_client.py
import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError

from src.core.config import settings
from src.core.events import BaseEvent, EventType

logger = logging.getLogger(__name__)


class KafkaEventProducer:
    """Kafka producer for publishing events"""
    
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.bootstrap_servers = settings.kafka_bootstrap_servers
        
    async def start(self):
        """Start the Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                retry_backoff_ms=1000,
                request_timeout_ms=30000,
            )
            await self.producer.start()
            logger.info(f"✅ Kafka producer started with servers: {self.bootstrap_servers}")
        except KafkaConnectionError as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to start Kafka producer: {e}")
            raise
    
    async def stop(self):
        """Stop the Kafka producer"""
        if self.producer:
            await self.producer.stop()
            logger.info("👋 Kafka producer stopped")
    
    async def publish_event(self, event: BaseEvent, topic: Optional[str] = None) -> bool:
        """
        Publish an event to Kafka
        
        Args:
            event: The event to publish
            topic: Optional topic override (defaults to event type)
        
        Returns:
            bool: True if published successfully
        """
        if not self.producer:
            logger.error("Kafka producer not started")
            return False
        
        try:
            # Use event type as topic if not specified
            topic = topic or f"resume-automation.{event.event_type.value}"
            
            # Use user_id as partition key for even distribution
            key = f"user_{event.user_id}"
            
            # Convert event to dict for serialization
            event_data = event.model_dump()
            
            # Send event
            await self.producer.send_and_wait(
                topic=topic,
                key=key,
                value=event_data
            )
            
            logger.debug(f"📤 Published event {event.event_id} to topic {topic}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to publish event {event.event_id}: {e}")
            return False


class KafkaEventConsumer:
    """Kafka consumer for processing events"""
    
    def __init__(self, group_id: str, topics: List[str]):
        self.group_id = group_id
        self.topics = topics
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.bootstrap_servers = settings.kafka_bootstrap_servers
        self.handlers: Dict[EventType, List[Callable]] = {}
        self.running = False
        
    async def start(self):
        """Start the Kafka consumer"""
        try:
            self.consumer = AIOKafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                auto_commit_interval_ms=5000,
            )
            await self.consumer.start()
            logger.info(f"✅ Kafka consumer started for group {self.group_id}, topics: {self.topics}")
        except KafkaConnectionError as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to start Kafka consumer: {e}")
            raise
    
    async def stop(self):
        """Stop the Kafka consumer"""
        self.running = False
        if self.consumer:
            await self.consumer.stop()
            logger.info(f"👋 Kafka consumer stopped for group {self.group_id}")
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """Register an event handler for a specific event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(f"📝 Registered handler for {event_type.value}")
    
    async def consume_events(self):
        """Start consuming events and dispatch to handlers"""
        if not self.consumer:
            raise RuntimeError("Consumer not started")
        
        self.running = True
        logger.info(f"🎯 Starting event consumption for group {self.group_id}")
        
        try:
            async for message in self.consumer:
                if not self.running:
                    break
                    
                try:
                    # Parse event data
                    event_data = message.value
                    event_type = EventType(event_data.get('event_type'))
                    
                    # Create BaseEvent object
                    event = BaseEvent(**event_data)
                    
                    logger.debug(f"📥 Received event {event.event_id} of type {event_type.value}")
                    
                    # Dispatch to handlers
                    if event_type in self.handlers:
                        for handler in self.handlers[event_type]:
                            try:
                                if asyncio.iscoroutinefunction(handler):
                                    await handler(event)
                                else:
                                    handler(event)
                            except Exception as e:
                                logger.error(f"❌ Handler failed for event {event.event_id}: {e}")
                    else:
                        logger.warning(f"⚠️ No handlers registered for event type {event_type.value}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to process message: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error in event consumption: {e}")
            raise


# Global producer instance
_producer: Optional[KafkaEventProducer] = None

async def get_event_producer() -> KafkaEventProducer:
    """Get the global event producer instance"""
    global _producer
    if not _producer:
        _producer = KafkaEventProducer()
        await _producer.start()
    return _producer

async def cleanup_event_producer():
    """Clean up the global event producer"""
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None