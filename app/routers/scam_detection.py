# ===== app/routers/scam_detection.py =====
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.services import LLMService
from app.schemas import OutputSchema

router = APIRouter(prefix="/api/v1", tags=["scam-detection"])

# Initialize LLM service lazily to avoid initialization errors at import
_llm_service = None

def get_llm_service():
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service

class TranscriptRequest(BaseModel):
    transcript: str = Field(..., description="The call transcript to analyze", min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "transcript": "X: Hello, this is tech support. We detected a virus on your computer..."
            }
        }

@router.post("/detect-scam", response_model=OutputSchema)
async def detect_scam(request: TranscriptRequest):
    """
    Analyze a call transcript to detect potential scams
    
    **Request Body:**
    ```json
    {
        "transcript": "Your call transcript here..."
    }
    ```
    
    **Response:** Returns scam detection results with tags and summary
    """
    try:
        llm_service = get_llm_service()
        result = await llm_service.parse_transcript(request.transcript)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing transcript: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "scam-detector"}
