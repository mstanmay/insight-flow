# InsightFlow — REST API Contract (v1)

Status: **Proposed (Phase 1)**. The FastAPI-generated OpenAPI spec (`/api/v1/openapi.json`, UI at `/docs`) becomes the source of truth once implemented; this document defines intent and frontend mapping.

Base URL: `{API_BASE_URL}/api/v1` · JSON UTF-8 · IDs are UUID strings · timestamps ISO-8601 UTC.

> **Note:** Numeric values in the JSON examples below are illustrative shapes only, not analysis results. Row/distinct counts quoted for the supplied CSV (7,000 / 320 / 6,680) are real profile figures.

---

## 1. Conventions

### Pagination (all list endpoints)
Query: `page` (≥1, default 1), `page_size` (1–200, default 25), `sort` (field, prefix `-` for desc).

```json
{ "items": [], "page": 1, "page_size": 25, "total": 320, "total_pages": 13 }
```

### Error envelope (all non-2xx)
```json
{ "error": { "code": "invalid_transition", "message": "Cannot move issue from 'resolved' to 'planned'.",
             "details": {"allowed": ["open"]}, "request_id": "8c1e…" } }
```

| HTTP | `code` examples |
|---|---|
| 400 | `invalid_csv`, `unmapped_text_column`, `empty_file` |
| 404 | `not_found` |
| 409 | `duplicate_dataset`, `job_already_running`, `invalid_transition` |
| 413 | `file_too_large`, `too_many_rows` |
| 422 | `validation_error` (Pydantic details) |
| 429 | `rate_limited` |
| 502/504 | `provider_error`, `provider_timeout` (only on endpoints that call providers synchronously) |
| 500 | `internal_error` (no stack trace) |

### Data availability metadata
Any metric that may be missing carries:
```json
{ "value": null, "availability": "unavailable", "reason": "Dataset has no timestamp column." }
```

---

## 2. Endpoints

### Health
| Method | Path | Response |
|---|---|---|
| GET | `/health` | `{status:"ok", version, pipeline_version}` (process alive) |
| GET | `/ready` | `{status:"ready"|"not_ready", checks:{database, migrations, worker}}` (503 if not ready) |

### Datasets & imports
| Method | Path | Notes |
|---|---|---|
| POST | `/datasets/imports` | multipart: `file`, optional `name`, `column_mapping` (JSON), `dry_run` (bool), `force` (bool), `auto_analyze` (bool, default true). `dry_run=true` → 200 preview, nothing stored. Otherwise 201 `ImportSummary`. Same file hash → 409 `duplicate_dataset` with existing id unless `force`. |
| GET | `/datasets` | paginated `DatasetSummary[]` |
| GET | `/datasets/{dataset_id}` | `DatasetDetail` (counts, mapping, latest job) |
| DELETE | `/datasets/{dataset_id}` | 204; cascades derived data |
| GET | `/imports/{import_id}` | `ImportSummary` (import_id == dataset_id in MVP; kept for contract stability) |
| GET | `/imports/{import_id}/errors.csv` | rejected rows: `row_number,reason,raw_text` (formula-escaped) |
| GET | `/jobs/{job_id}` | `AnalysisJob` |

`ImportSummary`
```json
{ "import_id": "…", "dataset_id": "…", "status": "imported",
  "column_mapping": {"review": "text", "category": "category"},
  "unmapped_columns": [], "rows_total": 7000, "rows_valid": 7000, "rows_rejected": 0,
  "distinct_texts": 320, "duplicate_rows": 6680,
  "warnings": ["No timestamp column: trend and recency analysis will be unavailable."],
  "errors_preview": [], "analysis_job_id": "…" }
```

`AnalysisJob`
```json
{ "job_id": "…", "dataset_id": "…", "status": "running", "stage": "clustering",
  "stages": [{"name": "sentiment", "status": "completed", "processed": 320, "failed": 0, "ms": 410}],
  "processed_rows": 320, "failed_rows": 0, "providers": {"sentiment": "vader@3.3.2", "llm": "template"},
  "pipeline_version": "1.0.0", "error_category": null, "started_at": "…", "completed_at": null }
```

### Feedback
| Method | Path | Notes |
|---|---|---|
| POST | `/feedback` | `{text, dataset_id?, source?, category?, rating?, created_at?}` → 201. Goes into a "Manual submissions" dataset if `dataset_id` omitted; analysed synchronously with the deterministic providers (sentiment + nearest issue). |
| GET | `/feedback` | Filters: `dataset_id, q` (case-insensitive substring), `sentiment` (`positive|neutral|negative`, multi), `category` (multi), `source`, `issue_id`, `date_from`, `date_to`, `include_duplicates` (default false). Sort: `created_at, sentiment_score, duplicate_count`. |
| GET | `/feedback/{feedback_id}` | original + normalized text, analysis, issues, duplicate count |

`FeedbackItem`
```json
{ "id": "…", "external_ref": "row-17", "text": "My order was processed incorrectly…",
  "category": "Operational Issues", "source": null, "created_at": null,
  "duplicate_count": 274, "sentiment": {"label": "negative", "score": -0.48, "provider": "vader@3.3.2"},
  "issue": {"id": "…", "key": "ISS-003", "title": "Wrong items received"} }
```

### Analysis & analytics
| Method | Path | Notes |
|---|---|---|
| POST | `/datasets/{dataset_id}/analyze` | `{force?: bool}` → 202 `AnalysisJob`. Returns existing job (200) when identical config already ran/is running. |
| GET | `/datasets/{dataset_id}/analytics` | Chart-ready KPIs (below). Filters: `category, sentiment, source, date_from, date_to`. |
| GET | `/datasets/{dataset_id}/trends` | `granularity=day|week|month`; returns `availability:"unavailable"` + reason if no timestamps. |
| GET | `/datasets/{dataset_id}/issues` | Same shape/filters as `/issues`, scoped. |

`Analytics`
```json
{ "dataset_id": "…", "filters": {}, "job_id": "…",
  "totals": {"rows": 7000, "distinct_texts": 320, "duplicate_rows": 6680},
  "sentiment": {"positive": {"rows": 2100, "share": 0.30}, "neutral": {…}, "negative": {…},
                "method": "VADER compound ≥0.05 positive, ≤−0.05 negative"},
  "by_category": [{"category": "Fraud and Scam", "rows": 1755, "negative_share": 0.91}],
  "by_source": {"availability": "unavailable", "reason": "No source column."},
  "top_issues": [{"id": "…", "key": "ISS-001", "title": "…", "rows": 276, "distinct": 9, "priority_score": 78.4}],
  "volume_over_time": {"availability": "unavailable", "reason": "Dataset has no timestamp column."} }
```

### Issues
| Method | Path | Notes |
|---|---|---|
| GET | `/issues` | Filters: `dataset_id, status (multi), kind (issue|strength), category, min_priority, q`. Default sort `-priority_score`. |
| GET | `/issues/{issue_id}` | Full detail + evidence + score breakdown + audit trail |
| PATCH | `/issues/{issue_id}` | `{status?, owner?, note?}`; validated transitions, writes `audit_events` |

Allowed transitions: `open → investigating | planned | dismissed`; `investigating → planned | resolved | dismissed | open`; `planned → resolved | investigating | dismissed`; `resolved → open`; `dismissed → open`.

`IssueDetail` (abridged)
```json
{ "id": "…", "key": "ISS-001", "title": "Seller requested additional payment (scam)",
  "kind": "issue", "category": "Fraud and Scam", "description": "Customers report …",
  "rows": 276, "distinct": 4, "sentiment_distribution": {"negative": 1.0, "neutral": 0, "positive": 0},
  "first_seen": null, "last_seen": null,
  "trend": {"value": null, "availability": "unavailable", "reason": "No timestamps."},
  "priority": { "score": 74.2, "label": "decision-support score (not a probability of churn or loss)",
    "confidence": "low",
    "components": [
      {"name": "impact", "value": 0.82, "weight": 0.30, "effective_weight": 0.43, "available": true,
       "explanation": "Mean negative intensity 0.71; category severity weight 1.0 (configured estimate)."},
      {"name": "trend", "value": null, "weight": 0.20, "effective_weight": 0, "available": false,
       "explanation": "Unavailable: dataset has no timestamps."} ],
    "limitations": ["Trend and recency excluded; weights renormalized over 70% of the formula.",
                    "Only 4 distinct texts support this issue (276 rows are repeats)."] },
  "evidence": [{"feedback_id": "…", "text": "I encountered a scam where…", "duplicate_count": 276, "rank": 1}],
  "status": "open", "owner": null, "audit": [] }
```

### Recommendations
| Method | Path | Notes |
|---|---|---|
| GET | `/issues/{issue_id}/recommendations` | Generated during analysis; `?regenerate=true` re-runs (rate limited) |
| POST | `/recommendations/{recommendation_id}/actions` | `{action: "accept"|"dismiss"|"track", owner?, note?}` → creates `tracked_actions` row + audit event |

`Recommendation`
```json
{ "id": "…", "issue_id": "…", "generated_by": "llm", "model": "<model-id>", "prompt_version": "rec-v1",
  "ai_generated": true, "status": "proposed",
  "title": "…", "problem_statement": "…", "recommended_action": "…", "rationale": "…",
  "supporting_feedback_ids": ["…"], "expected_outcome": "…",
  "confidence_label": "low|medium|high", "limitations": ["…"] }
```

### Reports
| Method | Path | Notes |
|---|---|---|
| POST | `/reports` | `{dataset_id, filters?, title?, include_strengths?}` → 201 snapshot (JSON stored, immutable) |
| GET | `/reports` | paginated |
| GET | `/reports/{report_id}` | `{meta, dataset, processing, key_findings, prioritized_issues[], evidence_refs[], recommendations[], methodology, limitations}` |
| GET | `/reports/{report_id}/export.csv` | one row per prioritized issue; formula-escaped |

### Integrations & curation (Adaption)
| Method | Path | Notes |
|---|---|---|
| GET | `/integrations/status` | `{sentiment:{provider,status}, llm:{provider,status,model}, adaption:{status:"disabled|configured|reachable|error", checked_at, detail}}` — derived from real checks |
| POST | `/datasets/{dataset_id}/curation/estimate` | Builds instruction dataset, calls Adaption `adapt(estimate=True)`, returns credit estimate. 409 if Adaption disabled. |
| POST | `/datasets/{dataset_id}/curation/runs` | Starts the Adaption run → 202 `CurationRun` |
| GET | `/curation/runs/{run_id}` | status, Adaption ids, evaluation metrics, classifier comparison (baseline vs curated) |

---

## 3. Frontend view → endpoint mapping

| Frontend element (current mock source) | Endpoint | Change needed in UI |
|---|---|---|
| Overview KPI cards: NPS `+38`, GMV `+$42.5K` (`trajectoryData`) | `/datasets/{id}/analytics` | **Replace** with Total feedback, Negative share, Distinct issues, Top-priority score. GMV/NPS have no data source. |
| Overview trajectory chart + range buttons 24h/7D/30D/Q3 | `/datasets/{id}/trends` | Show "Trend unavailable — no timestamps" state for the supplied CSV; works for timestamped datasets. |
| Friction cluster cards ISS-884/885/886 (`FrictionClusters.jsx`) | `/issues?dataset_id=&kind=issue&page_size=3` | Bind title, rows/distinct, priority, status; remove `$…/week` impact. |
| Evidence drawer (`issueContexts`) | `/issues/{id}` + `/issues/{id}/recommendations` | Root cause → `description`; impact → priority breakdown; quotes → `evidence[]`; "Deploy Fix" → recommendation `track` action. |
| Feedback explorer table + filters | `/feedback` (server-side filters + pagination) | Order Value column removed (no data); sentiment/category filters map 1:1; channel filter hidden when `by_source` unavailable. |
| CSV import modal (`runVectorIngest`) | `POST /datasets/imports` → poll `/jobs/{id}` | Progress bar driven by real job stages. "Vectorizing… text-embedding-3-large" copy removed (not used). |
| Decision Studio ROI slider ($35.3K, $1.84M) | — | **Remove or relabel** as a user-input what-if calculator with no data claims. |
| Friction Radar | `/issues` (priority vs distinct evidence) | Plot real issues. |
| Telemetry stream terminal | `/jobs/{id}` stage events | Show real job log; remove "LIVE 60Hz", "P99 22ms", "96.4% confidence". |
| Hotfix modal / Jira keys | `POST /recommendations/{id}/actions` | Rename to "Track action"; no fake deployment simulation. |
| Global search | `/feedback?q=` and `/issues?q=` | — |
| New: Reports button | `POST /reports`, `GET /reports/{id}/export.csv` | Add export action. |
| New: Integration badge | `/integrations/status` | Real status only. |
