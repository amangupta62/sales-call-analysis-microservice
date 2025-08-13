"""Main FastAPI application for Sales Call Analysis Microservice."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from config.settings import settings
from models.database import create_tables
from api.routes import transcription_router, tts_router, replay_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Sales Call Analysis Microservice...")
    
    try:
        # Create database tables
        create_tables()
        logger.info("Database tables created/verified successfully")
        
        # Create necessary directories
        os.makedirs(settings.audio_upload_dir, exist_ok=True)
        os.makedirs("./tts_output", exist_ok=True)
        logger.info("Required directories created successfully")
        
        logger.info("Sales Call Analysis Microservice started successfully")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Sales Call Analysis Microservice...")


# Create FastAPI app
app = FastAPI(
    title="Sales Call Analysis Microservice",
    description="""
    A comprehensive microservice for analyzing sales call audio recordings.
    
    ## Features
    
    * **Audio Transcription**: Convert audio to text using OpenAI Whisper
    * **Sentiment Analysis**: Analyze emotional tone and sentiment
    * **Coachable Moment Detection**: Identify key learning opportunities
    * **Executive Summaries**: Generate comprehensive call summaries
    * **Text-to-Speech**: Convert text back to audio for replay
    * **Background Processing**: Async processing using Celery and Redis
    
    ## Endpoints
    
    * `/transcribe/*` - Audio upload and transcription
    * `/speak/*` - Text-to-speech conversion
    * `/replay/*` - Coachable moment replay functionality
    
    ## Architecture
    
    Built with FastAPI, SQLAlchemy, Celery, Redis, and PostgreSQL.
    """,
    version="1.0.0",
    contact={
        "name": "Sales Call Analysis Team",
        "email": "support@salesanalysis.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(transcription_router, prefix="/api/v1")
app.include_router(tts_router, prefix="/api/v1")
app.include_router(replay_router, prefix="/api/v1")


@app.get("/", tags=["root"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Sales Call Analysis Microservice",
        "version": "1.0.0",
        "status": "operational",
        "description": "AI-powered sales call analysis and coaching platform",
        "endpoints": {
            "transcription": "/api/v1/transcribe",
            "text_to_speech": "/api/v1/speak",
            "replay": "/api/v1/replay",
            "documentation": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Sales Call Analysis Microservice",
        "version": "1.0.0",
        "timestamp": "2024-01-01T00:00:00Z"
    }


@app.get("/config", tags=["config"])
async def get_config():
    """Get current configuration (non-sensitive values only)."""
    return {
        "debug": settings.debug,
        "log_level": settings.log_level,
        "audio_max_size_mb": settings.audio_max_size_mb,
        "supported_audio_formats": settings.supported_audio_formats,
        "whisper_model": settings.whisper_model,
        "tts_engine": settings.tts_engine,
        "coachable_moment_threshold": settings.coachable_moment_threshold
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_type": type(exc).__name__
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP exception handler."""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
