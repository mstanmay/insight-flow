"""
InsightFlow Database Seed Script
Imports the real customer feedback CSV and runs complete analysis pipeline.
"""
import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.db import SessionLocal
from app.models.entities import Dataset, Feedback, AnalysisJob
from app.services.ingestion import read_csv_stream
from app.services.analysis import run_dataset_analysis_pipeline

CSV_CANDIDATE_PATHS = [
    os.path.join("data", "BuildBattle_2026_Customer_Feedback_Dataset.csv"),
    r"C:\Users\M S Tanmay\Downloads\BuildBattle_2026_Customer_Feedback_Dataset.csv",
    "BuildBattle_2026_Customer_Feedback_Dataset.csv"
]


def seed():
    csv_path = None
    for p in CSV_CANDIDATE_PATHS:
        if os.path.exists(p):
            csv_path = p
            break

    if not csv_path:
        print("Dataset CSV not found. Skipping seed.")
        return

    print(f"Reading dataset from {csv_path}...")
    with open(csv_path, "rb") as f:
        content = f.read()

    headers, mapping, unmapped, valid_rows, rejected_rows, file_sha256 = read_csv_stream(content)
    print(f"Parsed {len(valid_rows)} valid feedback rows. Headers: {headers}")

    db = SessionLocal()
    try:
        from app.core.db import Base, engine
        Base.metadata.create_all(bind=engine)

        existing = db.query(Dataset).filter(Dataset.file_sha256 == file_sha256).first()
        if existing:
            print(f"Dataset already seeded (ID: {existing.id}).")
            return

        unique_hashes = set()
        distinct_count = 0
        for r in valid_rows:
            h = r["content_hash"]
            if h not in unique_hashes:
                unique_hashes.add(h)
                distinct_count += 1

        dataset = Dataset(
            name="BuildBattle 2026 Customer Feedback",
            source_filename=os.path.basename(csv_path),
            file_sha256=file_sha256,
            row_count=len(valid_rows),
            valid_count=len(valid_rows),
            rejected_count=len(rejected_rows),
            distinct_text_count=distinct_count,
            column_mapping=mapping,
            status="imported"
        )
        db.add(dataset)
        db.flush()

        seen_hash_to_id = {}
        # First pass: create canonical feedback items (distinct hashes)
        canonical_objects = []
        duplicate_rows = []
        for r in valid_rows:
            h = r["content_hash"]
            if h not in seen_hash_to_id:
                fb = Feedback(
                    dataset_id=dataset.id,
                    external_ref=r["external_ref"],
                    original_text=r["original_text"],
                    normalized_text=r["normalized_text"],
                    content_hash=h,
                    duplicate_of_id=None,
                    source_category=r["source_category"]
                )
                db.add(fb)
                canonical_objects.append((h, fb))
                seen_hash_to_id[h] = True
            else:
                duplicate_rows.append(r)

        db.flush()
        # Map actual IDs for canonicals
        hash_to_actual_id = {h: fb.id for h, fb in canonical_objects}

        # Second pass: insert duplicates in batches
        batch_size = 500
        for i in range(0, len(duplicate_rows), batch_size):
            batch = duplicate_rows[i:i + batch_size]
            for r in batch:
                h = r["content_hash"]
                fb = Feedback(
                    dataset_id=dataset.id,
                    external_ref=r["external_ref"],
                    original_text=r["original_text"],
                    normalized_text=r["normalized_text"],
                    content_hash=h,
                    duplicate_of_id=hash_to_actual_id.get(h),
                    source_category=r["source_category"]
                )
                db.add(fb)
            db.flush()

        db.commit()
        print(f"Seeded {len(valid_rows)} feedback entries ({distinct_count} distinct).")

        # Run analysis pipeline
        print("Running AI analysis pipeline...")
        job = AnalysisJob(
            dataset_id=dataset.id,
            status="queued",
            stage="init",
            config_hash="default_seed_v1",
            idempotency_key=f"{dataset.id}_seed"
        )
        db.add(job)
        db.commit()

        run_dataset_analysis_pipeline(db, job)
        print("Analysis completed successfully!")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
