import pytest
from app.services.priority import calculate_priority_score


def test_priority_score_full_signals():
    """Verify standard priority calculation with available signals."""
    result = calculate_priority_score(
        impact_raw=0.75,
        urgency_raw=0.8,
        trend_raw=0.5,
        distinct_count=15,
        sentiment_consistency=0.9,
        recency_raw=0.7
    )
    assert 0.0 <= result["score"] <= 100.0
    assert result["confidence"] == "high"
    assert len(result["components"]) == 5
    assert all(c["available"] for c in result["components"])


def test_priority_score_sparse_data_honest_weight_rebalancing():
    """Verify that when temporal and recency signals are unavailable (as in our CSV),
    the engine honestly marks them unavailable and normalizes over available weights.
    """
    result = calculate_priority_score(
        impact_raw=0.8,
        urgency_raw=0.9,
        trend_raw=None,
        distinct_count=12,
        sentiment_consistency=0.85,
        recency_raw=None
    )
    assert 0.0 <= result["score"] <= 100.0
    unavail = [c["name"] for c in result["components"] if not c["available"]]
    assert "trend" in unavail
    assert "recency" in unavail
    assert result["confidence"] in ("medium", "low")


def test_priority_score_low_sample_guard():
    """Verify that distinct_count < 5 caps evidence strength for honesty."""
    result = calculate_priority_score(
        impact_raw=0.5,
        urgency_raw=0.2,
        trend_raw=None,
        distinct_count=2,
        sentiment_consistency=1.0,
        recency_raw=None
    )
    assert 0.0 <= result["score"] <= 100.0
    ev = next(s for s in result["components"] if s["name"] == "evidence")
    assert ev["value"] <= 0.30
    assert result["confidence"] == "low"
