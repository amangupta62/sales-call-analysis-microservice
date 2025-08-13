"""API routes for text-to-speech conversion."""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from loguru import logger
import os

from models.database import get_db
from schemas.sales_call import TTSRequest, TTSResponse
from services.tts_service import tts_service

router = APIRouter(prefix="/speak", tags=["text-to-speech"])


@router.post("/", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech.
    
    Accepts JSON with:
    - text: Text to convert to speech
    - language: Language code (optional, defaults to English)
    - speed: Speech speed multiplier (optional, defaults to 1.0)
    
    Returns TTS audio file information.
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Convert text to speech
        tts_result = tts_service.text_to_speech(
            text=request.text,
            language=request.language,
            speed=request.speed
        )
        
        logger.info(f"TTS conversion completed for text: {request.text[:50]}...")
        
        return TTSResponse(
            audio_file_path=tts_result["audio_file_path"],
            duration_seconds=tts_result["duration_seconds"],
            text_length=tts_result["text_length"]
        )
        
    except Exception as e:
        logger.error(f"Error in text-to-speech conversion: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """
    Get generated audio file by filename.
    
    Returns the audio file for download or streaming.
    """
    try:
        # Validate filename
        if not filename or ".." in filename or "/" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Construct file path
        file_path = tts_service.output_dir / filename
        
        # Check if file exists
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Return file response
        return FileResponse(
            path=str(file_path),
            media_type="audio/mpeg",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving audio file {filename}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/batch")
async def batch_text_to_speech(texts: list[str], language: str = "en", speed: float = 1.0):
    """
    Convert multiple texts to speech in batch.
    
    Accepts list of texts and converts each to speech.
    Returns list of TTS results.
    """
    try:
        if not texts or len(texts) == 0:
            raise HTTPException(status_code=400, detail="Texts list cannot be empty")
        
        if len(texts) > 10:  # Limit batch size
            raise HTTPException(status_code=400, detail="Batch size cannot exceed 10 texts")
        
        results = []
        
        for i, text in enumerate(texts):
            try:
                if not text or not text.strip():
                    results.append({
                        "index": i,
                        "status": "error",
                        "error": "Empty text"
                    })
                    continue
                
                # Convert text to speech
                tts_result = tts_service.text_to_speech(
                    text=text,
                    language=language,
                    speed=speed
                )
                
                results.append({
                    "index": i,
                    "status": "success",
                    "audio_file_path": tts_result["audio_file_path"],
                    "duration_seconds": tts_result["duration_seconds"],
                    "text_length": tts_result["text_length"]
                })
                
            except Exception as e:
                results.append({
                    "index": i,
                    "status": "error",
                    "error": str(e)
                })
        
        logger.info(f"Batch TTS conversion completed for {len(texts)} texts")
        
        return {
            "total_texts": len(texts),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"]),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch text-to-speech conversion: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/languages")
async def get_supported_languages():
    """
    Get list of supported languages for TTS.
    
    Returns available language codes and names.
    """
    try:
        # Common language codes supported by most TTS engines
        languages = [
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "es", "name": "Spanish", "native_name": "Español"},
            {"code": "fr", "name": "French", "native_name": "Français"},
            {"code": "de", "name": "German", "native_name": "Deutsch"},
            {"code": "it", "name": "Italian", "native_name": "Italiano"},
            {"code": "pt", "name": "Portuguese", "native_name": "Português"},
            {"code": "ru", "name": "Russian", "native_name": "Русский"},
            {"code": "ja", "name": "Japanese", "native_name": "日本語"},
            {"code": "ko", "name": "Korean", "native_name": "한국어"},
            {"code": "zh", "name": "Chinese", "native_name": "中文"},
            {"code": "ar", "name": "Arabic", "native_name": "العربية"},
            {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"}
        ]
        
        return {
            "supported_languages": languages,
            "default_language": "en",
            "tts_engine": tts_service.engine
        }
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status")
async def get_tts_status():
    """
    Get TTS service status and configuration.
    
    Returns current TTS engine status and settings.
    """
    try:
        return {
            "status": "operational",
            "engine": tts_service.engine,
            "language": tts_service.language,
            "speed": tts_service.speed,
            "output_directory": str(tts_service.output_dir),
            "engine_available": {
                "gtts": hasattr(tts_service, 'gtts_available') and tts_service.gtts_available,
                "pyttsx3": hasattr(tts_service, 'pyttsx3_available') and tts_service.pyttsx3_available
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting TTS status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
