from google.genai import types
from schemas.output_schema import OutputSchema
from config.gemini_client import gemini_client
from config.settings import settings


async def parse_audio_with_llm(file_path: str, mime_type: str) -> OutputSchema:
    """
    Parse audio file with LLM using native file processing capabilities.
    
    Args:
        file_path: Path to the audio file
        mime_type: MIME type of the audio file
        
    Returns:
        OutputSchema: Parsed output from LLM
        
    Raises:
        Exception: If LLM processing fails
    """
    client = gemini_client.get_client()
    
    with open(file_path, 'rb') as f:
        audio_bytes = f.read()
    
    parts = [
        types.Part.from_text(text=settings.SYSTEM_PROMPT),
        types.Part.from_bytes(
            data=audio_bytes,
            mime_type=mime_type,
        )
    ]

    generation_config = types.GenerateContentConfig(
        temperature=settings.TEMPERATURE,
        max_output_tokens=settings.MAX_OUTPUT_TOKENS,
        response_mime_type="application/json",
        response_schema=OutputSchema.model_json_schema()
    )

    response = await client.aio.models.generate_content(
        model=settings.MODEL_NAME,
        contents=parts,
        config=generation_config
    )
    
    if not getattr(response, "text", None):
        raise Exception("Empty LLM response")
    
    return OutputSchema.model_validate_json(response.text)


async def parse_text_with_llm(file_content: str) -> OutputSchema:
    """
    Parse text content with LLM.
    
    Args:
        file_content: Text content to analyze
        
    Returns:
        OutputSchema: Parsed output from LLM
        
    Raises:
        Exception: If LLM processing fails
    """
    client = gemini_client.get_client()
    
    parts = [
        types.Part.from_text(text=settings.SYSTEM_PROMPT),
        types.Part.from_text(text=file_content),
    ]

    generation_config = types.GenerateContentConfig(
        temperature=settings.TEMPERATURE,
        max_output_tokens=settings.MAX_OUTPUT_TOKENS,
        response_mime_type="application/json",
        response_schema=OutputSchema.model_json_schema()
    )

    response = await client.aio.models.generate_content(
        model=settings.MODEL_NAME,
        contents=parts,
        config=generation_config
    )
    
    if not getattr(response, "text", None):
        raise Exception("Empty LLM response")
    
    return OutputSchema.model_validate_json(response.text)
