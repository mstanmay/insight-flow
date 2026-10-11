from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from app.core.db import Base, generate_uuid, utc_now


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    source_filename = Column(String(255), nullable=False)
    file_sha256 = Column(String(64), nullable=False, unique=True, index=True)
    row_count = Column(Integer, default=0)
    valid_count = Column(Integer, default=0)
    rejected_count = Column(Integer, default=0)
    distinct_text_count = Column(Integer, default=0)
    column_mapping = Column(JSON, default=dict)
    status = Column(String(50), default="imported")  # imported, analyzing, ready, failed
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    feedback = relationship("Feedback", back_populates="dataset", cascade="all, delete-orphan")
    analysis_jobs = relationship("AnalysisJob", back_populates="dataset", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="dataset", cascade="all, delete-orphan")
    import_errors = relationship("ImportError", back_populates="dataset", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="dataset", cascade="all, delete-orphan")


class ImportError(Base):
    __tablename__ = "import_errors"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    error_reason = Column(String(500), nullable=False)
    raw_content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    dataset = relationship("Dataset", back_populates="import_errors")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    external_ref = Column(String(100), nullable=True)  # e.g. row-17 or external ticket ID
    original_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    duplicate_of_id = Column(String(36), ForeignKey("feedback.id"), nullable=True, index=True)
    
    # Metadata
    source = Column(String(100), nullable=True, index=True)  # Zendesk, Shopify, etc.
    source_category = Column(String(100), nullable=True, index=True)  # Category from CSV if given
    rating = Column(Float, nullable=True)
    product = Column(String(100), nullable=True)
    language = Column(String(10), nullable=True)
    extra = Column(JSON, default=dict)

    # Observed time vs ingestion time
    created_at = Column(DateTime, nullable=True, index=True)  # NULL if CSV has no date
    received_at = Column(DateTime, default=utc_now)

    # Relationships
    dataset = relationship("Dataset", back_populates="feedback")
    analysis = relationship("FeedbackAnalysis", back_populates="feedback", uselist=False, cascade="all, delete-orphan")
    issue_links = relationship("IssueFeedback", back_populates="feedback", cascade="all, delete-orphan")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="queued", index=True)  # queued, running, completed, completed_with_errors, failed
    stage = Column(String(50), default="init")
    processed_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    provider_ids = Column(JSON, default=dict)  # {"sentiment": "vader@3.3.2", "clustering": "tfidf+agglo"}
    pipeline_version = Column(String(20), default="1.0.0")
    config_hash = Column(String(64), nullable=False)
    idempotency_key = Column(String(128), unique=True, index=True)
    stage_logs = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    dataset = relationship("Dataset", back_populates="analysis_jobs")
    feedback_analyses = relationship("FeedbackAnalysis", back_populates="job", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="job", cascade="all, delete-orphan")


class FeedbackAnalysis(Base):
    __tablename__ = "feedback_analyses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    feedback_id = Column(String(36), ForeignKey("feedback.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    sentiment_label = Column(String(20), nullable=False, index=True)  # positive, neutral, negative
    sentiment_score = Column(Float, nullable=False)  # -1.0 to 1.0
    sentiment_provider = Column(String(50), nullable=False)
    keywords = Column(JSON, default=list)
    cluster_key = Column(String(50), nullable=True, index=True)
    predicted_category = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    feedback = relationship("Feedback", back_populates="analysis")
    job = relationship("AnalysisJob", back_populates="feedback_analyses")

    __table_args__ = (
        Index("ix_analysis_sentiment_cluster", "sentiment_label", "cluster_key"),
    )


class Issue(Base):
    __tablename__ = "issues"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("analysis_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    issue_key = Column(String(20), nullable=False, index=True)  # e.g. ISS-001
    title = Column(String(255), nullable=False)
    topic = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    kind = Column(String(20), default="issue")  # issue vs strength
    
    row_count = Column(Integer, default=0)
    distinct_count = Column(Integer, default=0)
    sentiment_distribution = Column(JSON, default=dict)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    trend = Column(JSON, default=dict)  # {"value": null, "availability": "unavailable", "reason": ...}
    
    priority_score = Column(Float, nullable=True, index=True)
    priority_breakdown = Column(JSON, default=dict)
    confidence = Column(String(20), default="low")  # high, medium, low
    
    status = Column(String(30), default="open", index=True)  # open, investigating, planned, resolved, dismissed
    owner = Column(String(100), nullable=True)
    action_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    dataset = relationship("Dataset", back_populates="issues")
    job = relationship("AnalysisJob", back_populates="issues")
    evidence_links = relationship("IssueFeedback", back_populates="issue", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="issue", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="issue", cascade="all, delete-orphan")


class IssueFeedback(Base):
    __tablename__ = "issue_feedback"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    issue_id = Column(String(36), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    feedback_id = Column(String(36), ForeignKey("feedback.id", ondelete="CASCADE"), nullable=False, index=True)
    is_representative = Column(Boolean, default=False)
    rank = Column(Integer, default=1)

    issue = relationship("Issue", back_populates="evidence_links")
    feedback = relationship("Feedback", back_populates="issue_links")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    issue_id = Column(String(36), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    problem_statement = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    supporting_feedback_ids = Column(JSON, default=list)
    expected_outcome = Column(Text, nullable=False)
    confidence_label = Column(String(20), default="medium")
    limitations = Column(JSON, default=list)
    
    generated_by = Column(String(50), default="template")  # template vs llm
    model = Column(String(50), nullable=True)
    prompt_version = Column(String(20), default="rec-v1")
    ai_generated = Column(Boolean, default=False)
    status = Column(String(30), default="proposed")  # proposed, accepted, dismissed, tracking
    created_at = Column(DateTime, default=utc_now)

    issue = relationship("Issue", back_populates="recommendations")
    tracked_actions = relationship("TrackedAction", back_populates="recommendation", cascade="all, delete-orphan")


class TrackedAction(Base):
    __tablename__ = "tracked_actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    recommendation_id = Column(String(36), ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(30), nullable=False)  # accept, dismiss, track
    owner = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    recommendation = relationship("Recommendation", back_populates="tracked_actions")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    issue_id = Column(String(36), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    previous_state = Column(JSON, default=dict)
    new_state = Column(JSON, default=dict)
    actor = Column(String(100), default="system")
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    issue = relationship("Issue", back_populates="audit_events")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    filters_applied = Column(JSON, default=dict)
    snapshot = Column(JSON, nullable=False)  # Frozen metrics, findings, issues, recs
    created_at = Column(DateTime, default=utc_now)

    dataset = relationship("Dataset", back_populates="reports")
