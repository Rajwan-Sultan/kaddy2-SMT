# ===== app/config/settings.py =====
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings and configuration"""
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    MODEL_NAME: str = "gemini-2.5-flash-lite"
    MAX_OUTPUT_TOKENS: int = 2000
    TEMPERATURE: float = 0.2
    
    def validate(self):
        """Validate that required settings are present"""
        if not self.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

settings = Settings()