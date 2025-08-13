"""Service for generating executive summaries of sales calls."""

import re
from typing import Dict, List, Optional
from loguru import logger

from models.sales_call import ExecutiveSummary
from services.sentiment_service import sentiment_service


class ExecutiveSummaryService:
    """Generates executive summaries of sales calls."""
    
    def __init__(self):
        """Initialize executive summary service."""
        self.summary_templates = {
            "success": "Sales call completed successfully with clear buying signals and positive customer engagement.",
            "follow_up": "Sales call shows potential but requires follow-up to address concerns and move toward closure.",
            "lost": "Sales call indicates customer is not currently interested, requiring re-engagement strategy."
        }
    
    def generate_executive_summary(self, transcript_data: Dict, 
                                 coachable_moments: List[Dict],
                                 sentiment_scores: Dict) -> Dict:
        """
        Generate executive summary from call analysis.
        
        Args:
            transcript_data: Transcript and analysis data
            coachable_moments: Detected coachable moments
            sentiment_scores: Overall sentiment analysis
            
        Returns:
            Dictionary containing executive summary
        """
        try:
            logger.info("Generating executive summary")
            
            # Analyze call content and structure
            call_analysis = self._analyze_call_content(transcript_data, coachable_moments)
            
            # Determine call outcome
            call_outcome = self._determine_call_outcome(call_analysis, sentiment_scores)
            
            # Generate key points
            key_points = self._extract_key_points(transcript_data, coachable_moments)
            
            # Generate action items
            action_items = self._generate_action_items(call_analysis, call_outcome)
            
            # Generate summary text
            summary_text = self._generate_summary_text(
                call_analysis, call_outcome, key_points, sentiment_scores
            )
            
            # Determine overall sentiment overview
            sentiment_overview = self._get_sentiment_overview(sentiment_scores)
            
            return {
                "summary": summary_text,
                "key_points": key_points,
                "action_items": action_items,
                "sentiment_overview": sentiment_overview,
                "call_outcome": call_outcome,
                "call_analysis": call_analysis
            }
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            raise
    
    def _analyze_call_content(self, transcript_data: Dict, coachable_moments: List[Dict]) -> Dict:
        """
        Analyze call content for patterns and insights.
        
        Args:
            transcript_data: Transcript and analysis data
            coachable_moments: Detected coachable moments
            
        Returns:
            Dictionary containing call analysis
        """
        analysis = {
            "total_duration": transcript_data.get("duration", 0.0),
            "total_segments": len(transcript_data.get("segments", [])),
            "speaker_distribution": {},
            "topic_areas": [],
            "objection_count": 0,
            "buying_signal_count": 0,
            "question_count": 0,
            "emotional_moments": 0
        }
        
        # Analyze speaker distribution
        segments = transcript_data.get("segments", [])
        for segment in segments:
            speaker = segment.get("speaker_id", "unknown")
            analysis["speaker_distribution"][speaker] = analysis["speaker_distribution"].get(speaker, 0) + 1
        
        # Analyze coachable moments
        for moment in coachable_moments:
            moment_type = moment.get("moment_type", "")
            if "objection" in moment_type:
                analysis["objection_count"] += 1
            elif "buying_signal" in moment_type:
                analysis["buying_signal_count"] += 1
            elif "question" in moment_type:
                analysis["question_count"] += 1
            elif "emotional" in moment_type:
                analysis["emotional_moments"] += 1
        
        # Identify topic areas
        analysis["topic_areas"] = self._identify_topic_areas(transcript_data.get("full_transcript", ""))
        
        return analysis
    
    def _identify_topic_areas(self, transcript: str) -> List[str]:
        """
        Identify main topic areas discussed in the call.
        
        Args:
            transcript: Full transcript text
            
        Returns:
            List of identified topic areas
        """
        topic_keywords = {
            "pricing": ["price", "cost", "budget", "investment", "value", "roi"],
            "features": ["feature", "functionality", "capability", "benefit", "advantage"],
            "timeline": ["timeline", "deadline", "schedule", "when", "timing"],
            "competition": ["competitor", "alternative", "compare", "vs", "versus"],
            "implementation": ["implementation", "setup", "onboarding", "training", "support"],
            "objections": ["concern", "worry", "issue", "problem", "challenge"]
        }
        
        identified_topics = []
        transcript_lower = transcript.lower()
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in transcript_lower for keyword in keywords):
                identified_topics.append(topic)
        
        return identified_topics
    
    def _determine_call_outcome(self, call_analysis: Dict, sentiment_scores: Dict) -> str:
        """
        Determine the overall outcome of the sales call.
        
        Args:
            call_analysis: Analysis of call content
            sentiment_scores: Overall sentiment scores
            
        Returns:
            Call outcome classification
        """
        # Scoring system for call outcome
        score = 0
        
        # Positive factors
        score += call_analysis["buying_signal_count"] * 2
        score += sentiment_scores.get("positive", 0) * 0.5
        
        # Negative factors
        score -= call_analysis["objection_count"] * 1.5
        score -= sentiment_scores.get("negative", 0) * 0.5
        
        # Neutral factors
        score += call_analysis["question_count"] * 0.5
        
        # Determine outcome based on score
        if score >= 3:
            return "success"
        elif score >= 0:
            return "follow_up"
        else:
            return "lost"
    
    def _extract_key_points(self, transcript_data: Dict, coachable_moments: List[Dict]) -> List[str]:
        """
        Extract key points from the call.
        
        Args:
            transcript_data: Transcript and analysis data
            coachable_moments: Detected coachable moments
            
        Returns:
            List of key points
        """
        key_points = []
        
        # Add duration and structure info
        duration = transcript_data.get("duration", 0.0)
        if duration > 0:
            key_points.append(f"Call duration: {duration:.1f} seconds")
        
        # Add coachable moment insights
        if coachable_moments:
            key_points.append(f"Identified {len(coachable_moments)} coachable moments")
            
            # Group by type
            moment_types = {}
            for moment in coachable_moments:
                moment_type = moment.get("moment_type", "unknown")
                moment_types[moment_type] = moment_types.get(moment_type, 0) + 1
            
            for moment_type, count in moment_types.items():
                key_points.append(f"{count} {moment_type.replace('_', ' ')} moments")
        
        # Add sentiment insights
        sentiment_scores = transcript_data.get("sentiment_scores", {})
        if sentiment_scores:
            overall_label = sentiment_scores.get("overall_label", "neutral")
            key_points.append(f"Overall sentiment: {overall_label}")
        
        return key_points
    
    def _generate_action_items(self, call_analysis: Dict, call_outcome: str) -> List[str]:
        """
        Generate action items based on call analysis.
        
        Args:
            call_analysis: Analysis of call content
            call_outcome: Determined call outcome
            
        Returns:
            List of action items
        """
        action_items = []
        
        if call_outcome == "success":
            action_items.extend([
                "Prepare contract and closing documents",
                "Schedule follow-up implementation meeting",
                "Send welcome package and onboarding materials"
            ])
        elif call_outcome == "follow_up":
            action_items.extend([
                "Address identified objections in follow-up",
                "Provide additional information requested",
                "Schedule follow-up call within 48 hours"
            ])
        else:  # lost
            action_items.extend([
                "Add to re-engagement campaign",
                "Analyze objections for product improvement",
                "Schedule follow-up in 30 days"
            ])
        
        # Add specific action items based on coachable moments
        if call_analysis["objection_count"] > 0:
            action_items.append("Develop objection handling strategies")
        
        if call_analysis["question_count"] > 0:
            action_items.append("Prepare detailed responses to questions asked")
        
        return action_items
    
    def _generate_summary_text(self, call_analysis: Dict, call_outcome: str, 
                              key_points: List[str], sentiment_scores: Dict) -> str:
        """
        Generate comprehensive summary text.
        
        Args:
            call_analysis: Analysis of call content
            call_outcome: Determined call outcome
            key_points: Extracted key points
            sentiment_scores: Overall sentiment scores
            
        Returns:
            Generated summary text
        """
        summary_parts = []
        
        # Opening statement
        summary_parts.append(f"This {call_analysis['total_duration']:.1f}-second sales call")
        
        # Outcome statement
        if call_outcome == "success":
            summary_parts.append("resulted in a successful outcome with clear buying signals.")
        elif call_outcome == "follow_up":
            summary_parts.append("shows potential but requires follow-up to move toward closure.")
        else:
            summary_parts.append("indicates the customer is not currently interested.")
        
        # Key metrics
        summary_parts.append(f"The call included {call_analysis['total_segments']} conversation segments")
        summary_parts.append(f"with {call_analysis['objection_count']} objections and {call_analysis['buying_signal_count']} buying signals identified.")
        
        # Sentiment overview
        if sentiment_scores:
            overall_label = sentiment_scores.get("overall_label", "neutral")
            summary_parts.append(f"Overall customer sentiment was {overall_label}.")
        
        # Topic areas
        if call_analysis["topic_areas"]:
            topics_text = ", ".join(call_analysis["topic_areas"])
            summary_parts.append(f"Key topics discussed included: {topics_text}.")
        
        # Recommendations
        if call_outcome == "success":
            summary_parts.append("Immediate next steps should focus on closing the deal and onboarding.")
        elif call_outcome == "follow_up":
            summary_parts.append("Focus follow-up efforts on addressing objections and providing requested information.")
        else:
            summary_parts.append("Consider re-engagement strategies and product improvements based on feedback.")
        
        return " ".join(summary_parts)
    
    def _get_sentiment_overview(self, sentiment_scores: Dict) -> str:
        """
        Get sentiment overview description.
        
        Args:
            sentiment_scores: Overall sentiment scores
            
        Returns:
            Sentiment overview description
        """
        if not sentiment_scores:
            return "neutral"
        
        overall_label = sentiment_scores.get("overall_label", "neutral")
        positive_count = sentiment_scores.get("positive", 0)
        negative_count = sentiment_scores.get("negative", 0)
        neutral_count = sentiment_scores.get("neutral", 0)
        
        if overall_label == "positive" and positive_count > negative_count * 2:
            return "strongly positive"
        elif overall_label == "negative" and negative_count > positive_count * 2:
            return "strongly negative"
        elif abs(positive_count - negative_count) <= 1:
            return "mixed"
        else:
            return overall_label
    
    def create_executive_summary_model(self, sales_call_id: int, 
                                     summary_data: Dict) -> ExecutiveSummary:
        """
        Create database model from executive summary data.
        
        Args:
            sales_call_id: ID of the sales call
            summary_data: Generated summary data
            
        Returns:
            ExecutiveSummary database model
        """
        try:
            model = ExecutiveSummary(
                sales_call_id=sales_call_id,
                summary=summary_data["summary"],
                key_points=summary_data["key_points"],
                action_items=summary_data["action_items"],
                sentiment_overview=summary_data["sentiment_overview"],
                call_outcome=summary_data["call_outcome"]
            )
            
            return model
            
        except Exception as e:
            logger.error(f"Error creating executive summary model: {e}")
            raise


# Global executive summary service instance
executive_summary_service = ExecutiveSummaryService()
