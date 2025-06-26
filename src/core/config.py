# src/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import os
import json

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    # Database
    database_url: str
    async_database_url: str
    
    # Redis
    redis_url: str
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    
    # API
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Resume Automation"

    # API Settings (optional)
    port: Optional[int] = 8048
    allowed_origins: Optional[List[str]] = None
    
    # Storage Configuration
    primary_backend: str = "local"  # Which backend to use by default
    
    # File Upload Settings
    allowed_file_types: List[str] = [".pdf", ".doc", ".docx", ".txt"]
    max_file_size_mb: int = 10
    
    # Security
    secret_key: str
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 week
    
    # LinkedIn
    linkedin_email: Optional[str] = None
    linkedin_password: Optional[str] = None
    
    # LLM Settings (ADD THESE)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_llm_provider: Optional[str] = "openai"  # or "anthropic"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    
    # Debug/Logging
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "text"  # "text" or "json"
    log_ingest_enabled: bool = False
    log_ingest_url: Optional[str] = None  # e.g., "http://localhost:9200"
    
    # Log ingestion resilience (anti-blocking)
    log_ingest_timeout_ms: int = 2000  # 2 second timeout
    log_ingest_queue_size: int = 1000  # Max queued messages
    log_ingest_retry_attempts: int = 3  # Retry failed sends
    log_ingest_latency_threshold_ms: int = 1000  # Circuit breaker threshold
    log_ingest_failure_threshold: int = 5  # Open circuit after N failures
    log_ingest_drop_policy: str = "oldest"  # "oldest" or "newest"
    
    # Frontend
    next_public_api_url: Optional[str] = None
    
    # Email/SMTP Settings
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None
    smtp_from_name: str = "ResumeAI Platform"

    # Scraping
    scrape_interval_hours: int = 6
    max_applications_per_day: int = 50
    
    @property
    def minio_config(self) -> Optional[Dict[str, Any]]:
        """Load MinIO configuration"""
        # Option 1: From JSON env var
        if os.getenv("MINIO_CONFIG"):
            return json.loads(os.getenv("MINIO_CONFIG"))
        
        # Option 2: From individual env vars
        if os.getenv("MINIO_ENDPOINT_URL"):
            return {
                "endpoint_url": os.getenv("MINIO_ENDPOINT_URL"),
                "access_key": os.getenv("MINIO_ACCESS_KEY"),
                "secret_key": os.getenv("MINIO_SECRET_KEY"),
                "bucket_name": os.getenv("MINIO_BUCKET_NAME"),
                "secure": os.getenv("MINIO_SECURE", "false").lower() == "true"
            }
        
        return None
    
    @property
    def aws_s3_config(self) -> Optional[Dict[str, Any]]:
        """Load AWS S3 configuration"""
        if os.getenv("AWS_S3_CONFIG"):
            return json.loads(os.getenv("AWS_S3_CONFIG"))
        
        if os.getenv("AWS_ACCESS_KEY_ID"):
            return {
                "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
                "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
                "bucket_name": os.getenv("AWS_S3_BUCKET_NAME"),
                "region": os.getenv("AWS_REGION", "us-east-1"),
                "storage_class": os.getenv("AWS_S3_STORAGE_CLASS", "STANDARD")
            }
        
        return None
    
    @property
    def azure_blob_config(self) -> Optional[Dict[str, Any]]:
        """Load Azure Blob configuration"""
        if os.getenv("AZURE_BLOB_CONFIG"):
            return json.loads(os.getenv("AZURE_BLOB_CONFIG"))
        
        if os.getenv("AZURE_ACCOUNT_NAME"):
            return {
                "account_name": os.getenv("AZURE_ACCOUNT_NAME"),
                "account_key": os.getenv("AZURE_ACCOUNT_KEY"),
                "container_name": os.getenv("AZURE_CONTAINER_NAME"),
                "tier": os.getenv("AZURE_BLOB_TIER", "Hot")
            }
        
        return None
    
    # Local storage path (for development)
    local_storage_path: str = "./storage"


    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = 'utf-8'
        extra = "ignore"

settings = Settings()
