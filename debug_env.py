# debug_env.py
import os
from dotenv import load_dotenv

print("Current working directory:", os.getcwd())
print(".env file exists:", os.path.exists('.env'))

# Load .env file
load_dotenv()

# Check if variables are loaded
print("\nEnvironment variables:")
print("DATABASE_URL:", os.getenv('DATABASE_URL'))
print("REDIS_URL:", os.getenv('REDIS_URL'))
print("SECRET_KEY:", os.getenv('SECRET_KEY', 'NOT SET'))

# Also check if we're in the right directory
print("\nDirectory contents:")
for item in os.listdir('.'):
    print(f"  {item}")
