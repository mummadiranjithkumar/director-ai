"""
Configuration module for loading environment variables and API keys.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_required_env_var(var_name: str) -> str:
    """Get required environment variable or raise exception."""
    value = os.getenv(var_name)
    if not value:
        raise Exception(f"Required environment variable {var_name} is not set")
    return value

# API Keys
RUNWAY_API_KEY = os.getenv('RUNWAY_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')

# Safe execution flags
DRY_RUN = os.getenv('DRY_RUN', 'False').lower() == 'true'
TEST_MODE = os.getenv('TEST_MODE', 'False').lower() == 'true'

# Configuration
print("✅ Configuration loaded successfully")
if DRY_RUN:
    print("🔒 DRY RUN MODE active")
if TEST_MODE:
    print("🧪 TEST MODE active")
print(f"✅ Runway API key configured")
print(f"✅ Gemini API key configured")
