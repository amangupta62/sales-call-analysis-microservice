"""Background tasks for sales call analysis processing."""

import time
from typing import Dict, List, Any
from loguru import logger

from workers.celery_app import celery_app
from models.database import get_db_context
from models.sales_call import SalesCall, CoachableMoment, ExecutiveSummary
from services.coachable_moment_service import coachable_moment_service
from services.executive_summary_service import executive_summary_service
from services.sentiment_service import sentiment_service


@celery_app.task(bind=True, name="analyze_coachable_moments")
def analyze_coachable_moments_task(self, sales_call_id: int):
    """
    Background task for analyzing coachable moments in existing transcripts.
    
    Args:
        sales_call_id: ID of the sales call to analyze
        
    Returns:
        Dictionary containing analysis results
    """
    start_time = time.time()
    task_id = self.request.id
    
    try:
        logger.info(f"Starting coachable moments analysis task {task_id} for sales call {sales_call_id}")
        
        with get_db_context() as db:
            # Get sales call and transcript
            sales_call = db.query(SalesCall).filter(SalesCall.id == sales_call_id).first()
            if not sales_call:
                raise ValueError(f"Sales call {sales_call_id} not found")
            
            # Get transcript segments (assuming they exist)
            transcript = sales_call.transcript
            if not transcript:
                raise ValueError(f"Transcript not found for sales call {sales_call_id}")
            
            # Convert transcript segments to analysis format
            segments = []
            for utterance in transcript.utterances:
                segment = {
                    "text": utterance.text,
                    "start_time": utterance.start_time,
                    "end_time": utterance.end_time,
                    "speaker_id": utterance.speaker_id,
                    "sentiment_score": utterance.sentiment_score or 0.0
                }
                segments.append(segment)
            
            # Detect coachable moments
            coachable_moments = coachable_moment_service.detect_coachable_moments(segments)
            
            # Remove existing coachable moments
            db.query(CoachableMoment).filter(CoachableMoment.sales_call_id == sales_call_id).delete()
            
            # Create new coachable moments
            coachable_moment_models = coachable_moment_service.create_coachable_moment_models(
                sales_call_id, coachable_moments
            )
            for moment in coachable_moment_models:
                db.add(moment)
            
            db.commit()
            
            processing_time = time.time() - start_time
            logger.info(f"Coachable moments analysis task {task_id} completed in {processing_time:.2f}s")
            
            return {
                "status": "success",
                "sales_call_id": sales_call_id,
                "coachable_moments_count": len(coachable_moments),
                "processing_time": processing_time,
                "task_id": task_id
            }
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Coachable moments analysis task {task_id} failed after {processing_time:.2f}s: {e}")
        raise


@celery_app.task(bind=True, name="regenerate_executive_summary")
def regenerate_executive_summary_task(self, sales_call_id: int):
    """
    Background task for regenerating executive summary.
    
    Args:
        sales_call_id: ID of the sales call
        
    Returns:
        Dictionary containing task results
    """
    start_time = time.time()
    task_id = self.request.id
    
    try:
        logger.info(f"Starting executive summary regeneration task {task_id} for sales call {sales_call_id}")
        
        with get_db_context() as db:
            # Get sales call and related data
            sales_call = db.query(SalesCall).filter(SalesCall.id == sales_call_id).first()
            if not sales_call:
                raise ValueError(f"Sales call {sales_call_id} not found")
            
            transcript = sales_call.transcript
            if not transcript:
                raise ValueError(f"Transcript not found for sales call {sales_call_id}")
            
            # Get coachable moments
            coachable_moments = db.query(CoachableMoment).filter(
                CoachableMoment.sales_call_id == sales_call_id
            ).all()
            
            # Convert to analysis format
            moments_data = []
            for moment in coachable_moments:
                moment_data = {
                    "moment_type": moment.moment_type,
                    "confidence": moment.confidence,
                    "start_time": moment.start_time,
                    "end_time": moment.end_time,
                    "description": moment.description,
                    "transcript_segment": moment.transcript_segment,
                    "recommendations": moment.recommendations
                }
                moments_data.append(moment_data)
            
            # Prepare transcript data
            transcript_data = {
                "full_transcript": transcript.full_transcript,
                "segments": transcript.segments or [],
                "sentiment_scores": transcript.sentiment_scores or {},
                "duration": sales_call.duration_seconds or 0.0
            }
            
            # Generate new executive summary
            new_summary = executive_summary_service.generate_executive_summary(
                transcript_data,
                moments_data,
                transcript.sentiment_scores or {}
            )
            
            # Remove existing executive summary
            db.query(ExecutiveSummary).filter(ExecutiveSummary.sales_call_id == sales_call_id).delete()
            
            # Create new executive summary
            summary_model = executive_summary_service.create_executive_summary_model(
                sales_call_id, new_summary
            )
            db.add(summary_model)
            
            db.commit()
            
            processing_time = time.time() - start_time
            logger.info(f"Executive summary regeneration task {task_id} completed in {processing_time:.2f}s")
            
            return {
                "status": "success",
                "sales_call_id": sales_call_id,
                "summary_id": summary_model.id,
                "processing_time": processing_time,
                "task_id": task_id
            }
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Executive summary regeneration task {task_id} failed after {processing_time:.2f}s: {e}")
        raise


@celery_app.task(bind=True, name="batch_sentiment_analysis")
def batch_sentiment_analysis_task(self, sales_call_ids: List[int]):
    """
    Background task for batch sentiment analysis of multiple sales calls.
    
    Args:
        sales_call_ids: List of sales call IDs to analyze
        
    Returns:
        Dictionary containing batch analysis results
    """
    start_time = time.time()
    task_id = self.request.id
    
    try:
        logger.info(f"Starting batch sentiment analysis task {task_id} for {len(sales_call_ids)} sales calls")
        
        results = {
            "total_processed": 0,
            "successful": 0,
            "failed": 0,
            "errors": []
        }
        
        with get_db_context() as db:
            for sales_call_id in sales_call_ids:
                try:
                    # Get sales call
                    sales_call = db.query(SalesCall).filter(SalesCall.id == sales_call_id).first()
                    if not sales_call:
                        results["errors"].append(f"Sales call {sales_call_id} not found")
                        results["failed"] += 1
                        continue
                    
                    # Get transcript
                    transcript = sales_call.transcript
                    if not transcript:
                        results["errors"].append(f"Transcript not found for sales call {sales_call_id}")
                        results["failed"] += 1
                        continue
                    
                    # Analyze sentiment for each utterance
                    for utterance in transcript.utterances:
                        if utterance.text and utterance.text.strip():
                            sentiment_result = sentiment_service.analyze_sentiment(utterance.text)
                            utterance.sentiment_score = sentiment_result["score"]
                            utterance.sentiment_label = sentiment_result["label"]
                    
                    # Update transcript sentiment scores
                    if transcript.utterances:
                        sentiment_scores = sentiment_service.get_sentiment_summary([
                            {
                                "label": u.sentiment_label,
                                "score": u.sentiment_score
                            }
                            for u in transcript.utterances
                        ])
                        transcript.sentiment_scores = sentiment_scores
                    
                    results["successful"] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing sales call {sales_call_id}: {str(e)}"
                    results["errors"].append(error_msg)
                    results["failed"] += 1
                    logger.error(error_msg)
                
                results["total_processed"] += 1
            
            db.commit()
        
        processing_time = time.time() - start_time
        logger.info(f"Batch sentiment analysis task {task_id} completed in {processing_time:.2f}s")
        
        results["processing_time"] = processing_time
        results["task_id"] = task_id
        
        return results
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Batch sentiment analysis task {task_id} failed after {processing_time:.2f}s: {e}")
        raise


@celery_app.task(bind=True, name="generate_call_insights")
def generate_call_insights_task(self, sales_call_id: int):
    """
    Background task for generating comprehensive call insights.
    
    Args:
        sales_call_id: ID of the sales call
        
    Returns:
        Dictionary containing insights
    """
    start_time = time.time()
    task_id = self.request.id
    
    try:
        logger.info(f"Starting call insights generation task {task_id} for sales call {sales_call_id}")
        
        with get_db_context() as db:
            # Get sales call and related data
            sales_call = db.query(SalesCall).filter(SalesCall.id == sales_call_id).first()
            if not sales_call:
                raise ValueError(f"Sales call {sales_call_id} not found")
            
            transcript = sales_call.transcript
            coachable_moments = sales_call.coachable_moments
            executive_summary = sales_call.executive_summary
            
            # Generate insights
            insights = {
                "call_metrics": {
                    "duration": sales_call.duration_seconds,
                    "utterance_count": len(transcript.utterances) if transcript else 0,
                    "coachable_moments_count": len(coachable_moments),
                    "has_executive_summary": executive_summary is not None
                },
                "speaker_analysis": {},
                "topic_analysis": {},
                "sentiment_trends": {},
                "recommendations": []
            }
            
            if transcript and transcript.utterances:
                # Speaker analysis
                speaker_stats = {}
                for utterance in transcript.utterances:
                    speaker = utterance.speaker_id
                    if speaker not in speaker_stats:
                        speaker_stats[speaker] = {
                            "utterance_count": 0,
                            "total_words": 0,
                            "avg_sentiment": 0.0,
                            "sentiment_counts": {"positive": 0, "negative": 0, "neutral": 0}
                        }
                    
                    speaker_stats[speaker]["utterance_count"] += 1
                    speaker_stats[speaker]["total_words"] += len(utterance.text.split())
                    
                    if utterance.sentiment_label:
                        speaker_stats[speaker]["sentiment_counts"][utterance.sentiment_label] += 1
                    
                    if utterance.sentiment_score:
                        speaker_stats[speaker]["avg_sentiment"] += utterance.sentiment_score
                
                # Calculate averages
                for speaker in speaker_stats:
                    count = speaker_stats[speaker]["utterance_count"]
                    if count > 0:
                        speaker_stats[speaker]["avg_sentiment"] /= count
                        speaker_stats[speaker]["avg_words_per_utterance"] = speaker_stats[speaker]["total_words"] / count
                
                insights["speaker_analysis"] = speaker_stats
            
            # Add recommendations based on analysis
            if insights["call_metrics"]["coachable_moments_count"] > 5:
                insights["recommendations"].append("High number of coachable moments - consider additional training")
            
            if insights["call_metrics"]["duration"] and insights["call_metrics"]["duration"] < 30:
                insights["recommendations"].append("Short call duration - may need more engagement strategies")
            
            processing_time = time.time() - start_time
            logger.info(f"Call insights generation task {task_id} completed in {processing_time:.2f}s")
            
            return {
                "status": "success",
                "sales_call_id": sales_call_id,
                "insights": insights,
                "processing_time": processing_time,
                "task_id": task_id
            }
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Call insights generation task {task_id} failed after {processing_time:.2f}s: {e}")
        raise
