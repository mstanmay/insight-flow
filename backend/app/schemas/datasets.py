from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DatasetSummary(BaseModel):
    id: str
    name: str
    source_filename: str
    row_count: int
    valid_count: int
    rejected_count: int
    distinct_text_count: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetDetail(DatasetSummary):
    column_mapping: Dict[str, Any] = {}
    file_sha256: str
    latest_job_id: Optional[str] = None


class ImportSummaryResponse(BaseModel):
    import_id: str
    dataset_id: str
    status: str
    column_mapping: Dict[str, str]
    unmapped_columns: List[str]
    rows_total: int
    rows_valid: int
    rows_rejected: int
    distinct_texts: int
    duplicate_rows: int
    warnings: List[str] = []
    errors_preview: List[Dict[str, Any]] = []
    analysis_job_id: Optional[str] = None


class FeedbackCreateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    dataset_id: Optional[str] = None
    source: Optional[str] = None
    source_category: Optional[str] = None
    rating: Optional[float] = None
    product: Optional[str] = None
    language: Optional[str] = None
    created_at: Optional[datetime] = None


class FeedbackSentiment(BaseModel):
    label: str
    score: float
    provider: str


class FeedbackItemResponse(BaseModel):
    id: str
    dataset_id: str
    external_ref: Optional[str] = None
    text: str
    source_category: Optional[str] = None
    source: Optional[str] = None
    rating: Optional[float] = None
    created_at: Optional[datetime] = None
    received_at: datetime
    duplicate_count: int = 1
    sentiment: Optional[FeedbackSentiment] = None
    issue_key: Optional[str] = None
    issue_title: Optional[str] = None

    class Config:
        from_attributes = True
