from google import genai
from config.settings import settings


class GeminiClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_client()
        return cls._instance
    
    def _initialize_client(self):
        try:
            self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            print("Gemini client initialized successfully")
        except Exception as e:
            print(f"Warning: Gemini client initialization failed: {e}")
            self.client = None
    
    def get_client(self):
        if self.client is None:
            raise Exception("Gemini client not available")
        return self.client


# Singleton instance
gemini_client = GeminiClient()
