"""API routes for coachable moment replay functionality."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from loguru import logger

from models.database import get_db
from models.sales_call import SalesCall, CoachableMoment, Transcript
from schemas.sales_call import CoachableMomentResponse
from services.tts_service import tts_service
from workers.tasks.analysis_tasks import analyze_coachable_moments_task

router = APIRouter(prefix="/replay", tags=["replay"])


@router.get("/{call_id}/moments", response_model=List[CoachableMomentResponse])
async def get_coachable_moments_for_replay(
    call_id: str,
    moment_type: Optional[str] = Query(None, description="Filter by moment type"),
    confidence_threshold: Optional[float] = Query(0.7, description="Minimum confidence threshold"),
    db: Session = Depends(get_db)
):
    """
    Get coachable moments for replay functionality.
    
    Returns filtered list of coachable moments that can be replayed.
    """
    try:
        sales_call = db.query(SalesCall).filter(SalesCall.call_id == call_id).first()
        if not sales_call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Query coachable moments
        query = db.query(CoachableMoment).filter(CoachableMoment.sales_call_id == sales_call.id)
        
        # Apply filters
        if moment_type:
            query = query.filter(CoachableMoment.moment_type == moment_type)
        
        if confidence_threshold:
            query = query.filter(CoachableMoment.confidence >= confidence_threshold)
        
        # Order by confidence and start time
        coachable_moments = query.order_by(
            CoachableMoment.confidence.desc(),
            CoachableMoment.start_time
        ).all()
        
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
        logger.error(f"Error getting coachable moments for replay: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{call_id}/moment/{moment_id}/replay")
async def replay_coachable_moment(
    call_id: str,
    moment_id: int,
    include_context: bool = Query(True, description="Include surrounding context"),
    context_seconds: int = Query(5, description="Context seconds before and after"),
    db: Session = Depends(get_db)
):
    """
    Replay a specific coachable moment with optional context.
    
    Generates TTS audio for the moment and returns audio file information.
    """
    try:
        # Get sales call and moment
        sales_call = db.query(SalesCall).filter(SalesCall.call_id == call_id).first()
        if not sales_call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        moment = db.query(CoachableMoment).filter(
            CoachableMoment.id == moment_id,
            CoachableMoment.sales_call_id == sales_call.id
        ).first()
        
        if not moment:
            raise HTTPException(status_code=404, detail="Coachable moment not found")
        
        # Get transcript for context
        transcript = sales_call.transcript
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        # Build replay text
        replay_text = self._build_replay_text(moment, transcript, include_context, context_seconds)
        
        # Generate TTS audio
        tts_result = tts_service.text_to_speech(
            text=replay_text,
            language="en",  # Default to English for now
            speed=1.0
        )
        
        logger.info(f"Replay generated for moment {moment_id} in call {call_id}")
        
        return {
            "moment_id": moment_id,
            "call_id": call_id,
            "replay_text": replay_text,
            "audio_file_path": tts_result["audio_file_path"],
            "duration_seconds": tts_result["duration_seconds"],
            "moment_type": moment.moment_type,
            "confidence": moment.confidence,
            "start_time": moment.start_time,
            "end_time": moment.end_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error replaying coachable moment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{call_id}/moment/{moment_id}/replay-with-recommendations")
async def replay_moment_with_recommendations(
    call_id: str,
    moment_id: int,
    include_recommendations: bool = Query(True, description="Include coaching recommendations"),
    db: Session = Depends(get_db)
):
    """
    Replay a coachable moment with coaching recommendations.
    
    Generates TTS audio that includes the moment and actionable recommendations.
    """
    try:
        # Get sales call and moment
        sales_call = db.query(SalesCall).filter(SalesCall.call_id == call_id).first()
        if not sales_call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        moment = db.query(CoachableMoment).filter(
            CoachableMoment.id == moment_id,
            CoachableMoment.sales_call_id == sales_call.id
        ).first()
        
        if not moment:
            raise HTTPException(status_code=404, detail="Coachable moment not found")
        
        # Build replay text with recommendations
        replay_text = self._build_replay_text_with_recommendations(moment)
        
        # Generate TTS audio
        tts_result = tts_service.text_to_speech(
            text=replay_text,
            language="en",
            speed=0.9  # Slightly slower for better comprehension
        )
        
        logger.info(f"Replay with recommendations generated for moment {moment_id} in call {call_id}")
        
        return {
            "moment_id": moment_id,
            "call_id": call_id,
            "replay_text": replay_text,
            "audio_file_path": tts_result["audio_file_path"],
            "duration_seconds": tts_result["duration_seconds"],
            "moment_type": moment.moment_type,
            "confidence": moment.confidence,
            "recommendations_included": include_recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error replaying moment with recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{call_id}/analyze-moments")
async def trigger_moment_analysis(
    call_id: str,
    db: Session = Depends(get_db)
):
    """
    Trigger re-analysis of coachable moments for a call.
    
    Useful for updating moment detection with new algorithms or parameters.
    """
    try:
        sales_call = db.query(SalesCall).filter(SalesCall.call_id == call_id).first()
        if not sales_call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Check if transcript exists
        if not sales_call.transcript:
            raise HTTPException(status_code=400, detail="Transcript not found - cannot analyze moments")
        
        # Trigger background analysis
        analyze_coachable_moments_task.delay(sales_call.id)
        
        logger.info(f"Coachable moment analysis triggered for call {call_id}")
        
        return {
            "message": "Coachable moment analysis started in background",
            "call_id": call_id,
            "status": "analysis_started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering moment analysis: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{call_id}/moment-types")
async def get_available_moment_types(call_id: str, db: Session = Depends(get_db)):
    """
    Get available moment types for a specific call.
    
    Returns unique moment types and their counts.
    """
    try:
        sales_call = db.query(SalesCall).filter(SalesCall.call_id == call_id).first()
        if not sales_call:
            raise HTTPException(status_code=404, detail="Call not found")
        
        # Get moment types and counts
        moment_types = db.query(
            CoachableMoment.moment_type,
            db.func.count(CoachableMoment.id).label("count")
        ).filter(
            CoachableMoment.sales_call_id == sales_call.id
        ).group_by(CoachableMoment.moment_type).all()
        
        return {
            "call_id": call_id,
            "moment_types": [
                {
                    "type": moment_type,
                    "count": count
                }
                for moment_type, count in moment_types
            ],
            "total_moments": sum(count for _, count in moment_types)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting moment types: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def _build_replay_text(self, moment, transcript, include_context: bool, context_seconds: int) -> str:
    """Build replay text with optional context."""
    replay_parts = []
    
    if include_context:
        # Add context before the moment
        context_start = max(0, moment.start_time - context_seconds)
        context_end = moment.start_time
        
        context_utterances = [
            u for u in transcript.utterances
            if context_start <= u.start_time < context_end
        ]
        
        if context_utterances:
            replay_parts.append("Context leading up to the moment:")
            for utterance in context_utterances:
                replay_parts.append(f"{utterance.speaker_id}: {utterance.text}")
            replay_parts.append("")
    
    # Add the moment itself
    replay_parts.append(f"Coachable moment - {moment.moment_type}:")
    replay_parts.append(f"{moment.transcript_segment}")
    replay_parts.append("")
    
    if include_context:
        # Add context after the moment
        context_start = moment.end_time
        context_end = moment.end_time + context_seconds
        
        context_utterances = [
            u for u in transcript.utterances
            if context_start <= u.start_time < context_end
        ]
        
        if context_utterances:
            replay_parts.append("Context following the moment:")
            for utterance in context_utterances:
                replay_parts.append(f"{utterance.speaker_id}: {utterance.text}")
    
    return " ".join(replay_parts)


def _build_replay_text_with_recommendations(self, moment) -> str:
    """Build replay text that includes coaching recommendations."""
    replay_parts = []
    
    # Add the moment
    replay_parts.append(f"Here's a {moment.moment_type} moment from the sales call:")
    replay_parts.append(f"'{moment.transcript_segment}'")
    replay_parts.append("")
    
    # Add recommendations
    if moment.recommendations:
        replay_parts.append("Coaching recommendations:")
        for i, recommendation in enumerate(moment.recommendations, 1):
            replay_parts.append(f"{i}. {recommendation}")
        replay_parts.append("")
    
    # Add confidence and timing info
    replay_parts.append(f"This moment occurred at {moment.start_time:.1f} to {moment.end_time:.1f} seconds")
    replay_parts.append(f"Confidence level: {moment.confidence:.1%}")
    
    return " ".join(replay_parts)
