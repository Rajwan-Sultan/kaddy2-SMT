from google import genai
from google.genai import types
from app.config import settings
from app.schemas import OutputSchema

class LLMService:
    """Service for LLM-based scam detection"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Gemini client"""
        try:
            settings.validate()
            self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        except Exception as e:
            print(f"Warning: Gemini client initialization failed: {e}")
            raise
    
    async def parse_transcript(self, transcript: str) -> OutputSchema:
        """Parse transcript and detect scam using LLM"""
        if not self.client:
            raise Exception("Gemini client not available")
        
        format_instructions = (
            "Return valid JSON with these exact fields:\n"
            "Strictly use this format:\n"
            "{\n"
            '  "scam_detected": bool,\n'
            '  "summary_of_the_call": string,\n'
            '  "scam_tags": [string]\n'
            "}"
        )
        
        prompt = (
"""You are an expert fraud detection analyst specializing in telecommunications scams.
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
If any information is missing, then just leave it empty or use empty arrays.\nIgnore irrelevant sections like references, hobbies, or template artifacts.\n\n""")
        parts = [
            types.Part.from_text(text=transcript),
            types.Part.from_text(text=prompt)
        ]

        generation_config = types.GenerateContentConfig(
            temperature=settings.TEMPERATURE,
            max_output_tokens=settings.MAX_OUTPUT_TOKENS,
            response_mime_type="application/json",
            response_schema=OutputSchema.model_json_schema()
        )

        response = await self.client.aio.models.generate_content(
            model=settings.MODEL_NAME,
            contents=parts,
            config=generation_config
        )
        
        if not getattr(response, "text", None):
            raise Exception("Empty LLM response")
        
        return OutputSchema.model_validate_json(response.text)