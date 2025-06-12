# src/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    # Database
    database_url: str
    async_database_url: str
    
    # Redis
    redis_url: str
    
    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Resume Automation"
    
    # Security
    secret_key: str
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week
    
    # LinkedIn
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Scraping
    scrape_interval_hours: int = 6
    max_applications_per_day: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = 'utf-8'

settings = Settings()
