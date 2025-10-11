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
        "OTP",
        "IRS Scam",
        "Bank Impersonation",
        "Utility Scam",
        "Romance Scam",
        "Grandparent Scam",
        "Fake Check Scam",
        "Cryptocurrency Scam",
        "Gift Card Scam",
        "Online Shopping Scam",
        "Travel Scam",
        "Health Insurance Scam",
        "Government Grant Scam",
        "Job Offer Scam",
        "Rental Scam",
        "Tax Scam",
        "Social Security Scam",
        "Account Suspension Scam",
        "Password Reset Scam",
        "Remote Access Scam",
        "Fake Invoice Scam",
        "Fake Prize Scam",
        "Fake Survey Scam",
        "Urgency Pressure",
        "Suspicious Payment Request",
    ] = Field(..., description="Type of scam detected")

class OutputSchema(BaseModel):
    scam_detected : Annotated[Literal['scam', 'ambiguous', 'legitimate'], Field(description="Classification of the call as 'scam', 'ambiguous', or 'legitimate'")] = 'legitimate'
    summary_of_the_call : Annotated[Optional[str], Field(description="Summary of the call in two lines")] = None
    scam_tags : Annotated[Optional[List[ScamTag]], Field(description="List of scam tags detected in the call")] = []
    rating: Annotated[float, Field(ge=0, le=100, description="Scam likelihood percentage from 0% to 100%")] = 0.0







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




# --- LLM Parsing Function ---
async def parse_with_llm(file_content: str) -> OutputSchema:
    """Parse file directly with LLM using native file processing capabilities (synchronous wrapper)."""
    if not gemini_client:
        raise Exception("Gemini client not available")
    
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
5. Consider cultural and regional communication norms
Extract the call data and return ONLY valid JSON. No explanations or formatting.\nFocus on relevant sections like if call is a possible scam, reason for contacting the person and the tags for possible scam\n
If any information is missing, then just leave it empty or use empty arrays.\nIgnore irrelevant sections like references, hobbies, or template artifacts.\n\n""")
    
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


transcript = """
হ্যালো, আমি আপনার টেকনিক্যাল সাপোর্ট টিম থেকে বলছি। আমি অর্জুন। আমাদের সিস্টেমে দেখা গেছে আপনার কম্পিউটারে একটা বড় সমস্যা। দুর্গাপুজোর ভিড়ে হ্যাকাররা আপনার ডিভাইসে ঢুকে পড়েছে। আপনি কি এখন ল্যাপটপের সামনে?
হ্যাঁ, ল্যাপটপে আছি। কিন্তু কী সমস্যা? আমি তো শুধু ইউটিউবে পুজোর নাচ দেখছিলাম আর মা’র কাছে মিষ্টি অর্ডার দিচ্ছিলাম। সব ঠিক আছে মনে হয়।
আমাদের রিপোর্টে দেখা যাচ্ছে আপনার ডিভাইস থেকে ডেটা চুরি হচ্ছে। এটা হয়তো পুজোর সময় সাইবার চোরের কাজ, কলকাতার সার্ভারে লোড বেশি থাকায় ঢুকে পড়েছে। আপনার অ্যাকাউন্ট সুরক্ষিত করতে হবে। আপনার ইউজার আইডি আর পাসওয়ার্ড কনফার্ম করুন।
পাসওয়ার্ড? আমি তো একটা সিম্পল পাসওয়ার্ড ব্যবহার করি, মা দুর্গার নামে। এটা কি ঠিক হবে? আমি বুঝছি না। আমার ল্যাপটপ তো ঠিক চলছে। আমি কাল রাতেও ফ্লিপকার্টে পুজোর জামা দেখছিলাম।
একদম নিরাপদ, চিন্তা নেই। আমরা আপনার ডিভাইসের সিকিউরিটি চেক করছি। আপনার ওয়াই-ফাই কোড আর ব্যাঙ্ক অ্যাকাউন্টের শেষ চারটে সংখ্যা দিন, আমরা চোরের ডিজিটাল ফাঁদটা বন্ধ করব। আপনি কি এখনো পুজোর নাচের ভিডিও দেখতে পারছেন?
হ্যাঁ, দেখতে পারছি। কিন্তু ব্যাঙ্কের নম্বর কেন? আমি তো শুধু মিষ্টির দোকানে ফোনপে করি, আর পুজোর প্যান্ডেলে দান দিয়েছি। ল্যাপটপ কাল থেকে একটু ধীর। এটা কি পুজোর ইন্টারনেট লোডের জন্য?
ঠিক এই কারণেই ফোন করেছি। আপনার ল্যাপটপে একটা সাইবার ঝোল ঢুকে গেছে, পুজোর ভিড়ে হ্যাকাররা সুযোগ নিচ্ছে। দ্রুত না করলে আপনার ফ্লিপকার্ট অর্ডার আর ইমেল লক হয়ে যাবে। তাড়াতাড়ি পাসওয়ার্ড আর ব্যাঙ্ক পিন দিন, আমরা এখনই ঠিক করব।
পিন? আমি তো দাদার কাছে শিখেছি পিন কাউকে দেওয়া যায় না। কিন্তু ল্যাপটপ ধীর হলে পুজোর ছবি আপলোড করতে সমস্যা হবে। আমার একটা পুরোনো খাতায় পাসওয়ার্ড লেখা, কোথায় রাখলাম?
সময় নেই! পুজোর প্যান্ডেলে যেমন ভিড়ে পকেটমার ঢোকে, তেমনি হ্যাকাররা আপনার খাতা হ্যাক করতে পারে। এখনই পিন আর ওয়াই-ফাই কোড বলুন, নইলে আপনার ফোনপে আর পুজোর ভিডিও উড়ে যাবে। আর ৫০০ টাকার গিফট কার্ড কিনে নিন, আমাদের সিকিউরিটি মশলার জন্য। কাছের মিষ্টির দোকানে পাওয়া যাবে!
গিফট কার্ড? আমি তো এখন বাড়িতে, পুজোর প্রসাদ খাচ্ছি। দোকানে যেতে হবে? ল্যাপটপ একটু ঝামেলা করছে, তবে চলছে। আমি কি খাতাটা খুঁজে পাসওয়ার্ড বলব?
দেরি করলে আপনার সব ফাইল পুজোর ধুনুচির ধোঁয়ার মতো উবে যাবে! খাতা খুঁজবেন না, সরাসরি পিন বলুন। গিফট কার্ডটা এখনই কিনে ফেলুন, নইলে আমরা বাঁচাতে পারব না। আপনার ল্যাপটপের গিগাবাইট পুড়ে যাচ্ছে, মা দুর্গার দোহাই!
আচ্ছা, বুঝলাম। কিন্তু দোকানে যেতে পারব না এখন, পুজোর প্যান্ডেলে যাব। আমি কি ল্যাপটপ বন্ধ করে রাখব? পিনটা খাতায় আছে, পরে বলব।
না, বন্ধ করবেন না! তাহলে আপনার ফ্লিপকার্ট অর্ডার আর পুজোর ছবি হারাবেন। এখনই পিন আর কোড বলুন। আমি আপনাকে হেল্প করছি, তাড়াতাড়ি করুন! পরে ফোন করলে ঠিক হবে না।
"""



# example usage
if __name__ == "__main__":
    result = asyncio.run(parse_with_llm(transcript))
    print(result.model_dump_json(indent=2))
    print("Scam Detected:", result.scam_detected)    
    print("Summary of the Call:", result.summary_of_the_call)
    print("Scam Tags:", [tag.tag for tag in result.scam_tags])
    print("Rating:", result.rating)