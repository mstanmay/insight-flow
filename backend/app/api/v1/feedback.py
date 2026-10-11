from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.core.db import get_db
from app.core.errors import AppError
from app.models.entities import Feedback, FeedbackAnalysis, Issue, Dataset
from app.schemas.datasets import FeedbackItemResponse, FeedbackCreateRequest
from app.schemas.common import PaginatedResponse
from app.services.ingestion import compute_content_hash, normalize_text
from app.services.sentiment import get_sentiment_provider

router = APIRouter(tags=["Feedback Management"])


@router.post("/feedback", response_model=FeedbackItemResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(payload: FeedbackCreateRequest, db: Session = Depends(get_db)):
    """Submit individual customer feedback record."""
    norm_text = normalize_text(payload.text)
    content_hash = compute_content_hash(norm_text)

    # Assign dataset or default
    dataset_id = payload.dataset_id
    if not dataset_id:
        default_ds = db.query(Dataset).filter(Dataset.name == "Manual Submissions").first()
        if not default_ds:
            default_ds = Dataset(
                name="Manual Submissions",
                source_filename="manual",
                file_sha256="manual_submissions_dataset"
            )
            db.add(default_ds)
            db.flush()
        dataset_id = default_ds.id

    # Check duplicate
    canonical = db.query(Feedback).filter(Feedback.content_hash == content_hash).first()
    duplicate_of_id = canonical.id if canonical else None

    fb = Feedback(
        dataset_id=dataset_id,
        original_text=payload.text,
        normalized_text=norm_text,
        content_hash=content_hash,
        duplicate_of_id=duplicate_of_id,
        source=payload.source or "Manual",
        source_category=payload.source_category,
        rating=payload.rating,
        product=payload.product,
        language=payload.language,
        created_at=payload.created_at
    )
    db.add(fb)
    db.flush()

    # Synchronous sentiment analysis for single manual submissions
    sentiment_prov = get_sentiment_provider()
    sent_res = sentiment_prov.analyze(norm_text)
    analysis = FeedbackAnalysis(
        feedback_id=fb.id,
        job_id="manual_job",
        sentiment_label=sent_res["label"],
        sentiment_score=sent_res["score"],
        sentiment_provider=sent_res["provider"]
    )
    db.add(analysis)
    db.commit()

    return FeedbackItemResponse(
        id=fb.id,
        dataset_id=fb.dataset_id,
        external_ref=fb.external_ref,
        text=fb.normalized_text,
        source_category=fb.source_category,
        source=fb.source,
        rating=fb.rating,
        created_at=fb.created_at,
        received_at=fb.received_at,
        duplicate_count=1,
        sentiment={
            "label": sent_res["label"],
            "score": sent_res["score"],
            "provider": sent_res["provider"]
        }
    )


@router.get("/feedback", response_model=PaginatedResponse[FeedbackItemResponse])
def list_feedback(
    dataset_id: Optional[str] = None,
    q: Optional[str] = None,
    sentiment: Optional[str] = None,  # positive, neutral, negative
    category: Optional[str] = None,
    source: Optional[str] = None,
    include_duplicates: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(Feedback)

    if dataset_id:
        query = query.filter(Feedback.dataset_id == dataset_id)
    if not include_duplicates:
        query = query.filter(Feedback.duplicate_of_id.is_(None))
    if category and category != "ALL":
        query = query.filter(Feedback.source_category == category)
    if source and source != "ALL":
        query = query.filter(Feedback.source == source)
    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Feedback.normalized_text.ilike(search_term),
                Feedback.external_ref.ilike(search_term),
                Feedback.source_category.ilike(search_term)
            )
        )

    if sentiment and sentiment != "ALL":
        query = query.join(FeedbackAnalysis).filter(FeedbackAnalysis.sentiment_label == sentiment.lower())

    total = query.count()
    records = (
        query.order_by(desc(Feedback.received_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for r in records:
        analysis = r.analysis
        sent_dict = None
        if analysis:
            sent_dict = {
                "label": analysis.sentiment_label,
                "score": analysis.sentiment_score,
                "provider": analysis.sentiment_provider
            }

        # Calculate duplicate count
        dupe_count = 1 + db.query(Feedback).filter(Feedback.duplicate_of_id == r.id).count()

        items.append(
            FeedbackItemResponse(
                id=r.id,
                dataset_id=r.dataset_id,
                external_ref=r.external_ref,
                text=r.original_text,
                source_category=r.source_category,
                source=r.source,
                rating=r.rating,
                created_at=r.created_at,
                received_at=r.received_at,
                duplicate_count=dupe_count,
                sentiment=sent_dict
            )
        )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages
    )
