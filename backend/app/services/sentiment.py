from abc import ABC, abstractmethod
from typing import Dict, Any, List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class BaseSentimentProvider(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str:
        pass

    @abstractmethod
    def analyze(self, text: str) -> Dict[str, Any]:
        """Returns {'label': 'positive'|'neutral'|'negative', 'score': float, 'provider': str}"""
        pass


class VaderSentimentProvider(BaseSentimentProvider):
    def __init__(self):
        self._analyzer = SentimentIntensityAnalyzer()

    @property
    def provider_id(self) -> str:
        return "vader@3.3.2"

    def analyze(self, text: str) -> Dict[str, Any]:
        scores = self._analyzer.polarity_scores(text)
        compound = scores.get("compound", 0.0)

        if compound >= 0.05:
            label = "positive"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        return {
            "label": label,
            "score": round(compound, 4),
            "provider": self.provider_id,
            "raw": scores
        }


class LexiconFallbackProvider(BaseSentimentProvider):
    """Deterministic fallback lexicon if VADER is ever unavailable."""
    def __init__(self):
        self._positive_words = {"great", "excellent", "love", "good", "fast", "helpful", "outstanding", "smooth"}
        self._negative_words = {"terrible", "bad", "scam", "fraud", "crash", "bug", "broken", "missing", "delay", "freeze"}

    @property
    def provider_id(self) -> str:
        return "lexicon-fallback@1.0"

    def analyze(self, text: str) -> Dict[str, Any]:
        words = set(text.lower().split())
        pos_hits = len(words.intersection(self._positive_words))
        neg_hits = len(words.intersection(self._negative_words))

        if neg_hits > pos_hits:
            label = "negative"
            score = -0.5
        elif pos_hits > neg_hits:
            label = "positive"
            score = 0.5
        else:
            label = "neutral"
            score = 0.0

        return {
            "label": label,
            "score": score,
            "provider": self.provider_id
        }


def get_sentiment_provider() -> BaseSentimentProvider:
    try:
        return VaderSentimentProvider()
    except Exception:
        return LexiconFallbackProvider()
