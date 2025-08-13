"""Sentiment analysis service using HuggingFace transformers."""

from typing import Dict, List
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from loguru import logger
import torch

from config.settings import settings


class SentimentService:
    """Handles sentiment analysis using pre-trained models."""
    
    def __init__(self):
        """Initialize sentiment analysis service."""
        self.model_name = settings.sentiment_model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipeline = None
        
        # Load sentiment analysis pipeline
        self._load_pipeline()
    
    def _load_pipeline(self):
        """Load sentiment analysis pipeline."""
        try:
            logger.info(f"Loading sentiment analysis model: {self.model_name}")
            logger.info(f"Using device: {self.device}")
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            # Create pipeline
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            
            logger.info("Sentiment analysis model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading sentiment analysis model: {e}")
            # Fallback to default pipeline
            try:
                self.pipeline = pipeline("sentiment-analysis", device=-1)
                logger.info("Loaded fallback sentiment analysis model")
            except Exception as fallback_error:
                logger.error(f"Failed to load fallback model: {fallback_error}")
                raise
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        try:
            if not text or not text.strip():
                return {"label": "neutral", "score": 0.0, "confidence": 0.0}
            
            # Analyze sentiment
            result = self.pipeline(text[:512])  # Limit text length for model input
            
            # Extract results
            label = result[0]["label"].lower()
            score = result[0]["score"]
            
            # Normalize label to our standard format
            normalized_label = self._normalize_label(label)
            
            # Convert score to sentiment score (-1 to 1)
            sentiment_score = self._convert_score(label, score)
            
            return {
                "label": normalized_label,
                "score": sentiment_score,
                "confidence": score,
                "original_label": label
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"label": "neutral", "score": 0.0, "confidence": 0.0}
    
    def analyze_batch_sentiment(self, texts: List[str]) -> List[Dict]:
        """
        Analyze sentiment of multiple texts in batch.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of sentiment analysis results
        """
        try:
            if not texts:
                return []
            
            # Filter out empty texts
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            
            if not valid_texts:
                return []
            
            # Analyze sentiment in batch
            results = self.pipeline(valid_texts)
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                label = result["label"].lower()
                score = result["score"]
                
                normalized_label = self._normalize_label(label)
                sentiment_score = self._convert_score(label, score)
                
                processed_results.append({
                    "text": valid_texts[i],
                    "label": normalized_label,
                    "score": sentiment_score,
                    "confidence": score,
                    "original_label": label
                })
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Error analyzing batch sentiment: {e}")
            return []
    
    def _normalize_label(self, label: str) -> str:
        """
        Normalize sentiment label to standard format.
        
        Args:
            label: Raw sentiment label
            
        Returns:
            Normalized sentiment label
        """
        label = label.lower()
        
        # Map common labels to our standard format
        positive_labels = ["positive", "pos", "good", "great", "excellent", "happy"]
        negative_labels = ["negative", "neg", "bad", "terrible", "awful", "sad"]
        
        if any(pos_label in label for pos_label in positive_labels):
            return "positive"
        elif any(neg_label in label for neg_label in negative_labels):
            return "negative"
        else:
            return "neutral"
    
    def _convert_score(self, label: str, confidence: float) -> float:
        """
        Convert confidence score to sentiment score (-1 to 1).
        
        Args:
            label: Sentiment label
            confidence: Confidence score
            
        Returns:
            Sentiment score between -1 and 1
        """
        normalized_label = self._normalize_label(label)
        
        if normalized_label == "positive":
            return confidence
        elif normalized_label == "negative":
            return -confidence
        else:
            return 0.0
    
    def get_sentiment_summary(self, sentiment_results: List[Dict]) -> Dict:
        """
        Generate summary statistics from sentiment analysis results.
        
        Args:
            sentiment_results: List of sentiment analysis results
            
        Returns:
            Dictionary containing sentiment summary
        """
        if not sentiment_results:
            return {
                "total": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0,
                "average_score": 0.0
            }
        
        total = len(sentiment_results)
        positive = sum(1 for r in sentiment_results if r["label"] == "positive")
        negative = sum(1 for r in sentiment_results if r["label"] == "negative")
        neutral = sum(1 for r in sentiment_results if r["label"] == "neutral")
        
        total_score = sum(r["score"] for r in sentiment_results)
        average_score = total_score / total if total > 0 else 0.0
        
        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "average_score": average_score,
            "positive_percentage": (positive / total) * 100 if total > 0 else 0.0,
            "negative_percentage": (negative / total) * 100 if total > 0 else 0.0,
            "neutral_percentage": (neutral / total) * 100 if total > 0 else 0.0
        }


# Global sentiment service instance
sentiment_service = SentimentService()
