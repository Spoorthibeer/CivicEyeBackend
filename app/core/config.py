import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load the .env file from the root directory
load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "CivicEye AI Backend"
    PROJECT_VERSION: str = "2.0.0"
    
    # Supabase Credentials
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY")
    
    # Paths
    TESSERACT_PATH: str = os.getenv("TESSERACT_PATH")
    MODEL_PATH: str = os.getenv("MODEL_PATH", "CivicEye_v1.pt")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "TG_GOVT_SECURE_2026")

# Create a single instance to be used across the app
settings = Settings()