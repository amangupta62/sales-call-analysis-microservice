"""Transcription service using OpenAI Whisper for speech-to-text conversion."""

import os
import whisper
from typing import Dict, List, Tuple, Optional
from loguru import logger
import torch

from config.settings import settings
from models.sales_call import Transcript, Utterance
from services.sentiment_service import SentimentService


class TranscriptionService:
    """Handles audio transcription using Whisper model."""
    
    def __init__(self):
        """Initialize transcription service."""
        self.model_name = settings.whisper_model
        self.device = settings.whisper_device
        self.model = None
        self.sentiment_service = SentimentService()
        
        # Load Whisper model
        self._load_model()
    
    def _load_model(self):
        """Load Whisper model."""
        try:
            logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name, device=self.device)
            logger.info(f"Whisper model loaded successfully on device: {self.device}")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            raise
    
    def transcribe_audio(self, audio_file_path: str) -> Dict:
        """
        Transcribe audio file using Whisper.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dictionary containing transcription results
        """
        try:
            logger.info(f"Starting transcription of: {audio_file_path}")
            
            # Transcribe audio
            result = self.model.transcribe(
                audio_file_path,
                verbose=True,
                word_timestamps=True
            )
            
            # Process transcription results
            processed_result = self._process_transcription_result(result)
            
            logger.info(f"Transcription completed successfully")
            return processed_result
            
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise
    
    def _process_transcription_result(self, result: Dict) -> Dict:
        """
        Process raw Whisper transcription result.
        
        Args:
            result: Raw Whisper transcription result
            
        Returns:
            Processed transcription result
        """
        try:
            # Extract basic information
            full_transcript = result["text"]
            segments = result.get("segments", [])
            
            # Process segments for speaker diarization
            processed_segments = []
            utterances = []
            
            for segment in segments:
                # Create utterance
                utterance = {
                    "speaker_id": f"speaker_{len(utterances) % 2 + 1}",  # Simple alternating speaker
                    "text": segment["text"].strip(),
                    "start_time": segment["start"],
                    "end_time": segment["end"],
                    "confidence": segment.get("avg_logprob", 0.0),
                    "words": segment.get("words", [])
                }
                
                # Analyze sentiment for this utterance
                sentiment_result = self.sentiment_service.analyze_sentiment(utterance["text"])
                utterance["sentiment_score"] = sentiment_result["score"]
                utterance["sentiment_label"] = sentiment_result["label"]
                
                processed_segments.append(utterance)
                utterances.append(utterance)
            
            # Calculate overall sentiment
            overall_sentiment = self._calculate_overall_sentiment(utterances)
            
            return {
                "full_transcript": full_transcript,
                "segments": processed_segments,
                "utterances": utterances,
                "sentiment_scores": overall_sentiment,
                "duration": segments[-1]["end"] if segments else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error processing transcription result: {e}")
            raise
    
    def _calculate_overall_sentiment(self, utterances: List[Dict]) -> Dict:
        """
        Calculate overall sentiment from individual utterances.
        
        Args:
            utterances: List of utterance dictionaries
            
        Returns:
            Dictionary containing overall sentiment scores
        """
        if not utterances:
            return {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
        
        total_score = 0.0
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        
        for utterance in utterances:
            score = utterance.get("sentiment_score", 0.0)
            total_score += score
            
            label = utterance.get("sentiment_label", "neutral")
            sentiment_counts[label] += 1
        
        avg_score = total_score / len(utterances)
        
        return {
            "average_score": avg_score,
            "positive": sentiment_counts["positive"],
            "negative": sentiment_counts["negative"],
            "neutral": sentiment_counts["neutral"],
            "overall_label": "positive" if avg_score > 0.1 else "negative" if avg_score < -0.1 else "neutral"
        }
    
    def create_transcript_models(self, sales_call_id: int, transcription_result: Dict) -> Tuple[Transcript, List[Utterance]]:
        """
        Create database models from transcription result.
        
        Args:
            sales_call_id: ID of the sales call
            transcription_result: Processed transcription result
            
        Returns:
            Tuple of (Transcript, List[Utterance])
        """
        try:
            # Create transcript
            transcript = Transcript(
                sales_call_id=sales_call_id,
                full_transcript=transcription_result["full_transcript"],
                segments=transcription_result["segments"],
                sentiment_scores=transcription_result["sentiment_scores"]
            )
            
            # Create utterances
            utterances = []
            for utterance_data in transcription_result["utterances"]:
                utterance = Utterance(
                    transcript_id=0,  # Will be set after transcript is saved
                    speaker_id=utterance_data["speaker_id"],
                    text=utterance_data["text"],
                    start_time=utterance_data["start_time"],
                    end_time=utterance_data["end_time"],
                    confidence=utterance_data["confidence"],
                    sentiment_score=utterance_data["sentiment_score"],
                    sentiment_label=utterance_data["sentiment_label"]
                )
                utterances.append(utterance)
            
            return transcript, utterances
            
        except Exception as e:
            logger.error(f"Error creating transcript models: {e}")
            raise


# Global transcription service instance
transcription_service = TranscriptionService()
