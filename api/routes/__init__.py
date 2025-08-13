"""API routes package for sales call analysis microservice."""

from .transcription import router as transcription_router
from .tts import router as tts_router
from .replay import router as replay_router

__all__ = [
    "transcription_router",
    "tts_router", 
    "replay_router"
]
