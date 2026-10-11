import threading
from typing import Optional
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.entities import AnalysisJob
from app.services.analysis import run_dataset_analysis_pipeline


def trigger_background_analysis(job_id: str) -> None:
    """Run analysis pipeline in an isolated background thread."""
    def worker():
        db: Session = SessionLocal()
        try:
            job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
            if job and job.status == "queued":
                run_dataset_analysis_pipeline(db, job)
        except Exception as e:
            pass
        finally:
            db.close()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
