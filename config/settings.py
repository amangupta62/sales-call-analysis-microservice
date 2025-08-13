"""Configuration settings for the Sales Call Analysis Microservice."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = Field(..., env="DATABASE_URL")
    database_test_url: str = Field(..., env="DATABASE_TEST_URL")
    
    # Redis Configuration
    redis_url: str = Field(..., env="REDIS_URL")
    redis_test_url: str = Field(..., env="REDIS_TEST_URL")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Celery Configuration
    celery_broker_url: str = Field(..., env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(..., env="CELERY_RESULT_BACKEND")
    
    # Audio Processing
    audio_upload_dir: str = Field(default="./uploads", env="AUDIO_UPLOAD_DIR")
    audio_max_size_mb: int = Field(default=50, env="AUDIO_MAX_SIZE_MB")
    supported_audio_formats: List[str] = Field(
        default=["wav", "mp3", "m4a"], 
        env="SUPPORTED_AUDIO_FORMATS"
    )
    
    # Whisper Model Configuration
    whisper_model: str = Field(default="base", env="WHISPER_MODEL")
    whisper_device: str = Field(default="cpu", env="WHISPER_DEVICE")
    
    # Sentiment Analysis
    sentiment_model: str = Field(
        default="cardiffnlp/twitter-roberta-base-sentiment-latest",
        env="SENTIMENT_MODEL"
    )
    
    # TTS Configuration
    tts_engine: str = Field(default="gtts", env="TTS_ENGINE")
    tts_language: str = Field(default="en", env="TTS_LANGUAGE")
    tts_speed: float = Field(default=1.0, env="TTS_SPEED")
    
    # Coachable Moment Detection
    coachable_moment_threshold: float = Field(
        default=0.7, 
        env="COACHABLE_MOMENT_THRESHOLD"
    )
    objection_keywords: List[str] = Field(
        default=["no", "not interested", "expensive", "think about it"],
        env="OBJECTION_KEYWORDS"
    )
    buying_signal_keywords: List[str] = Field(
        default=["yes", "interested", "when can we start", "what's next"],
        env="BUYING_SIGNAL_KEYWORDS"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
