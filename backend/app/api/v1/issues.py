from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.db import get_db
from app.core.errors import AppError
from app.models.entities import Issue, IssueFeedback, Feedback, Recommendation, AuditEvent
from app.schemas.issues import (
    IssueItemResponse,
    IssueDetailResponse,
    IssueEvidenceItem,
    IssueStatusUpdateRequest,
    RecommendationResponse,
    RecommendationActionRequest,
)
from app.schemas.common import PaginatedResponse

router = APIRouter(tags=["Issue Intelligence & Tracking"])

VALID_TRANSITIONS = {
    "open": ["investigating", "planned", "dismissed"],
    "investigating": ["planned", "resolved", "dismissed", "open"],
    "planned": ["resolved", "investigating", "dismissed"],
    "resolved": ["open"],
    "dismissed": ["open"]
}


@router.get("/issues", response_model=PaginatedResponse[IssueItemResponse])
def list_issues(
    dataset_id: Optional[str] = None,
    kind: Optional[str] = None,  # issue vs strength
    category: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Issue)
    if dataset_id:
        query = query.filter(Issue.dataset_id == dataset_id)
    if kind:
        query = query.filter(Issue.kind == kind)
    if category and category != "ALL":
        query = query.filter(Issue.topic == category)
    if status_filter and status_filter != "ALL":
        query = query.filter(Issue.status == status_filter)

    total = query.count()
    items = (
        query.order_by(desc(Issue.priority_score))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages
    )


@router.get("/issues/{issue_id}", response_model=IssueDetailResponse)
def get_issue(issue_id: str, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        # Check by human-friendly key (e.g. ISS-001)
        issue = db.query(Issue).filter(Issue.issue_key == issue_id).first()
    if not issue:
        raise AppError(code="not_found", message=f"Issue {issue_id} not found", status_code=404)

    # Gather evidence items
    evidence_links = (
        db.query(IssueFeedback)
        .filter(IssueFeedback.issue_id == issue.id)
        .order_by(IssueFeedback.rank)
        .all()
    )

    evidence_items = []
    for link in evidence_links:
        fb = link.feedback
        dupe_count = 1 + db.query(Feedback).filter(Feedback.duplicate_of_id == fb.id).count()
        sent = fb.analysis
        evidence_items.append(IssueEvidenceItem(
            feedback_id=fb.id,
            text=fb.original_text,
            duplicate_count=dupe_count,
            rank=link.rank,
            sentiment_label=sent.sentiment_label if sent else None,
            sentiment_score=sent.sentiment_score if sent else None
        ))

    recs = [RecommendationResponse.model_validate(r) for r in issue.recommendations]

    res = IssueDetailResponse.model_validate(issue)
    res.evidence = evidence_items
    res.recommendations = recs
    res.action_notes = issue.action_notes
    return res


@router.patch("/issues/{issue_id}", response_model=IssueItemResponse)
def update_issue_status(
    issue_id: str,
    payload: IssueStatusUpdateRequest,
    db: Session = Depends(get_db)
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        issue = db.query(Issue).filter(Issue.issue_key == issue_id).first()
    if not issue:
        raise AppError(code="not_found", message=f"Issue {issue_id} not found", status_code=404)

    # Validate state transition
    if payload.status and payload.status != issue.status:
        allowed = VALID_TRANSITIONS.get(issue.status, [])
        if payload.status not in allowed:
            raise AppError(
                code="invalid_transition",
                message=f"Cannot move issue from '{issue.status}' to '{payload.status}'",
                status_code=409,
                details={"allowed_transitions": allowed}
            )

        audit = AuditEvent(
            issue_id=issue.id,
            action="status_change",
            previous_state={"status": issue.status},
            new_state={"status": payload.status},
            actor="operator",
            note=payload.note
        )
        db.add(audit)
        issue.status = payload.status

    if payload.owner is not None:
        issue.owner = payload.owner
    if payload.note is not None:
        issue.action_notes = payload.note

    db.commit()
    db.refresh(issue)
    return issue
