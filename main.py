"""
AquaForensics FastAPI Backend Application.
Hackathon: OneAquaHealth IEEE Global Hackathon 2026.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import init_db
from routers.investigations import router as investigations_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema on startup
    init_db()
    yield

app = FastAPI(
    title="AquaForensics API",
    description=(
        "AquaForensics is an evidence-guided environmental investigation engine "
        "that turns citizen observations of urban freshwater anomalies into structured investigations, "
        "competing hypotheses, uncertainty estimates, and computed next-best observations."
    ),
    version="0.1-dev",
    lifespan=lifespan
)

import os

cors_origins_env = os.getenv("CORS_ORIGINS", "").strip()
if cors_origins_env:
    allowed_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(investigations_router)

@app.get("/")
def read_root():
    return {
        "project": "AquaForensics",
        "description": "Evidence-Guided Environmental Investigation Engine",
        "hackathon": "OneAquaHealth IEEE Global Hackathon 2026",
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "engine": "Bayesian Expected Information Gain Engine v0.1-dev"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
