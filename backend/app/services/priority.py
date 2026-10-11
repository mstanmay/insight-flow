import math
from typing import Dict, Any, List, Optional
from app.core.config import get_settings


def calculate_priority_score(
    impact_raw: float,             # 0.0 - 1.0 (mean negative intensity + category severity)
    urgency_raw: float,            # 0.0 - 1.0 (urgency keyword marker density & criticality)
    trend_raw: Optional[float],    # 0.0 - 1.0, or None if timestamps missing
    distinct_count: int,           # number of unique text records
    sentiment_consistency: float,  # 0.0 - 1.0 share of negative sentiment
    recency_raw: Optional[float],  # 0.0 - 1.0, or None if timestamps missing
    custom_weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Deterministic explainable priority scoring formula:
    Priority = 100 * (sum(w_i * c_i) / sum(w_i of available components))
    
    Minimum sample safeguards:
    - If distinct_count < 5, evidence strength capped at 0.30
    - If temporal data (trend or recency) is absent, excluded and remaining normalized
    """
    settings = get_settings()
    weights = custom_weights or {
        "impact": settings.PRIORITY_WEIGHT_IMPACT,
        "urgency": settings.PRIORITY_WEIGHT_URGENCY,
        "trend": settings.PRIORITY_WEIGHT_TREND,
        "evidence": settings.PRIORITY_WEIGHT_EVIDENCE,
        "recency": settings.PRIORITY_WEIGHT_RECENCY,
    }

    # 1. Evidence strength calculation with safeguards
    evidence_base = (1.0 - math.exp(-max(distinct_count, 0) / 8.0)) * min(max(sentiment_consistency, 0.0), 1.0)
    if distinct_count < 5:
        evidence_strength = min(evidence_base, 0.30)
        evidence_expl = f"Capped at {evidence_strength:.2f} due to low distinct feedback sample size ({distinct_count} unique items)."
    else:
        evidence_strength = min(max(evidence_base, 0.0), 1.0)
        evidence_expl = f"Computed from {distinct_count} unique items with {sentiment_consistency*100:.0f}% sentiment consistency."

    components = []
    available_weights_sum = 0.0
    weighted_value_sum = 0.0
    limitations = []
    missing_count = 0

    # Evaluate each component
    # Impact
    impact_val = min(max(impact_raw, 0.0), 1.0)
    components.append({
        "name": "impact",
        "value": round(impact_val, 4),
        "weight": weights["impact"],
        "effective_weight": 0.0,
        "available": True,
        "explanation": f"Negative intensity & severity impact index: {impact_val:.2f} (0-1 range)."
    })

    # Urgency
    urgency_val = min(max(urgency_raw, 0.0), 1.0)
    components.append({
        "name": "urgency",
        "value": round(urgency_val, 4),
        "weight": weights["urgency"],
        "effective_weight": 0.0,
        "available": True,
        "explanation": f"Critical blocker and scam/fraud/failure marker concentration: {urgency_val:.2f}."
    })

    # Trend
    if trend_raw is not None:
        trend_val = min(max(trend_raw, 0.0), 1.0)
        components.append({
            "name": "trend",
            "value": round(trend_val, 4),
            "weight": weights["trend"],
            "effective_weight": 0.0,
            "available": True,
            "explanation": f"Normalized complaint growth over comparison period: {trend_val:.2f}."
        })
    else:
        missing_count += 1
        limitations.append("Trend analysis unavailable: dataset records do not contain valid comparison timestamp windows.")
        components.append({
            "name": "trend",
            "value": None,
            "weight": weights["trend"],
            "effective_weight": 0.0,
            "available": False,
            "explanation": "Unavailable: dataset lacks timestamps for longitudinal velocity analysis."
        })

    # Evidence Strength
    components.append({
        "name": "evidence",
        "value": round(evidence_strength, 4),
        "weight": weights["evidence"],
        "effective_weight": 0.0,
        "available": True,
        "explanation": evidence_expl
    })

    # Recency
    if recency_raw is not None:
        recency_val = min(max(recency_raw, 0.0), 1.0)
        components.append({
            "name": "recency",
            "value": round(recency_val, 4),
            "weight": weights["recency"],
            "effective_weight": 0.0,
            "available": True,
            "explanation": f"Exponential decay recency factor: {recency_val:.2f}."
        })
    else:
        missing_count += 1
        limitations.append("Recency analysis unavailable: timestamps are not present in the ingested dataset.")
        components.append({
            "name": "recency",
            "value": None,
            "weight": weights["recency"],
            "effective_weight": 0.0,
            "available": False,
            "explanation": "Unavailable: dataset records do not have ingestion/creation timestamps."
        })

    # Calculate effective weights
    for comp in components:
        if comp["available"]:
            available_weights_sum += comp["weight"]

    if available_weights_sum > 0:
        for comp in components:
            if comp["available"]:
                comp["effective_weight"] = round(comp["weight"] / available_weights_sum, 4)
                weighted_value_sum += comp["effective_weight"] * comp["value"]

    score = round(100.0 * weighted_value_sum, 1)

    # Determine confidence level
    if missing_count >= 2:
        confidence = "low"
    elif missing_count == 1:
        confidence = "medium"
    else:
        confidence = "high"

    if distinct_count < 5:
        limitations.append(f"Low distinct evidence volume: only {distinct_count} unique complaints observed.")
        confidence = "low"

    return {
        "score": score,
        "confidence": confidence,
        "label": "decision-support score (not a probability of churn or loss)",
        "components": components,
        "limitations": limitations
    }
