"""Service for detecting coachable moments in sales calls."""

import re
from typing import List, Dict, Optional
from loguru import logger

from config.settings import settings
from models.sales_call import CoachableMoment
from services.sentiment_service import sentiment_service


class CoachableMomentService:
    """Detects coachable moments in sales call transcripts."""
    
    def __init__(self):
        """Initialize coachable moment service."""
        self.threshold = settings.coachable_moment_threshold
        self.objection_keywords = settings.objection_keywords
        self.buying_signal_keywords = settings.buying_signal_keywords
        
        # Compile regex patterns for better performance
        self.objection_patterns = [re.compile(rf'\b{kw}\b', re.IGNORECASE) for kw in self.objection_keywords]
        self.buying_signal_patterns = [re.compile(rf'\b{kw}\b', re.IGNORECASE) for kw in self.buying_signal_keywords]
    
    def detect_coachable_moments(self, transcript_segments: List[Dict]) -> List[Dict]:
        """
        Detect coachable moments in transcript segments.
        
        Args:
            transcript_segments: List of transcript segments with timing
            
        Returns:
            List of detected coachable moments
        """
        try:
            logger.info(f"Detecting coachable moments in {len(transcript_segments)} transcript segments")
            
            coachable_moments = []
            
            for segment in transcript_segments:
                text = segment.get("text", "").lower()
                start_time = segment.get("start_time", 0.0)
                end_time = segment.get("end_time", 0.0)
                speaker_id = segment.get("speaker_id", "unknown")
                sentiment_score = segment.get("sentiment_score", 0.0)
                
                # Detect different types of coachable moments
                moments = self._analyze_segment(
                    text, start_time, end_time, speaker_id, sentiment_score
                )
                
                coachable_moments.extend(moments)
            
            # Sort moments by start time
            coachable_moments.sort(key=lambda x: x["start_time"])
            
            logger.info(f"Detected {len(coachable_moments)} coachable moments")
            return coachable_moments
            
        except Exception as e:
            logger.error(f"Error detecting coachable moments: {e}")
            return []
    
    def _analyze_segment(self, text: str, start_time: float, end_time: float, 
                         speaker_id: str, sentiment_score: float) -> List[Dict]:
        """
        Analyze a single transcript segment for coachable moments.
        
        Args:
            text: Text content of the segment
            start_time: Start time of the segment
            end_time: End time of the segment
            speaker_id: Speaker identifier
            sentiment_score: Sentiment score of the segment
            
        Returns:
            List of detected coachable moments in this segment
        """
        moments = []
        
        # Detect objections
        objection_moment = self._detect_objection(text, start_time, end_time, speaker_id, sentiment_score)
        if objection_moment:
            moments.append(objection_moment)
        
        # Detect buying signals
        buying_signal_moment = self._detect_buying_signal(text, start_time, end_time, speaker_id, sentiment_score)
        if buying_signal_moment:
            moments.append(buying_signal_moment)
        
        # Detect emotional moments
        emotional_moment = self._detect_emotional_moment(text, start_time, end_time, speaker_id, sentiment_score)
        if emotional_moment:
            moments.append(emotional_moment)
        
        # Detect question patterns
        question_moment = self._detect_question_patterns(text, start_time, end_time, speaker_id, sentiment_score)
        if question_moment:
            moments.append(question_moment)
        
        # Detect silence or hesitation
        silence_moment = self._detect_silence_hesitation(text, start_time, end_time, speaker_id, sentiment_score)
        if silence_moment:
            moments.append(silence_moment)
        
        return moments
    
    def _detect_objection(self, text: str, start_time: float, end_time: float, 
                          speaker_id: str, sentiment_score: float) -> Optional[Dict]:
        """Detect customer objections."""
        # Check for objection keywords
        objection_found = False
        matched_keywords = []
        
        for pattern in self.objection_patterns:
            if pattern.search(text):
                objection_found = True
                matched_keywords.append(pattern.pattern.replace(r'\b', '').replace(r'\B', ''))
        
        if objection_found:
            confidence = min(0.9, 0.6 + abs(sentiment_score) * 0.3)
            
            return {
                "moment_type": "objection",
                "confidence": confidence,
                "start_time": start_time,
                "end_time": end_time,
                "description": f"Customer objection detected: {', '.join(matched_keywords)}",
                "transcript_segment": text,
                "recommendations": [
                    "Acknowledge the customer's concern",
                    "Ask clarifying questions to understand the objection better",
                    "Provide specific examples or case studies",
                    "Address the root cause, not just the symptom"
                ],
                "speaker_id": speaker_id,
                "sentiment_score": sentiment_score
            }
        
        return None
    
    def _detect_buying_signal(self, text: str, start_time: float, end_time: float, 
                             speaker_id: str, sentiment_score: float) -> Optional[Dict]:
        """Detect buying signals from customer."""
        # Check for buying signal keywords
        buying_signal_found = False
        matched_keywords = []
        
        for pattern in self.buying_signal_patterns:
            if pattern.search(text):
                buying_signal_found = True
                matched_keywords.append(pattern.pattern.replace(r'\b', '').replace(r'\B', ''))
        
        if buying_signal_found:
            confidence = min(0.9, 0.7 + sentiment_score * 0.2)
            
            return {
                "moment_type": "buying_signal",
                "confidence": confidence,
                "start_time": start_time,
                "end_time": end_time,
                "description": f"Buying signal detected: {', '.join(matched_keywords)}",
                "transcript_segment": text,
                "recommendations": [
                    "Move quickly to close the deal",
                    "Ask for the sale directly",
                    "Address any remaining concerns",
                    "Provide next steps and timeline"
                ],
                "speaker_id": speaker_id,
                "sentiment_score": sentiment_score
            }
        
        return None
    
    def _detect_emotional_moment(self, text: str, start_time: float, end_time: float, 
                                speaker_id: str, sentiment_score: float) -> Optional[Dict]:
        """Detect emotionally charged moments."""
        # Check for strong emotional indicators
        emotional_indicators = [
            r'\b(very|extremely|really|so)\b',
            r'\b(love|hate|terrible|amazing|awful|fantastic)\b',
            r'\b(upset|angry|frustrated|excited|thrilled)\b',
            r'\b(never|always|everyone|nobody)\b'  # Absolute language
        ]
        
        emotional_score = 0
        for indicator in emotional_indicators:
            if re.search(indicator, text, re.IGNORECASE):
                emotional_score += 1
        
        # Check for exclamation marks
        emotional_score += text.count('!') * 0.5
        
        if emotional_score >= 2 or abs(sentiment_score) > 0.6:
            confidence = min(0.9, 0.5 + emotional_score * 0.2 + abs(sentiment_score) * 0.3)
            
            emotion_type = "positive" if sentiment_score > 0 else "negative"
            
            return {
                "moment_type": f"emotional_{emotion_type}",
                "confidence": confidence,
                "start_time": start_time,
                "end_time": end_time,
                "description": f"Strong {emotion_type} emotional moment detected",
                "transcript_segment": text,
                "recommendations": [
                    "Acknowledge the customer's emotions",
                    "Show empathy and understanding",
                    "Use this moment to build rapport",
                    "Channel positive emotions into buying decisions"
                ],
                "speaker_id": speaker_id,
                "sentiment_score": sentiment_score
            }
        
        return None
    
    def _detect_question_patterns(self, text: str, start_time: float, end_time: float, 
                                 speaker_id: str, sentiment_score: float) -> Optional[Dict]:
        """Detect important question patterns."""
        # Check for key question types
        question_patterns = [
            r'\b(how much|what does it cost|pricing)\b',
            r'\b(when can|timeline|deadline)\b',
            r'\b(what if|what happens if|guarantee)\b',
            r'\b(how does|how do you|process)\b'
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                confidence = 0.8
                
                return {
                    "moment_type": "information_request",
                    "confidence": confidence,
                    "start_time": start_time,
                    "end_time": end_time,
                    "description": "Customer requesting specific information",
                    "transcript_segment": text,
                    "recommendations": [
                        "Provide clear, specific answers",
                        "Use this opportunity to demonstrate expertise",
                        "Ask follow-up questions to understand needs better",
                        "Provide written documentation if possible"
                    ],
                    "speaker_id": speaker_id,
                    "sentiment_score": sentiment_score
                }
        
        return None
    
    def _detect_silence_hesitation(self, text: str, start_time: float, end_time: float, 
                                  speaker_id: str, sentiment_score: float) -> Optional[Dict]:
        """Detect moments of silence or hesitation."""
        # Check for hesitation indicators
        hesitation_indicators = [
            r'\b(um|uh|er|ah)\b',
            r'\b(well|you know|like|sort of|kind of)\b',
            r'\b(i think|maybe|probably|possibly)\b'
        ]
        
        hesitation_score = 0
        for indicator in hesitation_indicators:
            matches = re.findall(indicator, text, re.IGNORECASE)
            hesitation_score += len(matches)
        
        # Check for short responses (potential hesitation)
        if len(text.split()) <= 3 and hesitation_score > 0:
            confidence = 0.7
            
            return {
                "moment_type": "hesitation",
                "confidence": confidence,
                "start_time": start_time,
                "end_time": end_time,
                "description": "Customer showing signs of hesitation or uncertainty",
                "transcript_segment": text,
                "recommendations": [
                    "Ask open-ended questions to understand concerns",
                    "Provide reassurance and build confidence",
                    "Address any doubts or objections",
                    "Use social proof or testimonials"
                ],
                "speaker_id": speaker_id,
                "sentiment_score": sentiment_score
            }
        
        return None
    
    def create_coachable_moment_models(self, sales_call_id: int, 
                                     coachable_moments: List[Dict]) -> List[CoachableMoment]:
        """
        Create database models from detected coachable moments.
        
        Args:
            sales_call_id: ID of the sales call
            coachable_moments: List of detected coachable moments
            
        Returns:
            List of CoachableMoment database models
        """
        try:
            models = []
            
            for moment_data in coachable_moments:
                model = CoachableMoment(
                    sales_call_id=sales_call_id,
                    moment_type=moment_data["moment_type"],
                    confidence=moment_data["confidence"],
                    start_time=moment_data["start_time"],
                    end_time=moment_data["end_time"],
                    description=moment_data["description"],
                    transcript_segment=moment_data["transcript_segment"],
                    recommendations=moment_data.get("recommendations", [])
                )
                models.append(model)
            
            return models
            
        except Exception as e:
            logger.error(f"Error creating coachable moment models: {e}")
            raise


# Global coachable moment service instance
coachable_moment_service = CoachableMomentService()
