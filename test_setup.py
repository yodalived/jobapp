# Create a test script: test_setup.py
from src.core.config import settings

print("Testing configuration...")
print(f"Project: {settings.project_name}")
print(f"Database URL: {settings.database_url}")
print(f"Redis URL: {settings.redis_url}")
print("✅ Configuration loaded successfully!")
