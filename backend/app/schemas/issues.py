from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class PriorityComponentExplanation(BaseModel):
    name: str
    value: Optional[float]
    weight: float
    effective_weight: float
    available: bool
    explanation: str


class PriorityBreakdown(BaseModel):
    score: Optional[float]
    confidence: str  # high, medium, low
    label: str = "decision-support score (not a probability of churn or loss)"
    components: List[PriorityComponentExplanation]
    limitations: List[str]


class IssueEvidenceItem(BaseModel):
    feedback_id: str
    text: str
    duplicate_count: int = 1
    rank: int = 1
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[float] = None


class RecommendationResponse(BaseModel):
    id: str
    issue_id: str
    title: str
    problem_statement: str
    recommended_action: str
    rationale: str
    supporting_feedback_ids: List[str]
    expected_outcome: str
    confidence_label: str
    limitations: List[str]
    generated_by: str
    ai_generated: bool
    model: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class IssueItemResponse(BaseModel):
    id: str
    issue_key: str
    title: str
    topic: str
    description: str
    kind: str
    row_count: int
    distinct_count: int
    sentiment_distribution: Dict[str, Any]
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    trend: Dict[str, Any]
    priority_score: Optional[float] = None
    priority_breakdown: Optional[PriorityBreakdown] = None
    confidence: str
    status: str
    owner: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class IssueDetailResponse(IssueItemResponse):
    evidence: List[IssueEvidenceItem] = []
    recommendations: List[RecommendationResponse] = []
    action_notes: Optional[str] = None


class IssueStatusUpdateRequest(BaseModel):
    status: Optional[str] = None
    owner: Optional[str] = None
    note: Optional[str] = None


class RecommendationActionRequest(BaseModel):
    action: str = Field(..., pattern="^(accept|dismiss|track)$")
    owner: Optional[str] = None
    note: Optional[str] = None
