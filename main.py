from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import router
import uvicorn

app = FastAPI(
    title="Scam Detection API",
    description="API for detecting scams in call transcripts using LLM",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

@app.get("/")
async def root():
    return {
        "message": "Scam Detection API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)