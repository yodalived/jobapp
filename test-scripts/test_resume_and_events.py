#!/usr/bin/env python3
"""
Test resume generation and Kafka event publishing
"""
import asyncio
import httpx
import json
import os
from dotenv import load_dotenv
from src.core.kafka_client import KafkaEventProducer
from src.core.events import JobDiscoveredEvent, ResumeGenerationRequestedEvent

# Load environment variables
load_dotenv()

async def test_resume_generation():
    """Test resume generation endpoint"""
    async with httpx.AsyncClient() as client:
        base_url = os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8048')
        
        # Login first
        login = await client.post(
            f"{base_url}/api/v1/auth/login",
            data={"username": "test@example.com", "password": "password123"}
        )
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test resume generation
        print("🔄 Testing resume generation...")
        resume_response = await client.post(
            f"{base_url}/api/v1/generator/generate-resume",
            headers=headers,
            params={"job_id": 1, "template": "modern_professional"}
        )
        
        if resume_response.status_code == 200:
            result = resume_response.json()
            print(f"   ✅ Resume generation successful: {result}")
        else:
            print(f"   ❌ Resume generation failed: {resume_response.status_code} - {resume_response.text}")


async def test_kafka_events():
    """Test Kafka event publishing"""
    print("\n🔄 Testing Kafka event publishing...")
    
    try:
        # Create producer
        producer = KafkaEventProducer()
        await producer.start()
        print("   ✅ Kafka producer started")
        
        # Create test events
        job_event = JobDiscoveredEvent(
            user_id=1,
            job_url="https://example.com/test-job",
            company="TestCorp",
            position="Senior Python Developer"
        )
        
        resume_event = ResumeGenerationRequestedEvent(
            user_id=1,
            job_id=1,
            template="modern_professional"
        )
        
        # Publish events
        success1 = await producer.publish_event(job_event)
        success2 = await producer.publish_event(resume_event)
        
        if success1 and success2:
            print("   ✅ Events published successfully")
            print(f"      - Job discovered event: {job_event.event_id}")
            print(f"      - Resume generation event: {resume_event.event_id}")
        else:
            print("   ❌ Failed to publish some events")
        
        # Cleanup
        await producer.stop()
        print("   ✅ Kafka producer stopped")
        
    except Exception as e:
        print(f"   ❌ Kafka test failed: {e}")


async def main():
    print("🧪 TESTING RESUME GENERATION & EVENTS\n")
    
    await test_resume_generation()
    await test_kafka_events()
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())