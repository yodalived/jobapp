#!/usr/bin/env python3
"""
Test script for email verification registration flow
"""
import asyncio
import sys
sys.path.append('.')

from src.core.email import email_service

async def test_email_service():
    print("Testing email service...")
    
    # Test if email service is configured
    print(f"SMTP configured: {email_service._is_configured()}")
    
    # Test sending verification email (will use console logging if not configured)
    success = await email_service.send_verification_email(
        "test@example.com", 
        "test-token-123"
    )
    
    print(f"Email send result: {success}")

if __name__ == "__main__":
    asyncio.run(test_email_service())