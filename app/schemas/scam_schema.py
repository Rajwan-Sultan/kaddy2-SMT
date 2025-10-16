from pydantic import BaseModel, Field
from typing import Optional, List, Annotated, Literal

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
    scam_detected: Annotated[Literal['scam','ambiguous','legitimate'], Field(description="Indicates if the call is a scam or not")] = []
    confidence_score: Annotated[Optional[int], Field(ge=0, le=100, description="Confidence score in percentage from 0 to 100")] = None
    risk_factors: Annotated[Optional[RiskFactors], Field(description="Detailed risk factor scores")] = None
    explanation: Annotated[Optional[str], Field(description="Summary of the call in two lines")] = None
    scam_tags: Annotated[Optional[List[ScamTag]], Field(description="List of scam tags detected in the call")] = []







"""
# ROLE
Y
# OUTPUT FORMAT
Provide your analysis in this exact JSON structure:

{
  "classification": "SCAM" | "AMBIGUOUS" | "LEGITIMATE",
  "confidence_score": 0-100,
  "key_indicators": ["list", "of", "relevant", "factors"],
  "risk_factors": {
    "urgency_pressure": 0-10,
    "suspicious_payment": 0-10, 
    "impersonation": 0-10,
    "information_request": 0-10,
    "emotional_manipulation": 0-10
  },
  "explanation": "Detailed analysis of why this classification was chosen",
  "recommendation": "Specific advice for how to respond"
}

# ANALYSIS GUIDELINES
1. Be conservative - when in doubt, classify as AMBIGUOUS
2. Consider the context and caller's stated purpose
3. Look for patterns rather than isolated phrases
4. Weight multiple weak indicators higher than single strong ones
5. Consider cultural and regional communication norms

Now analyze the following call transcript:
<transcript>
{transcript}
</transcript>


"""