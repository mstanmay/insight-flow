from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.db import get_db
from app.core.errors import AppError
from app.core.config import get_settings
from app.models.entities import Dataset, Feedback, AnalysisJob, ImportError
from app.schemas.datasets import (
    DatasetSummary,
    DatasetDetail,
    ImportSummaryResponse,
    FeedbackItemResponse,
    FeedbackCreateRequest,
)
from app.schemas.common import PaginatedResponse
from app.services.ingestion import read_csv_stream
from app.worker.runner import trigger_background_analysis

router = APIRouter(tags=["Datasets & Ingestion"])
settings = get_settings()


@router.post("/datasets/imports", response_model=ImportSummaryResponse, status_code=status.HTTP_201_CREATED)
async def import_dataset_csv(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    dry_run: bool = Form(False),
    force: bool = Form(False),
    auto_analyze: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    Import customer feedback CSV dataset.
    Validates file headers, normalizes text, deduplicates content, and enqueues analysis.
    """
    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise AppError(
            code="file_too_large",
            message=f"Uploaded file exceeds maximum limit of {settings.MAX_UPLOAD_MB}MB",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )

    try:
        headers, mapping, unmapped, valid_rows, rejected_rows, file_sha256 = read_csv_stream(content)
    except ValueError as e:
        raise AppError(code="invalid_csv", message=str(e), status_code=status.HTTP_400_BAD_REQUEST)

    # Check for duplicate file
    existing = db.query(Dataset).filter(Dataset.file_sha256 == file_sha256).first()
    if existing and not force and not dry_run:
        raise AppError(
            code="duplicate_dataset",
            message=f"Dataset with identical file hash already exists (ID: {existing.id})",
            status_code=status.HTTP_409_CONFLICT,
            details={"dataset_id": existing.id}
        )

    # Calculate duplicate content stats
    unique_hashes = set()
    distinct_count = 0
    duplicate_rows = 0
    for r in valid_rows:
        h = r["content_hash"]
        if h not in unique_hashes:
            unique_hashes.add(h)
            distinct_count += 1
        else:
            duplicate_rows += 1

    warnings = []
    if "created_at" not in mapping:
        warnings.append("No timestamp column detected: longitudinal trend and recency scoring will be marked as unavailable.")

    if dry_run:
        return ImportSummaryResponse(
            import_id="dry-run",
            dataset_id="dry-run",
            status="preview",
            column_mapping=mapping,
            unmapped_columns=unmapped,
            rows_total=len(valid_rows) + len(rejected_rows),
            rows_valid=len(valid_rows),
            rows_rejected=len(rejected_rows),
            distinct_texts=distinct_count,
            duplicate_rows=duplicate_rows,
            warnings=warnings,
            errors_preview=rejected_rows[:10]
        )

    # Persist dataset
    dataset_name = name or file.filename or "Customer Feedback Dataset"
    dataset = Dataset(
        name=dataset_name,
        source_filename=file.filename or "uploaded.csv",
        file_sha256=file_sha256,
        row_count=len(valid_rows) + len(rejected_rows),
        valid_count=len(valid_rows),
        rejected_count=len(rejected_rows),
        distinct_text_count=distinct_count,
        column_mapping=mapping,
        status="imported"
    )
    db.add(dataset)
    db.flush()

    # Store rejected rows
    for rej in rejected_rows:
        err = ImportError(
            dataset_id=dataset.id,
            row_number=rej["row_number"],
            error_reason=rej["reason"],
            raw_content=rej.get("raw")
        )
        db.add(err)

    # Deduplication map across batch
    seen_hash_to_id = {}
    feedback_objects = []

    for r in valid_rows:
        h = r["content_hash"]
        canonical_id = seen_hash_to_id.get(h)
        
        fb = Feedback(
            dataset_id=dataset.id,
            external_ref=r["external_ref"],
            original_text=r["original_text"],
            normalized_text=r["normalized_text"],
            content_hash=h,
            duplicate_of_id=canonical_id,
            source=r["source"],
            source_category=r["source_category"],
            rating=r["rating"],
            product=r["product"],
            language=r["language"],
            created_at=r["created_at"],
            extra=r["extra"]
        )
        db.add(fb)
        db.flush()

        if canonical_id is None:
            seen_hash_to_id[h] = fb.id

    db.commit()

    # Auto trigger background analysis
    analysis_job_id = None
    if auto_analyze and len(valid_rows) > 0:
        job = AnalysisJob(
            dataset_id=dataset.id,
            status="queued",
            stage="init",
            config_hash="default_v1",
            idempotency_key=f"{dataset.id}_job_1"
        )
        db.add(job)
        db.commit()
        analysis_job_id = job.id
        trigger_background_analysis(job.id)

    return ImportSummaryResponse(
        import_id=dataset.id,
        dataset_id=dataset.id,
        status="imported",
        column_mapping=mapping,
        unmapped_columns=unmapped,
        rows_total=dataset.row_count,
        rows_valid=dataset.valid_count,
        rows_rejected=dataset.rejected_count,
        distinct_texts=distinct_count,
        duplicate_rows=duplicate_rows,
        warnings=warnings,
        errors_preview=rejected_rows[:10],
        analysis_job_id=analysis_job_id
    )


@router.get("/datasets", response_model=PaginatedResponse[DatasetSummary])
def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db)
):
    total = db.query(Dataset).count()
    items = (
        db.query(Dataset)
        .order_by(desc(Dataset.created_at))
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


@router.get("/datasets/{dataset_id}", response_model=DatasetDetail)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise AppError(code="not_found", message=f"Dataset {dataset_id} not found", status_code=404)
    
    latest_job = (
        db.query(AnalysisJob)
        .filter(AnalysisJob.dataset_id == dataset_id)
        .order_by(desc(AnalysisJob.created_at))
        .first()
    )
    res = DatasetDetail.model_validate(dataset)
    res.latest_job_id = latest_job.id if latest_job else None
    return res


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: str, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise AppError(code="not_found", message=f"Dataset {dataset_id} not found", status_code=404)
    db.delete(dataset)
    db.commit()
    return None
