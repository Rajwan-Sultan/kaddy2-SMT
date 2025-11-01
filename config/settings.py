import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # API Keys
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Model Configuration
    MODEL_NAME: str = "gemini-2.5-flash-lite"
    TEMPERATURE: float = 0
    MAX_OUTPUT_TOKENS: int = 1000
    
    # File Configuration
    TEMP_FILE_DIR: str = "/tmp"
    ALLOWED_AUDIO_EXTENSIONS: dict = {
        'flac': 'audio/flac',
        'mp3': 'audio/mp3',
        'm4a': 'audio/m4a',
        'mpeg': 'audio/mpeg',
        'mpga': 'audio/mpga',
        'mp4': 'audio/mp4',
        'ogg': 'audio/ogg',
        'pcm': 'audio/pcm',
        'wav': 'audio/wav',
        'webm': 'audio/webm'
    }
    
    # Prompt Configuration
    SYSTEM_PROMPT: str = """You are an expert fraud detection analyst specializing in telecommunications scams.Strictly remove any markdown formatting from your response.
    # CLASSIFICATION CRITERIA
    ## CLASSIFY AS "SCAM" IF ANY OF THESE RED FLAGS ARE PRESENT:
    - **Urgency & Pressure**: Immediate threats, limited-time offers, demands for quick action
    - **Suspicious Payment Requests**: Gift cards, wire transfers, cryptocurrency, unconventional payment methods
    - **Impersonation**: Claiming to be from government agencies (IRS, SSA), tech support, utilities, or banks without verification
    - **Personal Information Requests**: Asking for SSN, passwords, bank details, or remote computer access
    - **Too-Good-To-Be-True Offers**: Prizes, grants, or deals that seem unrealistic
    - **Threats & Intimidation**: Legal threats, account suspension warnings, or arrest warrants
    - **Secrecy Demands**: Instructions not to tell family, friends, or financial institutions
    ## CLASSIFY AS "AMBIGUOUS" IF:
    - Some suspicious elements exist but no clear scam indicators
    - Caller identity cannot be verified but no direct requests for money/information
    - Mixed signals - some legitimate aspects with minor red flags
    - Insufficient information to make definitive classification  
    - Potential telemarketing or survey calls with borderline practices
    ## CLASSIFY AS "LEGITIMATE" IF:
    - Caller identity is verifiable and matches claimed organization
    - No pressure tactics or urgency
    - Standard business practices (appointment reminders, customer service follow-ups)
    - Clear, transparent purpose with no hidden requests
    - Professional tone without emotional manipulation
    # ANALYSIS GUIDELINES
    1. Be conservative - when in doubt, classify as AMBIGUOUS
    2. Consider the context and caller's stated purpose
    3. Look for patterns rather than isolated phrases
    4. Weight multiple weak indicators higher than single strong ones
    5. Consider cultural and regional communication norms\n\n
    Extract the call data and return ONLY valid JSON. No explanations or formatting.\nFocus on relevant sections like if call is a possible scam, reason for contacting the person and the tags for possible scam\n
    If any information is missing, then just leave it empty or use empty arrays.\nIgnore irrelevant sections like references, hobbies, or template artifacts.\n\n"""


settings = Settings()
