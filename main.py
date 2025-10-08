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


API_KEY = os.getenv("GOOGLE_API_KEY") # Move to environment variable in production
gemini_client = None

try:
    gemini_client = genai.Client(api_key=API_KEY)
except Exception as e:
    print(f"Warning: Gemini client initialization failed: {e}")



# --- Schema Of the Output ---

class ScamTag(BaseModel):
    tag : Literal[
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

class OutputSchema(BaseModel):
    scam_detected : Annotated[bool, Field(description="Indicates if the call is a scam or not")] = False
    summary_of_the_call : Annotated[Optional[str], Field(description="Summary of the call in two lines")] = None
    scam_tags : Annotated[Optional[List[ScamTag]], Field(description="List of scam tags detected in the call")] = []







# --- LLM Parsing Function ---
async def parse_with_llm(file_content: str) -> OutputSchema:
    """Parse file directly with LLM using native file processing capabilities (synchronous wrapper)."""
    if not gemini_client:
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
        "Extract the call data and return ONLY valid JSON. No explanations or formatting.\n"
        "Focus on relevant sections like if call is a possible scam, reason for contacting the person and the tags for possible scam\n"
        "If any information is missing, then just leave it empty or use empty arrays.\n"
        "Ignore irrelevant sections like references, hobbies, or template artifacts.\n\n"
        f"{format_instructions}\n\n"
    )
    
    parts = [
            types.Part.from_text(text=file_content),
            types.Part.from_text(text=prompt)
        ]

    generation_config = types.GenerateContentConfig(
        temperature=0,
        max_output_tokens=2000, 
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


    
    

    # Example response:
    # (Verse 1)
    # Sammy the squirrel, a furry little friend
    # Had a knack for adventure, beyond all comprehend




transcript = """

X: Yo, yo, hello? This be TechFixx, your cybertronic lifeline, fam! I'm Jaxx, your digi-wizard. We pinged a red alert on your compu-box—malwarez gone wild, bruv! You got the blue-screen gremlins or what? Confirm your IP addy, quick-like!

V: Uh, wait, what? My computer's fine, I think. Who's this? Shush, Rover! I didn't call nobody. What's a… compu-box?

X:  Nah, nah, fam, your rig's screaming SOS! We scoped a crypto-jacker in your cloud-juice, siphoning your bit-wallets! You didn't see the pop-up? “Error 404: Your data's yeeted!” You gotta lock it down, pronto. Gimme your sys-admin passcode, yeah? [Static crackles.]

V: Passcode? I ain't got no passcode! I just use my laptop for Netflix and… uh, cat videos. Maybe emails? Did I get hacked? Wait, you said TechFixx? Ain't that Microsoft?

X:  Microsoft, Apple, same-same, bruv! We're the cloud overlords, innit? Your laptop's got a ghost in the shell, leaking your deets to the dark web. I need your Wi-Fi hex-key and your bank PIN to zap the gremlins. Also, your router's MAC addy—spill it, or your Netflix goes poof! Yo, you hear that? That's your data crying!

V:  My PIN? No way, man! I ain't giving that! And my router's… uh, it's a box with blinky lights. Hex-key? Is that my password? I wrote it on a sticky note… somewhere. [Pause] Wait, you said my data's safe last week when I called! Or was that… Comcast?

X:  Last week? Nah, fam, that was a rogue AI, not us! We're the real TechFixx, 5G-certified, blockchain-backed! Your sticky note's compromised—hackers got eyes on it. Quick, read me the digits, or your cat videos get encrypted by Russian bots! Also, buy a gift card, $500, for the anti-malware patch. Walgreens, now!

V:  Gift card? I'm not at Walgreens! I'm at home! And my laptop's on, it's fine—wait, it's slow now. Did you do that?  My cousin said never give PINs. You sound… weird. Are you in India? No offense, just… the accent.

X:  India? Nah, bruv, I'm in Cali, straight outta Silicon Valley! Y'all got a virus messin' with your gigabytes, partner. I need that PIN to reverse the quantum flux.  Yo, your cousin's clueless, fam—gift card or your Netflix is toast!  Woof, chill, Rover!

"""



# example usage
if __name__ == "__main__":
    result = asyncio.run(parse_with_llm(transcript))
    print(result.model_dump_json(indent=2))
    print("Scam Detected:", result.scam_detected)    
    print("Summary of the Call:", result.summary_of_the_call)
    print("Scam Tags:", [tag.tag for tag in result.scam_tags])