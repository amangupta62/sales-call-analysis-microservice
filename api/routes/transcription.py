"""API routes for audio transcription and analysis."""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from loguru import logger

from models.database import get_db
from models.sales_call import SalesCall, Transcript, CoachableMoment, ExecutiveSummary
from schemas.sales_call import (
    AudioUploadResponse,
    TranscriptResponse,
    CoachableMomentResponse,
    ExecutiveSummaryResponse,
    SalesCallAnalysisResponse
)
from workers.tasks.transcription_tasks import process_audio_upload_task
from utils.audio_processor import audio_processor

router = APIRouter(prefix="/transcribe", tags=["transcription"])


@router.post("/upload", response_model=AudioUploadResponse)
async def upload_audio(
    background_tasks: BackgroundTasks,
    call_id: str = Form(...),
    agent_id: str = Form(...),
    customer_id: str = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload audio file for transcription and analysis.
    
    This endpoint accepts multipart form data with:
    - call_id: Unique identifier for the sales call
    - agent_id: ID of the sales agent
    - customer_id: ID of the customer
    - audio_file: Audio file (WAV, MP3, M4A)
    
    The audio will be processed asynchronously in the background.
    """
    try:
        # Validate file
        if not audio_file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check if call_id already exists
        existing_call = db.query(SalesCall).filter(SalesCall.call_id == call_id).first()
        if existing_call:
            raise HTTPException(status_code=400, detail=f"Call ID {call_id} already exists")
        
        # Validate audio file
        is_valid, error_message = audio_processor.validate_audio_file(
            audio_file.filename, audio_file.size
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Read file content
        file_content = await audio_file.read()
        
        # Save audio file
        file_path, filename = audio_processor.save_audio_file(file_content, audio_file.filename)
        
        # Start background processing
        background_tasks.add_task(
            process_audio_upload_task.delay,
            call_id,
            agent_id,
            customer_id,
            file_path,
            audio_file.filename
        )
        
        logger.info(f"Audio upload initiated for call {call_id}")
        
        return AudioUploadResponse(
            call_id=call_id,
            message="Audio file uploaded successfully. Processing started in background.",
            status="uploaded",
            audio_file_path=file_path
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading audio: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{call_id}/status", response_model=dict)
async def get_transcription_status(call_id: str, db: Session = Depends(get_db)):
    """
    Get the status of transcription for a specific call.
    
    Returns the current status and processing information.
    """
    try:
        sales_call = db.query(SalesCall).filter(SalesCall.call_id == call_id).first()
        if not sales_call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        return {
            "call_id": call_id,
            "status": sales_call.status,
            "created_at": sales_call.created_at,
            "updated_at": sales_call.updated_at,
            "duration_seconds": sales_call.duration_seconds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcription status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{call_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(call_id: str, db: Session = Depends(get_db)):
    """
    Get the transcript for a specific call.
    
    Returns the full transcript with speaker diarization and sentiment analysis.
    """
    try:
        sales_call = db.query(SalesCall).filter(SalesCall.call_id == call_id).first()
        if not sales_call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        if not sales_call.transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        # Convert to response schema
        transcript = sales_call.transcript
        segments = []
        
        for utterance in transcript.utterances:
            segment = {
                "speaker_id": utterance.speaker_id,
                "text": utterance.text,
                "start_time": utterance.start_time,
                "end_time": utterance.end_time,
                "confidence": utterance.confidence,
                "sentiment_score": utterance.sentiment_score,
                "sentiment_label": utterance.sentiment_label
            }
            segments.append(segment)
        
        return TranscriptResponse(
            id=transcript.id,
            sales_call_id=transcript.sales_call_id,
            full_transcript=transcript.full_transcript,
            segments=segments,
            sentiment_scores=transcript.sentiment_scores,
            created_at=transcript.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transcript: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{call_id}/coachable-moments", response_model=List[CoachableMomentResponse])
async def get_coachable_moments(call_id: str, db: Session = Depends(get_db)):
    """
    Get coachable moments detected in a specific call.
    
    Returns list of detected coachable moments with recommendations.
    """
    try:
        sales_call = db.query(SalesCall).filter(SalesCall.call_id == call_id).first()
        if not sales_call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        coachable_moments = sales_call.coachable_moments
        
        # Convert to response schema
        response_moments = []
        for moment in coachable_moments:
            response_moment = CoachableMomentResponse(
                id=moment.id,
                sales_call_id=moment.sales_call_id,
                moment_type=moment.moment_type,
                confidence=moment.confidence,
                start_time=moment.start_time,
                end_time=moment.end_time,
                description=moment.description,
                transcript_segment=moment.transcript_segment,
                recommendations=moment.recommendations,
                created_at=moment.created_at
            )
            response_moments.append(response_moment)
        
        return response_moments
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coachable moments: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{call_id}/executive-summary", response_model=ExecutiveSummaryResponse)
async def get_executive_summary(call_id: str, db: Session = Depends(get_db)):
    """
    Get the executive summary for a specific call.
    
    Returns comprehensive summary with key points and action items.
    """
    try:
        sales_call = db.query(SalesCall).filter(SalesCall.call_id == call_id).first()
        if not sales_call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        if not sales_call.executive_summary:
            raise HTTPException(status_code=404, detail="Executive summary not found")
        
        summary = sales_call.executive_summary
        
        return ExecutiveSummaryResponse(
            id=summary.id,
            sales_call_id=summary.sales_call_id,
            summary=summary.summary,
            key_points=summary.key_points,
            action_items=summary.action_items,
            sentiment_overview=summary.sentiment_overview,
            call_outcome=summary.call_outcome,
            created_at=summary.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting executive summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{call_id}/analysis", response_model=SalesCallAnalysisResponse)
async def get_complete_analysis(call_id: str, db: Session = Depends(get_db)):
    """
    Get complete analysis for a specific call.
    
    Returns all analysis components: transcript, coachable moments, and executive summary.
    """
    try:
        sales_call = db.query(SalesCall).filter(SalesCall.call_id == call_id).first()
        if not sales_call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Check if analysis is complete
        if sales_call.status != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"Analysis not complete. Current status: {sales_call.status}"
            )
        
        # Get transcript
        transcript_response = None
        if sales_call.transcript:
            transcript = sales_call.transcript
            segments = []
            for utterance in transcript.utterances:
                segment = {
                    "speaker_id": utterance.speaker_id,
                    "text": utterance.text,
                    "start_time": utterance.start_time,
                    "end_time": utterance.end_time,
                    "confidence": utterance.confidence,
                    "sentiment_score": utterance.sentiment_score,
                    "sentiment_label": utterance.sentiment_label
                }
                segments.append(segment)
            
            transcript_response = TranscriptResponse(
                id=transcript.id,
                sales_call_id=transcript.sales_call_id,
                full_transcript=transcript.full_transcript,
                segments=segments,
                sentiment_scores=transcript.sentiment_scores,
                created_at=transcript.created_at
            )
        
        # Get coachable moments
        coachable_moments_response = []
        for moment in sales_call.coachable_moments:
            response_moment = CoachableMomentResponse(
                id=moment.id,
                sales_call_id=moment.sales_call_id,
                moment_type=moment.moment_type,
                confidence=moment.confidence,
                start_time=moment.start_time,
                end_time=moment.end_time,
                description=moment.description,
                transcript_segment=moment.transcript_segment,
                recommendations=moment.recommendations,
                created_at=moment.created_at
            )
            coachable_moments_response.append(response_moment)
        
        # Get executive summary
        executive_summary_response = None
        if sales_call.executive_summary:
            summary = sales_call.executive_summary
            executive_summary_response = ExecutiveSummaryResponse(
                id=summary.id,
                sales_call_id=summary.sales_call_id,
                summary=summary.summary,
                key_points=summary.key_points,
                action_items=summary.action_items,
                sentiment_overview=summary.sentiment_overview,
                call_outcome=summary.call_outcome,
                created_at=summary.created_at
            )
        
        # Calculate processing time (approximate)
        processing_time = 0.0
        if sales_call.created_at and sales_call.updated_at:
            processing_time = (sales_call.updated_at - sales_call.created_at).total_seconds()
        
        return SalesCallAnalysisResponse(
            sales_call={
                "id": sales_call.id,
                "call_id": sales_call.call_id,
                "agent_id": sales_call.agent_id,
                "customer_id": sales_call.customer_id,
                "audio_file_path": sales_call.audio_file_path,
                "duration_seconds": sales_call.duration_seconds,
                "status": sales_call.status,
                "created_at": sales_call.created_at,
                "updated_at": sales_call.updated_at
            },
            transcript=transcript_response,
            coachable_moments=coachable_moments_response,
            executive_summary=executive_summary_response,
            analysis_status=sales_call.status,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting complete analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=List[dict])
async def list_sales_calls(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """
    List all sales calls with optional filtering.
    
    Returns paginated list of sales calls with basic information.
    """
    try:
        query = db.query(SalesCall)
        
        # Apply status filter if provided
        if status:
            query = query.filter(SalesCall.status == status)
        
        # Apply pagination
        sales_calls = query.offset(skip).limit(limit).all()
        
        # Convert to response format
        response_calls = []
        for call in sales_calls:
            response_call = {
                "id": call.id,
                "call_id": call.call_id,
                "agent_id": call.agent_id,
                "customer_id": call.customer_id,
                "status": call.status,
                "duration_seconds": call.duration_seconds,
                "created_at": call.created_at,
                "updated_at": call.updated_at
            }
            response_calls.append(response_call)
        
        return response_calls
        
    except Exception as e:
        logger.error(f"Error listing sales calls: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
