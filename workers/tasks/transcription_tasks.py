"""Background tasks for audio transcription processing."""

import time
from typing import Dict, Any
from loguru import logger
from sqlalchemy.orm import Session

from workers.celery_app import celery_app
from models.database import get_db_context
from models.sales_call import SalesCall, Transcript, Utterance
from services.transcription_service import transcription_service
from services.coachable_moment_service import coachable_moment_service
from services.executive_summary_service import executive_summary_service
from utils.audio_processor import audio_processor


@celery_app.task(bind=True, name="transcribe_audio")
def transcribe_audio_task(self, sales_call_id: int, audio_file_path: str):
    """
    Background task for transcribing audio files.
    
    Args:
        sales_call_id: ID of the sales call
        audio_file_path: Path to the audio file
        
    Returns:
        Dictionary containing task results
    """
    start_time = time.time()
    task_id = self.request.id
    
    try:
        logger.info(f"Starting transcription task {task_id} for sales call {sales_call_id}")
        
        # Update sales call status to processing
        with get_db_context() as db:
            sales_call = db.query(SalesCall).filter(SalesCall.id == sales_call_id).first()
            if not sales_call:
                raise ValueError(f"Sales call {sales_call_id} not found")
            
            sales_call.status = "processing"
            db.commit()
        
        # Transcribe audio
        transcription_result = transcription_service.transcribe_audio(audio_file_path)
        
        # Detect coachable moments
        coachable_moments = coachable_moment_service.detect_coachable_moments(
            transcription_result["segments"]
        )
        
        # Generate executive summary
        executive_summary = executive_summary_service.generate_executive_summary(
            transcription_result,
            coachable_moments,
            transcription_result["sentiment_scores"]
        )
        
        # Save results to database
        with get_db_context() as db:
            # Create transcript
            transcript, utterances = transcription_service.create_transcript_models(
                sales_call_id, transcription_result
            )
            db.add(transcript)
            db.flush()  # Get transcript ID
            
            # Update utterances with transcript ID
            for utterance in utterances:
                utterance.transcript_id = transcript.id
                db.add(utterance)
            
            # Create coachable moments
            coachable_moment_models = coachable_moment_service.create_coachable_moment_models(
                sales_call_id, coachable_moments
            )
            for moment in coachable_moment_models:
                db.add(moment)
            
            # Create executive summary
            summary_model = executive_summary_service.create_executive_summary_model(
                sales_call_id, executive_summary
            )
            db.add(summary_model)
            
            # Update sales call status and duration
            sales_call.status = "completed"
            sales_call.duration_seconds = transcription_result.get("duration", 0.0)
            
            db.commit()
        
        processing_time = time.time() - start_time
        logger.info(f"Transcription task {task_id} completed successfully in {processing_time:.2f}s")
        
        return {
            "status": "success",
            "sales_call_id": sales_call_id,
            "transcript_id": transcript.id,
            "coachable_moments_count": len(coachable_moments),
            "processing_time": processing_time,
            "task_id": task_id
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Transcription task {task_id} failed after {processing_time:.2f}s: {e}")
        
        # Update sales call status to failed
        try:
            with get_db_context() as db:
                sales_call = db.query(SalesCall).filter(SalesCall.id == sales_call_id).first()
                if sales_call:
                    sales_call.status = "failed"
                    db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update sales call status: {db_error}")
        
        # Re-raise the exception for Celery to handle
        raise


@celery_app.task(bind=True, name="process_audio_upload")
def process_audio_upload_task(self, call_id: str, agent_id: str, customer_id: str, 
                             audio_file_path: str, original_filename: str):
    """
    Background task for processing audio uploads.
    
    Args:
        call_id: Unique call identifier
        agent_id: ID of the sales agent
        customer_id: ID of the customer
        audio_file_path: Path to the uploaded audio file
        original_filename: Original filename
        
    Returns:
        Dictionary containing task results
    """
    start_time = time.time()
    task_id = self.request.id
    
    try:
        logger.info(f"Starting audio upload processing task {task_id} for call {call_id}")
        
        # Get audio metadata
        audio_metadata = audio_processor.get_audio_metadata(audio_file_path)
        
        # Create sales call record
        with get_db_context() as db:
            sales_call = SalesCall(
                call_id=call_id,
                agent_id=agent_id,
                customer_id=customer_id,
                audio_file_path=audio_file_path,
                duration_seconds=audio_metadata.get("duration_seconds"),
                status="uploaded"
            )
            db.add(sales_call)
            db.commit()
            
            sales_call_id = sales_call.id
        
        # Start transcription task
        transcribe_audio_task.delay(sales_call_id, audio_file_path)
        
        processing_time = time.time() - start_time
        logger.info(f"Audio upload processing task {task_id} completed in {processing_time:.2f}s")
        
        return {
            "status": "success",
            "call_id": call_id,
            "sales_call_id": sales_call_id,
            "audio_metadata": audio_metadata,
            "processing_time": processing_time,
            "task_id": task_id
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Audio upload processing task {task_id} failed after {processing_time:.2f}s: {e}")
        raise


@celery_app.task(bind=True, name="retry_failed_transcription")
def retry_failed_transcription_task(self, sales_call_id: int, max_retries: int = 3):
    """
    Background task for retrying failed transcriptions.
    
    Args:
        sales_call_id: ID of the sales call to retry
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dictionary containing task results
    """
    start_time = time.time()
    task_id = self.request.id
    
    try:
        logger.info(f"Starting retry task {task_id} for sales call {sales_call_id}")
        
        with get_db_context() as db:
            sales_call = db.query(SalesCall).filter(SalesCall.id == sales_call_id).first()
            if not sales_call:
                raise ValueError(f"Sales call {sales_call_id} not found")
            
            # Check if we should retry
            if sales_call.status == "failed":
                # Reset status and retry transcription
                sales_call.status = "processing"
                db.commit()
                
                # Start transcription task
                transcribe_audio_task.delay(sales_call_id, sales_call.audio_file_path)
                
                processing_time = time.time() - start_time
                logger.info(f"Retry task {task_id} initiated for sales call {sales_call_id}")
                
                return {
                    "status": "retry_initiated",
                    "sales_call_id": sales_call_id,
                    "processing_time": processing_time,
                    "task_id": task_id
                }
            else:
                return {
                    "status": "no_retry_needed",
                    "sales_call_id": sales_call_id,
                    "current_status": sales_call.status,
                    "processing_time": time.time() - start_time,
                    "task_id": task_id
                }
                
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Retry task {task_id} failed after {processing_time:.2f}s: {e}")
        raise


@celery_app.task(bind=True, name="cleanup_audio_files")
def cleanup_audio_files_task(self, max_age_hours: int = 24):
    """
    Background task for cleaning up old audio files.
    
    Args:
        max_age_hours: Maximum age of files in hours
        
    Returns:
        Dictionary containing cleanup results
    """
    start_time = time.time()
    task_id = self.request.id
    
    try:
        logger.info(f"Starting audio cleanup task {task_id}")
        
        # Clean up old TTS files
        from services.tts_service import tts_service
        tts_service.cleanup_old_files(max_age_hours)
        
        # Clean up old upload files (optional)
        # audio_processor.cleanup_temp_files([])
        
        processing_time = time.time() - start_time
        logger.info(f"Audio cleanup task {task_id} completed in {processing_time:.2f}s")
        
        return {
            "status": "success",
            "max_age_hours": max_age_hours,
            "processing_time": processing_time,
            "task_id": task_id
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Audio cleanup task {task_id} failed after {processing_time:.2f}s: {e}")
        raise
