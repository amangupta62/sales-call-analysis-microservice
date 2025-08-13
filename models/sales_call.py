"""Database models for sales calls and related entities."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List

from models.database import Base


class SalesCall(Base):
    """Sales call entity."""
    
    __tablename__ = "sales_calls"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String(255), unique=True, index=True, nullable=False)
    agent_id = Column(String(255), index=True, nullable=False)
    customer_id = Column(String(255), index=True, nullable=False)
    audio_file_path = Column(String(500), nullable=False)
    duration_seconds = Column(Float, nullable=True)
    status = Column(String(50), default="processing")  # processing, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    transcript = relationship("Transcript", back_populates="sales_call", uselist=False)
    coachable_moments = relationship("CoachableMoment", back_populates="sales_call")
    executive_summary = relationship("ExecutiveSummary", back_populates="sales_call", uselist=False)


class Transcript(Base):
    """Transcript entity for sales calls."""
    
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    sales_call_id = Column(Integer, ForeignKey("sales_calls.id"), nullable=False)
    full_transcript = Column(Text, nullable=False)
    segments = Column(JSON, nullable=True)  # Speaker diarization segments
    sentiment_scores = Column(JSON, nullable=True)  # Overall sentiment analysis
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sales_call = relationship("SalesCall", back_populates="transcript")
    utterances = relationship("Utterance", back_populates="transcript")


class Utterance(Base):
    """Individual utterance with speaker identification and sentiment."""
    
    __tablename__ = "utterances"
    
    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"), nullable=False)
    speaker_id = Column(String(50), nullable=False)  # agent, customer, or speaker_1, speaker_2
    text = Column(Text, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    confidence = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String(50), nullable=True)  # positive, negative, neutral
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    transcript = relationship("Transcript", back_populates="utterances")


class CoachableMoment(Base):
    """Detected coachable moments in sales calls."""
    
    __tablename__ = "coachable_moments"
    
    id = Column(Integer, primary_key=True, index=True)
    sales_call_id = Column(Integer, ForeignKey("sales_calls.id"), nullable=False)
    moment_type = Column(String(100), nullable=False)  # objection, buying_signal, etc.
    confidence = Column(Float, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    transcript_segment = Column(Text, nullable=False)
    recommendations = Column(JSON, nullable=True)  # Coaching recommendations
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sales_call = relationship("SalesCall", back_populates="coachable_moments")


class ExecutiveSummary(Base):
    """Executive summary of sales calls."""
    
    __tablename__ = "executive_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    sales_call_id = Column(Integer, ForeignKey("sales_calls.id"), nullable=False)
    summary = Column(Text, nullable=False)
    key_points = Column(JSON, nullable=True)  # List of key points
    action_items = Column(JSON, nullable=True)  # List of action items
    sentiment_overview = Column(String(100), nullable=True)  # Overall sentiment
    call_outcome = Column(String(100), nullable=True)  # success, follow_up, lost
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sales_call = relationship("SalesCall", back_populates="executive_summary")


class AudioFile(Base):
    """Audio file metadata and storage information."""
    
    __tablename__ = "audio_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    format = Column(String(20), nullable=False)  # wav, mp3, m4a
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
