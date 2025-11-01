import utils.session
from fastapi import FastAPI
from routers import audio_router, text_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Scam Detection API",
    description="API for detecting scams in audio and text communications",
    version="1.0.0"
)

# adding corrs middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# Include routers
app.include_router(audio_router.router, prefix="/api/v1", tags=["Audio Analysis"])
app.include_router(text_router.router, prefix="/api/v1", tags=["Text Analysis"])

@app.get("/")
async def root():
    return {"message": "Scam Detection API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)