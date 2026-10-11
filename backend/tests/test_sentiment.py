import pytest
from app.services.sentiment import get_sentiment_provider


def test_vader_positive_sentiment():
    provider = get_sentiment_provider()
    res = provider.analyze("The new update is exceptionally smooth, fast and delightful!")
    assert res["label"] == "positive"
    assert res["score"] > 0.05


def test_vader_negative_sentiment():
    provider = get_sentiment_provider()
    res = provider.analyze("This is a complete scam, it crashed and stole my money! Terribly broken.")
    assert res["label"] == "negative"
    assert res["score"] < -0.05


def test_vader_neutral_sentiment():
    provider = get_sentiment_provider()
    res = provider.analyze("The order was placed at standard delivery time.")
    assert res["label"] in ("neutral", "positive")
