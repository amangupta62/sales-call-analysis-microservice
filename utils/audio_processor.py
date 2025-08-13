"""Audio processing utilities for handling audio files."""

import os
import uuid
from pathlib import Path
from typing import Tuple, Optional
import librosa
from pydub import AudioSegment
from loguru import logger

from config.settings import settings


class AudioProcessor:
    """Handles audio file processing and validation."""
    
    def __init__(self):
        """Initialize audio processor."""
        self.upload_dir = Path(settings.audio_upload_dir)
        self.max_size_bytes = settings.audio_max_size_mb * 1024 * 1024
        self.supported_formats = settings.supported_audio_formats
        
        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_audio_file(self, file_path: str, file_size: int) -> Tuple[bool, str]:
        """
        Validate audio file format and size.
        
        Args:
            file_path: Path to the audio file
            file_size: Size of the file in bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        if file_size > self.max_size_bytes:
            return False, f"File size {file_size} bytes exceeds maximum allowed size {self.max_size_bytes} bytes"
        
        # Check file format
        file_extension = Path(file_path).suffix.lower().lstrip('.')
        if file_extension not in self.supported_formats:
            return False, f"Unsupported audio format: {file_extension}. Supported formats: {', '.join(self.supported_formats)}"
        
        return True, ""
    
    def save_audio_file(self, file_content: bytes, original_filename: str) -> Tuple[str, str]:
        """
        Save uploaded audio file to disk.
        
        Args:
            file_content: Raw file content
            original_filename: Original filename
            
        Returns:
            Tuple of (saved_file_path, unique_filename)
        """
        # Generate unique filename
        file_extension = Path(original_filename).suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = self.upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"Saved audio file: {file_path}")
        return str(file_path), unique_filename
    
    def get_audio_metadata(self, file_path: str) -> dict:
        """
        Extract metadata from audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing audio metadata
        """
        try:
            # Load audio with librosa
            y, sr = librosa.load(file_path, sr=None)
            
            # Get duration
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Get number of channels
            if len(y.shape) > 1:
                channels = y.shape[1]
            else:
                channels = 1
            
            # Get file size
            file_size = os.path.getsize(file_path)
            
            return {
                "duration_seconds": duration,
                "sample_rate": sr,
                "channels": channels,
                "file_size_bytes": file_size,
                "format": Path(file_path).suffix.lower().lstrip('.')
            }
        except Exception as e:
            logger.error(f"Error extracting audio metadata: {e}")
            return {}
    
    def convert_audio_format(self, input_path: str, output_format: str = "wav") -> Optional[str]:
        """
        Convert audio file to specified format.
        
        Args:
            input_path: Path to input audio file
            output_format: Desired output format
            
        Returns:
            Path to converted audio file or None if conversion fails
        """
        try:
            # Load audio with pydub
            audio = AudioSegment.from_file(input_path)
            
            # Generate output path
            output_path = str(Path(input_path).with_suffix(f".{output_format}"))
            
            # Export to new format
            audio.export(output_path, format=output_format)
            
            logger.info(f"Converted audio to {output_format}: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            return None
    
    def normalize_audio(self, file_path: str) -> Optional[str]:
        """
        Normalize audio levels for better transcription.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Path to normalized audio file or None if normalization fails
        """
        try:
            # Load audio with pydub
            audio = AudioSegment.from_file(file_path)
            
            # Normalize audio
            normalized_audio = audio.normalize()
            
            # Generate output path
            output_path = str(Path(file_path).with_suffix(".normalized.wav"))
            
            # Export normalized audio
            normalized_audio.export(output_path, format="wav")
            
            logger.info(f"Normalized audio: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error normalizing audio: {e}")
            return None
    
    def cleanup_temp_files(self, file_paths: list):
        """
        Clean up temporary audio files.
        
        Args:
            file_paths: List of file paths to delete
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up file {file_path}: {e}")


# Global audio processor instance
audio_processor = AudioProcessor()
