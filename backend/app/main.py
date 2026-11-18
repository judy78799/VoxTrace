"""
VoxTrace Backend - Main Application Entry Point

Low-quality Audio Robust Speech Recognition System
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import audio, projects, transcripts
from app.core.config import settings
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 생명주기 관리

    시작 시: 데이터베이스 초기화
    종료 시: 정리 작업
    """
    # Startup
    print("🚀 VoxTrace Backend Starting...")
    await init_db()
    print("✅ Database initialized")

    yield

    # Shutdown
    print("👋 VoxTrace Backend Shutting down...")


app = FastAPI(
    title="VoxTrace API",
    description="Local-first Speech Recognition & Audio Enhancement System",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(transcripts.router, prefix="/api/transcripts", tags=["transcripts"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "VoxTrace API",
        "version": "0.1.0",
    }


@app.get("/api/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "models": {
            "asr": "not_loaded",
            "diarization": "not_loaded",
            "vad": "not_loaded",
            "enhancement": "not_loaded",
        },
    }
