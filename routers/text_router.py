from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from schemas.output_schema import OutputSchema
from services.llm_service import parse_text_with_llm

router = APIRouter()


class TextInput(BaseModel):
    content: str


@router.post("/analyzer_text", response_model=OutputSchema)
async def analyze_text(text_input: TextInput):
    """
    Analyze text content for scam detection.
    
    Args:
        text_input: Text content to analyze
        
    Returns:
        OutputSchema: Analysis results including scam detection, confidence score, and risk factors
        
    Raises:
        HTTPException: If text processing or analysis fails
    """
    try:
        # Parse the text content with LLM
        result = await parse_text_with_llm(text_input.content)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing text: {str(e)}"
        )
