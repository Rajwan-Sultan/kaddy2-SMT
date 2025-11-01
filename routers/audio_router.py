import os
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from schemas.output_schema import OutputSchema
from services.llm_service import parse_audio_with_llm
from utils.file_utils import check_mime_type
from config.settings import settings

router = APIRouter()


@router.post("/analyzer_audio", response_model=OutputSchema)
async def analyze_audio(file: UploadFile = File(...)):
    """
    Analyze uploaded audio file for scam detection.
    
    Args:
        file: Audio file to analyze
        
    Returns:
        OutputSchema: Analysis results including scam detection, confidence score, and risk factors
        
    Raises:
        HTTPException: If file processing or analysis fails
    """
    try:
        # Check MIME type before processing
        mime_type = check_mime_type(file)
        
        # Save uploaded file to a temporary location
        temp_file_path = os.path.join(settings.TEMP_FILE_DIR, file.filename)
        # with open(temp_file_path, "wb") as temp_file:
        #     content = await file.read()
        #     temp_file.write(content)


        #! Edited to use aiofiles for async file operations
        content = await file.read()
        async with aiofiles.open(temp_file_path, "wb") as temp_file:
            await temp_file.write(content)





        # Parse the audio file with LLM
        result = await parse_audio_with_llm(temp_file_path, mime_type)

        # Clean up temporary file
        os.remove(temp_file_path)

        return result

    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio file: {str(e)}"
        )