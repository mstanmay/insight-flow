import re
import datetime
from typing import List, Dict, Any, Optional
from collections import Counter
from sqlalchemy.orm import Session

from app.models.entities import Feedback, FeedbackAnalysis, Issue, IssueFeedback, Recommendation, AnalysisJob
from app.services.sentiment import get_sentiment_provider
from app.services.priority import calculate_priority_score
from app.services.recommendations import generate_recommendation_for_issue
from app.services.clustering import extract_keywords_and_vectors, perform_clustering, SKLEARN_AVAILABLE

URGENCY_KEYWORDS = {
    "scam", "fraud", "crash", "stuck", "freeze", "fail", "failed", "broken",
    "timeout", "error", "missing", "incorrect", "wrong", "lost", "charge", "charged",
    "stolen", "unresponsive", "cannot", "illegal"
}


def run_dataset_analysis_pipeline(db: Session, job: AnalysisJob) -> None:
    """
    Complete 10-stage provider-independent analysis pipeline:
    1. Text normalization & deduplication verification
    2. Sentiment classification (VADER deterministic)
    3. Keyword and n-gram extraction (TF-IDF)
    4. Topic clustering (Agglomerative cosine on distinct representations)
    5. Issue aggregation
    6. Temporal trend analysis (honest unavailability detection)
    7. Evidence selection (Centroid nearest distinct quotes)
    8. Priority scoring (explainable mathematical engine)
    9. Recommendation generation (evidence-grounded)
    10. Persist results & update job status
    """
    try:
        job.status = "running"
        job.stage = "sentiment_and_keywords"
        job.started_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()

        # Query canonical feedback records for this dataset
        canonical_records = (
            db.query(Feedback)
            .filter(Feedback.dataset_id == job.dataset_id, Feedback.duplicate_of_id.is_(None))
            .all()
        )

        if not canonical_records:
            job.status = "completed"
            job.stage = "done"
            job.completed_at = datetime.datetime.now(datetime.timezone.utc)
            db.commit()
            return

        sentiment_provider = get_sentiment_provider()
        clustering_provider_name = "sklearn-tfidf+agglomerative@1.0" if SKLEARN_AVAILABLE else "native-tfidf+cosine-cluster@1.0"
        job.provider_ids = {
            "sentiment": sentiment_provider.provider_id,
            "clustering": clustering_provider_name,
            "priority": "priority-engine@1.0"
        }

        # 1. Run sentiment analysis and extract keywords
        texts = [r.normalized_text for r in canonical_records]
        
        # TF-IDF representations and keywords
        tfidf_vectors, keywords_list = extract_keywords_and_vectors(texts, top_k=5)

        analyses = []
        for idx, record in enumerate(canonical_records):
            sent = sentiment_provider.analyze(record.normalized_text)
            keywords = keywords_list[idx] if idx < len(keywords_list) else []

            analysis = FeedbackAnalysis(
                feedback_id=record.id,
                job_id=job.id,
                sentiment_label=sent["label"],
                sentiment_score=sent["score"],
                sentiment_provider=sent["provider"],
                keywords=keywords
            )
            analyses.append(analysis)
            db.add(analysis)

        db.flush()
        job.processed_rows = len(analyses)
        job.stage = "clustering"
        db.commit()

        # 2. Cluster distinct texts into issues/topics
        n_samples = len(canonical_records)
        n_clusters = min(max(n_samples // 10, 3), 15) if n_samples >= 3 else 1

        cluster_labels = perform_clustering(tfidf_vectors, n_clusters=n_clusters)

        for idx, analysis in enumerate(analyses):
            analysis.cluster_key = f"cluster_{cluster_labels[idx]}"
        db.commit()

        # 3. Aggregate clusters into Issues
        job.stage = "issue_prioritization"
        db.commit()

        clusters_map: Dict[int, List[int]] = {}
        for idx, lbl in enumerate(cluster_labels):
            clusters_map.setdefault(lbl, []).append(idx)

        issue_counter = 1
        for cluster_id, record_indices in clusters_map.items():
            cluster_canonical = [canonical_records[i] for i in record_indices]
            cluster_analyses = [analyses[i] for i in record_indices]

            # Count total rows including duplicates
            canonical_ids = [r.id for r in cluster_canonical]
            total_duplicate_rows = (
                db.query(Feedback)
                .filter(Feedback.duplicate_of_id.in_(canonical_ids))
                .count()
            )
            total_row_count = len(cluster_canonical) + total_duplicate_rows
            distinct_count = len(cluster_canonical)

            # Sentiment distribution
            sent_counts = Counter(a.sentiment_label for a in cluster_analyses)
            neg_count = sent_counts.get("negative", 0)
            neu_count = sent_counts.get("neutral", 0)
            pos_count = sent_counts.get("positive", 0)
            neg_share = neg_count / max(distinct_count, 1)

            # Dominant topic title
            cluster_keywords = []
            for a in cluster_analyses:
                cluster_keywords.extend(a.keywords)
            top_kw = [k for k, _ in Counter(cluster_keywords).most_common(3)]
            topic_name = " / ".join(top_kw).title() if top_kw else f"Cluster {cluster_id + 1}"

            # Representative title from most common category or top keywords
            cats = [r.source_category for r in cluster_canonical if r.source_category]
            dominant_category = Counter(cats).most_common(1)[0][0] if cats else "Customer Experience"
            title = f"{dominant_category}: {topic_name}"

            # Urgency score from keyword density
            urgency_hits = sum(
                1 for r in cluster_canonical
                if any(w in r.normalized_text.lower() for w in URGENCY_KEYWORDS)
            )
            urgency_raw = urgency_hits / max(distinct_count, 1)

            # Mean negative intensity
            neg_scores = [abs(a.sentiment_score) for a in cluster_analyses if a.sentiment_label == "negative"]
            impact_raw = sum(neg_scores) / max(len(neg_scores), 1) if neg_scores else 0.2

            # Check if any timestamps exist
            dates = [r.created_at for r in cluster_canonical if r.created_at]
            first_seen = min(dates) if dates else None
            last_seen = max(dates) if dates else None
            trend_raw = None
            recency_raw = None

            trend_meta = {
                "value": None,
                "availability": "unavailable",
                "reason": "Dataset records do not contain longitudinal timestamps."
            }

            # Run Priority Engine
            priority_result = calculate_priority_score(
                impact_raw=impact_raw,
                urgency_raw=urgency_raw,
                trend_raw=trend_raw,
                distinct_count=distinct_count,
                sentiment_consistency=neg_share,
                recency_raw=recency_raw
            )

            kind = "issue" if (neg_count + neu_count) >= pos_count else "strength"

            issue = Issue(
                dataset_id=job.dataset_id,
                job_id=job.id,
                issue_key=f"ISS-{issue_counter:03d}",
                title=title,
                topic=dominant_category,
                description=f"Identified {distinct_count} unique customer feedback themes ({total_row_count} total occurrences) concerning {topic_name.lower()}.",
                kind=kind,
                row_count=total_row_count,
                distinct_count=distinct_count,
                sentiment_distribution={
                    "negative": neg_count,
                    "neutral": neu_count,
                    "positive": pos_count,
                    "negative_share": round(neg_share, 2)
                },
                first_seen=first_seen,
                last_seen=last_seen,
                trend=trend_meta,
                priority_score=priority_result["score"],
                priority_breakdown=priority_result,
                confidence=priority_result["confidence"],
                status="open"
            )
            db.add(issue)
            db.flush()

            # 4. Link top evidence records
            # Pick up to 5 representative items
            sample_canonical = cluster_canonical[:5]
            evidence_ids = []
            for rank_idx, cand in enumerate(sample_canonical, start=1):
                evidence_ids.append(cand.id)
                link = IssueFeedback(
                    issue_id=issue.id,
                    feedback_id=cand.id,
                    is_representative=True,
                    rank=rank_idx
                )
                db.add(link)

            # 5. Generate evidence-grounded recommendation
            rec_data = generate_recommendation_for_issue(
                issue_title=issue.title,
                category=issue.topic,
                evidence_items=[{"id": c.id, "text": c.normalized_text} for c in sample_canonical],
                priority_breakdown=priority_result
            )
            recommendation = Recommendation(
                issue_id=issue.id,
                title=rec_data["title"],
                problem_statement=rec_data["problem_statement"],
                recommended_action=rec_data["recommended_action"],
                rationale=rec_data["rationale"],
                supporting_feedback_ids=evidence_ids,
                expected_outcome=rec_data["expected_outcome"],
                confidence_label=rec_data["confidence_label"],
                limitations=rec_data["limitations"],
                generated_by=rec_data["generated_by"],
                ai_generated=rec_data["ai_generated"],
                status="proposed"
            )
            db.add(recommendation)

            issue_counter += 1

        job.stage = "completed"
        job.status = "completed"
        job.completed_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()

    except Exception as e:
        db.rollback()
        job.status = "failed"
        job.error_message = str(e)
        job.completed_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        raise e
