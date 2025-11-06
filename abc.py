import asyncio
import json
import re
from fastapi import FastAPI, UploadFile, File, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Annotated,Literal
import os
from dotenv import load_dotenv
import uuid
load_dotenv()


app = FastAPI()


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

def check_mime_type(file: UploadFile):
    ext = file.filename.split('.')[-1].lower()
    allowed_extensions = {
         'flac':'audio/flac', 
         'mp3':'audio/mp3',
         'm4a':'audio/m4a', 
         'mpeg':'audio/mpeg',
         'mpga':'audio/mpga', 
         'mp4':'audio/mp4',
         'ogg': 'audio/ogg', 
         'pcm': 'audio/pcm', 
         'wav': 'audio/wav', 
         'webm': 'audio/webm' 
    }
    if ext not in allowed_extensions:
        raise Exception(f"Unsupported file extension: {ext}")
    return allowed_extensions[ext]

def prompt_text():
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
    If any information is missing, then just leave it empty or use empty arrays.\nIgnore irrelevant sections like references, hobbies, or template artifacts.\n\n""")
    return prompt

# --- LLM Parsing Function ---
async def parse_with_llm_audio(file_path: str, mime_type: str) -> OutputSchema:
    """Parse file directly with LLM using native file processing capabilities (synchronous wrapper)."""
    if not gemini_client:
        raise Exception("Gemini client not available")
    
    prompt = prompt_text()
    
    with open(file_path, 'rb') as f:
        audio_bytes = f.read()
    
    parts = [
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(
                data=audio_bytes,
                mime_type=mime_type,
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

async def parse_with_llm_text(file_content) -> OutputSchema:
    """Parse file directly with LLM using native file processing capabilities (synchronous wrapper)."""
    if not gemini_client:
        raise Exception("Gemini client not available")
    
    prompt  = prompt_text()
    

    parts = [
            types.Part.from_text(text=prompt),
            types.Part.from_text(text=file_content),
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

@app.post("/analyzer_audio", response_model=OutputSchema)
async def analyze_audio(file: UploadFile = File(...)):
    """Analyze uploaded audio file for scam detection."""
    try:
        # Check MIME type before processing
        mime_type = check_mime_type(file)
        
        # Save uploaded file to a temporary location
        temp_file_path = f"/tmp/{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)

        # Parse the audio file with LLM
        result = await parse_with_llm_audio(temp_file_path, mime_type)

        # Clean up temporary file
        os.remove(temp_file_path)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio file: {str(e)}"
        )

@app.post("/analyzer_text", response_model=OutputSchema)
async def analyze_text(file: str):
    """Analyze uploaded text file for scam detection."""
    try:
        # Parse the text content with LLM
        result = await parse_with_llm_text(file)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing text file: {str(e)}"
        )

@app.websocket("/analyzer_audio_stream")
async def analyze_audio_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio chunk analysis.
    
    Connection Flow:
    1. Connect to ws://host:port/analyzer_audio_stream
    2. Receive connection confirmation (JSON)
    3. Send audio format as text (e.g., "mp3", "wav", "webm")
    4. Receive format confirmation (JSON)
    5. Send audio data continuously as binary
    6. Send "ANALYZE" as text to trigger analysis of accumulated audio
    7. Receive analysis results (JSON) - instantly after ANALYZE
    8. Repeat steps 5-7 for multiple files
    9. Send "CLOSE" to close connection or just disconnect
    
    Supported formats: flac, mp3, m4a, mpeg, mpga, mp4, ogg, pcm, wav, webm
    """
    await websocket.accept()
    audio_format = None
    audio_buffer = bytearray()
    analysis_count = 0
    
    try:
        await websocket.send_json({
            "status": "connected",
            "message": "Send audio format first (e.g., 'mp3', 'wav', 'webm'), then send audio data as binary. Send 'ANALYZE' to analyze, 'CLOSE' to disconnect."
        })
        
        # First message should be the audio format
        format_message = await websocket.receive_text()
        audio_format = format_message.lower().strip()
        
        # Validate audio format
        allowed_formats = {
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
        
        if audio_format not in allowed_formats:
            await websocket.send_json({
                "status": "error",
                "error": f"Unsupported audio format: {audio_format}. Supported formats: {', '.join(allowed_formats.keys())}"
            })
            await websocket.close()
            return
        
        mime_type = allowed_formats[audio_format]
        
        await websocket.send_json({
            "status": "format_accepted",
            "format": audio_format,
            "mime_type": mime_type,
            "message": "Connection ready. Send audio data as binary, then 'ANALYZE' to process. Connection stays open for multiple files."
        })
        
        while True:
            # Try to receive message (could be text or binary)
            message = await websocket.receive()
            
            # Check if connection is closing
            if message.get('type') == 'websocket.disconnect':
                break
            
            if 'text' in message:
                command = message['text'].strip().upper()
                
                if command == "ANALYZE":
                    if len(audio_buffer) == 0:
                        await websocket.send_json({
                            "status": "error",
                            "error": "No audio data to analyze"
                        })
                        continue
                    
                    analysis_count += 1
                    temp_file_path = f"/tmp/audio_stream_{uuid.uuid4()}_{analysis_count}.{audio_format}"
                    
                    try:
                        # Save accumulated audio to temporary file
                        with open(temp_file_path, "wb") as temp_file:
                            temp_file.write(audio_buffer)
                        
                        # Send processing status
                        await websocket.send_json({
                            "status": "processing",
                            "analysis_number": analysis_count,
                            "audio_size_bytes": len(audio_buffer)
                        })
                        
                        # Analyze the accumulated audio
                        result = await parse_with_llm_audio(temp_file_path, mime_type)
                        
                        # Send analysis result back IMMEDIATELY
                        await websocket.send_json({
                            "status": "complete",
                            "analysis_number": analysis_count,
                            "audio_size_bytes": len(audio_buffer),
                            "analysis": result.model_dump()
                        })
                        
                        # Clear buffer after successful analysis (ready for next file)
                        audio_buffer.clear()
                        
                    except Exception as e:
                        await websocket.send_json({
                            "status": "error",
                            "analysis_number": analysis_count,
                            "error": str(e)
                        })
                        # Clear buffer on error to allow retry
                        audio_buffer.clear()
                    
                    finally:
                        # Clean up temporary file
                        if os.path.exists(temp_file_path):
                            os.remove(temp_file_path)
                
                elif command == "CLEAR":
                    # Clear the audio buffer without analyzing
                    buffer_size = len(audio_buffer)
                    audio_buffer.clear()
                    await websocket.send_json({
                        "status": "buffer_cleared",
                        "cleared_bytes": buffer_size
                    })
                
                elif command == "STATUS":
                    # Get current buffer status
                    await websocket.send_json({
                        "status": "buffer_status",
                        "buffer_size_bytes": len(audio_buffer),
                        "analysis_count": analysis_count,
                        "format": audio_format
                    })
                
                elif command == "CLOSE":
                    # Graceful close requested by client
                    await websocket.send_json({
                        "status": "closing",
                        "message": f"Connection closing. Processed {analysis_count} files."
                    })
                    break
                
                else:
                    await websocket.send_json({
                        "status": "error",
                        "error": f"Unknown command: {command}. Available commands: ANALYZE, CLEAR, STATUS, CLOSE"
                    })
            
            elif 'bytes' in message:
                # Accumulate audio data silently (no acknowledgment to avoid blocking)
                audio_chunk = message['bytes']
                audio_buffer.extend(audio_chunk)
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected after {analysis_count} analyses, buffer size: {len(audio_buffer)} bytes")
    except RuntimeError as e:
        # Handle "Cannot call receive once a disconnect message has been received" error
        if "disconnect" in str(e).lower():
            print(f"WebSocket disconnected (RuntimeError) after {analysis_count} analyses")
        else:
            print(f"WebSocket RuntimeError: {e}")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Don't try to send messages or close if already disconnected
        print(f"WebSocket cleanup: {analysis_count} analyses completed, final buffer size: {len(audio_buffer)} bytes")

@app.get("/analyzer_audio_stream/info", tags=["WebSocket"])
async def get_websocket_info():
    """
    Get information about the WebSocket audio streaming endpoint.
    
    This is a helper endpoint to show WebSocket connection details in Swagger.
    The actual WebSocket endpoint is at: ws://host:port/analyzer_audio_stream
    """
    return {
        "endpoint": "/analyzer_audio_stream",
        "protocol": "WebSocket",
        "description": "Real-time audio streaming analysis endpoint",
        "connection_url": "ws://127.0.0.1:8000/analyzer_audio_stream",
        "usage": {
            "step_1": "Connect to WebSocket endpoint",
            "step_2": "Receive connection confirmation (JSON)",
            "step_3": "Send audio format as text (e.g., 'mp3', 'wav')",
            "step_4": "Receive format confirmation (JSON)",
            "step_5": "Send audio data continuously as binary",
            "step_6": "Send 'ANALYZE' as text to analyze accumulated audio",
            "step_7": "Receive analysis results (JSON)",
            "step_8": "Optionally continue sending more audio or close connection"
        },
        "commands": {
            "ANALYZE": "Analyze all accumulated audio data in buffer",
            "CLEAR": "Clear audio buffer without analyzing",
            "STATUS": "Get current buffer status",
            "CLOSE": "Close the WebSocket connection"
        },
        "supported_formats": ["flac", "mp3", "m4a", "mpeg", "mpga", "mp4", "ogg", "pcm", "wav", "webm"],
        "example_client_code": "See test_websocket.py for usage example"
    }

if __name__ == "__main__":
    import uvicorn
    import time
    start = time.time()
    uvicorn.run(app, host="0.0.0.0", port=8000)
