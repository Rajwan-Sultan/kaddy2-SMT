import asyncio
import json
import re
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Annotated,Literal
import os
from dotenv import load_dotenv
load_dotenv()

# --- LLM SDK Imports ---
from google import genai
from google.genai import types


API_KEY = os.getenv("GOOGLE_API_KEY")
gemini_client = None

try:
    gemini_client = genai.Client(api_key=API_KEY)
except Exception as e:
    print(f"Warning: Gemini client initialization failed: {e}")



# --- Schema Of the Output ---
class ScamTag(BaseModel):
    tag: Literal[
        "Robocall",
        "Phishing",
        "Telemarketing",
        "Debt Collection",
        "Survey Scam",
        "Charity Scam",
        "Tech Support Scam",
        "Lottery Scam",
        "Investment Scam",
        "Other"
    ] = Field(..., description="Type of scam detected")


class RiskFactors(BaseModel):
    urgency_pressure: Annotated[Optional[int], Field(ge=0, le=10, description="Risk factor score for urgency and pressure tactics")] = None
    suspicious_payment: Annotated[Optional[int], Field(ge=0, le=10, description="Risk factor score for suspicious payment requests")] = None
    impersonation: Annotated[Optional[int], Field(ge=0, le=10, description="Risk factor score for impersonation attempts")] = None
    information_request: Annotated[Optional[int], Field(ge=0, le=10, description="Risk factor score for personal information requests")] = None
    emotional_manipulation: Annotated[Optional[int], Field(ge=0, le=10, description="Risk factor score for emotional manipulation tactics")] = None

class OutputSchema(BaseModel):
    scam_detected: Annotated[Literal['scam','ambiguous','legitimate'], Field(description="Indicates if the call is a scam or not")] = None
    confidence_score: Annotated[Optional[int], Field(ge=0, le=100, description="Confidence score in percentage from 0 to 100")] = None
    risk_factors: Annotated[Optional[RiskFactors], Field(description="Detailed risk factor scores")] = None
    explanation: Annotated[Optional[str], Field(description="Summary of the call in two lines")] = None
    scam_tags: Annotated[Optional[List[ScamTag]], Field(description="List of scam tags detected in the call")] = None





# --- LLM Parsing Function ---
async def parse_with_llm(file_content) -> OutputSchema:
    """Parse file directly with LLM using native file processing capabilities (synchronous wrapper)."""
    if not gemini_client:
        raise Exception("Gemini client not available")
    
    prompt = (
    """You are an expert fraud detection analyst specializing in telecommunications scams.Strictly remove any markdown formatting from your response.
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
    If any information is missing, then just leave it empty or use empty arrays.\nIgnore irrelevant sections like references, hobbies, or template artifacts.\n\n
""")
    


    
    with open(file_content, 'rb') as f:
        audio_bytes = f.read()
    parts = [
            types.Part.from_text(text=prompt),
            # types.Part.from_text(text=file_content),
            types.Part.from_bytes(
                data=audio_bytes,
                mime_type='audio/mp3',
        
            )
        ]

    generation_config = types.GenerateContentConfig(
        temperature=0,
        max_output_tokens=1000, 
        response_mime_type="application/json",
        response_schema=OutputSchema.model_json_schema()
    )

    response = await gemini_client.aio.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=parts,
        config=generation_config
    )
    

    if not getattr(response, "text", None):
        raise Exception("Empty LLM response")
    return OutputSchema.model_validate_json(response.text)




if __name__ == "__main__":
    import datetime
    start = datetime.datetime.now()
    result = asyncio.run(parse_with_llm("scam3.mp3"))
    end = datetime.datetime.now()
    print(result.model_dump_json(indent=2))
    print("Time taken:", end - start)