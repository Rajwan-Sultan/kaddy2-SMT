from fastapi import UploadFile
from config.settings import settings


def check_mime_type(file: UploadFile) -> str:
    """
    Check if the uploaded file has a supported audio extension and return its MIME type.
    
    Args:
        file: The uploaded file
        
    Returns:
        str: The MIME type of the file
        
    Raises:
        Exception: If the file extension is not supported
    """
    ext = file.filename.split('.')[-1].lower()
    
    if ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
        raise Exception(f"Unsupported file extension: {ext}")
    
    return settings.ALLOWED_AUDIO_EXTENSIONS[ext]
