"""Toxicity detection service using a pre-trained NLP model."""

import logging
from typing import Dict, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# Global model instance (lazy loaded)
_model = None
_model_loaded = False


class ToxicityAnalyzer:
    """
    Analyzes text for toxicity using the Detoxify model.
    
    The model provides scores for:
    - toxicity: General toxicity
    - severe_toxicity: Severe/extreme toxicity
    - obscene: Obscene language
    - threat: Threatening language
    - insult: Insulting language
    - identity_attack: Identity-based attacks
    """
    
    def __init__(self):
        self._model = None
        self._is_loaded = False
    
    def load_model(self) -> bool:
        """
        Load the toxicity detection model.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        if self._is_loaded:
            return True
        
        try:
            from detoxify import Detoxify
            
            logger.info("Loading toxicity detection model...")
            # Using 'original' model - good balance of speed and accuracy
            # Other options: 'unbiased', 'multilingual'
            self._model = Detoxify('original')
            self._is_loaded = True
            logger.info("Toxicity detection model loaded successfully")
            return True
            
        except ImportError:
            logger.error(
                "Detoxify package not installed. "
                "Install with: pip install detoxify"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to load toxicity model: {e}")
            return False
    
    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analyze text for toxicity.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with toxicity scores (0.0 to 1.0)
        """
        if not self._is_loaded:
            if not self.load_model():
                # Return default scores if model isn't available
                return self._get_default_scores()
        
        try:
            # Get predictions from the model
            results = self._model.predict(text)
            
            # Convert numpy floats to Python floats and round
            scores = {
                key: round(float(value), 4)
                for key, value in results.items()
            }
            
            # Add an overall toxicity flag
            scores['is_toxic'] = scores.get('toxicity', 0) > 0.5
            scores['toxicity_level'] = self._get_toxicity_level(
                scores.get('toxicity', 0)
            )
            
            return scores
            
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return self._get_default_scores()
    
    def _get_toxicity_level(self, score: float) -> str:
        """
        Convert toxicity score to human-readable level.
        
        Args:
            score: Toxicity score (0.0 to 1.0)
            
        Returns:
            Toxicity level string
        """
        if score < 0.2:
            return "safe"
        elif score < 0.4:
            return "mild"
        elif score < 0.6:
            return "moderate"
        elif score < 0.8:
            return "high"
        else:
            return "severe"
    
    def _get_default_scores(self) -> Dict[str, float]:
        """Return default scores when model is unavailable."""
        return {
            "toxicity": 0.0,
            "severe_toxicity": 0.0,
            "obscene": 0.0,
            "threat": 0.0,
            "insult": 0.0,
            "identity_attack": 0.0,
            "is_toxic": False,
            "toxicity_level": "unknown"
        }
    
    def is_available(self) -> bool:
        """Check if the toxicity analyzer is available."""
        return self._is_loaded


# Global singleton instance
toxicity_analyzer = ToxicityAnalyzer()
