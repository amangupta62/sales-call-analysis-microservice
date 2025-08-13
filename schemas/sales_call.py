"""Pydantic schemas for sales call API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SalesCallBase(BaseModel):
    """Base sales call schema."""
    call_id: str = Field(..., description="Unique identifier for the sales call")
    agent_id: str = Field(..., description="ID of the sales agent")
    customer_id: str = Field(..., description="ID of the customer")


class SalesCallCreate(SalesCallBase):
    """Schema for creating a new sales call."""
    pass


class SalesCallResponse(SalesCallBase):
    """Schema for sales call response."""
    id: int
    audio_file_path: str
    duration_seconds: Optional[float] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TranscriptSegment(BaseModel):
    """Schema for transcript segment with speaker diarization."""
    speaker_id: str = Field(..., description="Speaker identifier")
    text: str = Field(..., description="Transcribed text")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    confidence: Optional[float] = Field(None, description="Confidence score")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score")
    sentiment_label: Optional[str] = Field(None, description="Sentiment label")


class TranscriptResponse(BaseModel):
    """Schema for transcript response."""
    id: int
    sales_call_id: int
    full_transcript: str
    segments: List[TranscriptSegment]
    sentiment_scores: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CoachableMomentResponse(BaseModel):
    """Schema for coachable moment response."""
    id: int
    sales_call_id: int
    moment_type: str
    confidence: float
    start_time: float
    end_time: float
    description: str
    transcript_segment: str
    recommendations: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExecutiveSummaryResponse(BaseModel):
    """Schema for executive summary response."""
    id: int
    sales_call_id: int
    summary: str
    key_points: Optional[List[str]] = None
    action_items: Optional[List[str]] = None
    sentiment_overview: Optional[str] = None
    call_outcome: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TTSRequest(BaseModel):
    """Schema for text-to-speech request."""
    text: str = Field(..., description="Text to convert to speech")
    language: Optional[str] = Field("en", description="Language code")
    speed: Optional[float] = Field(1.0, description="Speech speed multiplier")


class TTSResponse(BaseModel):
    """Schema for text-to-speech response."""
    audio_file_path: str
    duration_seconds: float
    text_length: int


class AudioUploadResponse(BaseModel):
    """Schema for audio upload response."""
    call_id: str
    message: str
    status: str
    audio_file_path: Optional[str] = None


class CoachableMomentDetectionResponse(BaseModel):
    """Schema for coachable moment detection response."""
    call_id: str
    moments_found: int
    moments: List[CoachableMomentResponse]
    processing_time: float


class SalesCallAnalysisResponse(BaseModel):
    """Schema for complete sales call analysis response."""
    sales_call: SalesCallResponse
    transcript: Optional[TranscriptResponse] = None
    coachable_moments: List[CoachableMomentResponse] = []
    executive_summary: Optional[ExecutiveSummaryResponse] = None
    analysis_status: str
    processing_time: float
