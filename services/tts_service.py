"""Text-to-Speech service using multiple TTS engines."""

import os
import uuid
from pathlib import Path
from typing import Optional, Dict
from loguru import logger
import tempfile

from config.settings import settings

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logger.warning("gTTS not available, falling back to pyttsx3")

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 not available")


class TTSService:
    """Handles text-to-speech conversion using multiple engines."""
    
    def __init__(self):
        """Initialize TTS service."""
        self.engine = settings.tts_engine.lower()
        self.language = settings.tts_language
        self.speed = settings.tts_speed
        self.output_dir = Path("./tts_output")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize TTS engines
        self._initialize_engines()
    
    def _initialize_engines(self):
        """Initialize available TTS engines."""
        if self.engine == "gtts" and GTTS_AVAILABLE:
            logger.info("Using gTTS engine")
        elif self.engine == "pyttsx3" and PYTTSX3_AVAILABLE:
            logger.info("Using pyttsx3 engine")
            self._init_pyttsx3()
        else:
            # Fallback to available engine
            if GTTS_AVAILABLE:
                self.engine = "gtts"
                logger.info("Falling back to gTTS engine")
            elif PYTTSX3_AVAILABLE:
                self.engine = "pyttsx3"
                logger.info("Falling back to pyttsx3 engine")
                self._init_pyttsx3()
            else:
                raise RuntimeError("No TTS engine available")
    
    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine."""
        try:
            self.pyttsx3_engine = pyttsx3.init()
            self.pyttsx3_engine.setProperty('rate', int(200 * self.speed))
            self.pyttsx3_engine.setProperty('volume', 0.9)
            
            # Get available voices
            voices = self.pyttsx3_engine.getProperty('voices')
            if voices:
                # Try to set voice based on language
                for voice in voices:
                    if self.language in voice.languages[0].lower():
                        self.pyttsx3_engine.setProperty('voice', voice.id)
                        break
                        
        except Exception as e:
            logger.error(f"Error initializing pyttsx3: {e}")
            raise
    
    def text_to_speech(self, text: str, language: Optional[str] = None, speed: Optional[float] = None) -> Dict:
        """
        Convert text to speech.
        
        Args:
            text: Text to convert to speech
            language: Language code (optional)
            speed: Speech speed multiplier (optional)
            
        Returns:
            Dictionary containing TTS results
        """
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            # Use provided parameters or defaults
            lang = language or self.language
            spd = speed or self.speed
            
            logger.info(f"Converting text to speech using {self.engine} engine")
            logger.info(f"Text length: {len(text)} characters")
            logger.info(f"Language: {lang}, Speed: {spd}")
            
            # Generate unique filename
            filename = f"{uuid.uuid4()}.mp3"
            output_path = self.output_dir / filename
            
            # Convert text to speech based on engine
            if self.engine == "gtts":
                audio_path = self._gtts_convert(text, lang, output_path)
            elif self.engine == "pyttsx3":
                audio_path = self._pyttsx3_convert(text, spd, output_path)
            else:
                raise ValueError(f"Unsupported TTS engine: {self.engine}")
            
            # Get audio metadata
            metadata = self._get_audio_metadata(audio_path)
            
            return {
                "audio_file_path": str(audio_path),
                "duration_seconds": metadata.get("duration", 0.0),
                "text_length": len(text),
                "filename": filename,
                "engine": self.engine,
                "language": lang,
                "speed": spd
            }
            
        except Exception as e:
            logger.error(f"Error in text-to-speech conversion: {e}")
            raise
    
    def _gtts_convert(self, text: str, language: str, output_path: Path) -> Path:
        """
        Convert text to speech using gTTS.
        
        Args:
            text: Text to convert
            language: Language code
            output_path: Output file path
            
        Returns:
            Path to generated audio file
        """
        try:
            # Create gTTS object
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Save audio file
            tts.save(str(output_path))
            
            logger.info(f"gTTS conversion completed: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error in gTTS conversion: {e}")
            raise
    
    def _pyttsx3_convert(self, text: str, speed: float, output_path: Path) -> Path:
        """
        Convert text to speech using pyttsx3.
        
        Args:
            text: Text to convert
            speed: Speech speed multiplier
            output_path: Output file path
            
        Returns:
            Path to generated audio file
        """
        try:
            # Set speech rate
            self.pyttsx3_engine.setProperty('rate', int(200 * speed))
            
            # Create temporary file for audio
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_path = Path(temp_file.name)
            temp_file.close()
            
            # Convert text to speech
            self.pyttsx3_engine.save_to_file(text, str(temp_path))
            self.pyttsx3_engine.runAndWait()
            
            # Convert WAV to MP3 using pydub if available
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_wav(str(temp_path))
                audio.export(str(output_path), format="mp3")
                
                # Clean up temporary file
                temp_path.unlink()
                
                logger.info(f"pyttsx3 conversion completed: {output_path}")
                return output_path
                
            except ImportError:
                # If pydub not available, use WAV file
                output_path = output_path.with_suffix('.wav')
                temp_path.rename(output_path)
                logger.info(f"pyttsx3 conversion completed (WAV): {output_path}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error in pyttsx3 conversion: {e}")
            raise
    
    def _get_audio_metadata(self, audio_path: Path) -> Dict:
        """
        Get metadata from generated audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary containing audio metadata
        """
        try:
            # Try to get duration using librosa
            import librosa
            y, sr = librosa.load(str(audio_path), sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            return {
                "duration": duration,
                "sample_rate": sr,
                "channels": 1 if len(y.shape) == 1 else y.shape[1]
            }
            
        except ImportError:
            # If librosa not available, return basic info
            return {
                "duration": 0.0,
                "sample_rate": 22050,
                "channels": 1
            }
        except Exception as e:
            logger.warning(f"Could not extract audio metadata: {e}")
            return {
                "duration": 0.0,
                "sample_rate": 22050,
                "channels": 1
            }
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Clean up old TTS audio files.
        
        Args:
            max_age_hours: Maximum age of files in hours
        """
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for file_path in self.output_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        logger.info(f"Cleaned up old TTS file: {file_path}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old TTS files: {e}")


# Global TTS service instance
tts_service = TTSService()
