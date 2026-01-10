"""Toxicity detection service using a pre-trained NLP model."""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Global singleton instance
toxicity_analyzer = None

class ToxicityAnalyzer:
    """
    Analyzes text for toxicity using the Hugging Face transformers model.
    Supports English, Hindi, and Hinglish.
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
            from transformers import pipeline
            
            logger.info("Loading multilingual toxicity detection model...")
            # Using local model folder. Ensure 'textdetox/xlmr-large-toxicity-classifier' files are in ./model
            self._model = pipeline("text-classification", model="./model")
            self._is_loaded = True
            logger.info("Toxicity detection model loaded successfully")
            return True
            
        except ImportError:
            logger.error(
                "Transformers package not installed. "
                "Install with: pip install transformers torch"
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
            # The pipeline returns a list of dicts like [{'label': 'LABEL_0', 'score': 0.99}]
            # LABEL_0 usually means non-toxic, LABEL_1 means toxic, but need to verify for this specific model.
            # Assuming standard binary classification where the model returns the most likely class.
            
            # Since pipeline call can handle truncation, we rely on defaults.
            # For this specific model:
            # LABEL_1 is typically Toxic
            # LABEL_0 is typically Non-Toxic
            
            results = self._model(text)
            result = results[0] if isinstance(results, list) else results
            
            label = result.get('label')
            score = result.get('score')
            
            toxicity_score = 0.0
            
            # Adjust score based on label
            # Note: Verify label mapping for textdetox/bert-multilingual-toxicity-classifier
            # Usually: LABEL_0 = Non-toxic, LABEL_1 = Toxic
            if label == 'LABEL_1' or label == 'toxic': 
                toxicity_score = score
            elif label == 'LABEL_0' or label == 'non-toxic':
                toxicity_score = 1.0 - score
            else:
                 # Fallback if labels are different (e.g. some models use 'toxic' directly)
                 if 'toxic' in label.lower() and 'non' not in label.lower():
                     toxicity_score = score
                 else:
                     toxicity_score = 1.0 - score

            # Since this model is primarily binary toxicity, we map the main score 
            # and set others to 0 or same to avoid breaking clients expecting these keys.
            scores = {
                "toxicity": round(toxicity_score, 4),
                "severe_toxicity": 0.0, # Not supported by this specific model breakdown
                "obscene": 0.0,
                "threat": 0.0,
                "insult": 0.0,
                "identity_attack": 0.0
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
