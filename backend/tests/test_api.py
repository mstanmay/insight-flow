import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_and_ready():
    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "ok"

    r_ready = client.get("/ready")
    assert r_ready.status_code == 200
    assert r_ready.json()["status"] == "ready"


def test_list_datasets():
    resp = client.get("/api/v1/datasets")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    ds = data["items"][0]
    assert "id" in ds
    assert "name" in ds
    assert ds["row_count"] == 7000
    assert ds["distinct_text_count"] == 320


def test_dataset_analytics_and_issues():
    resp = client.get("/api/v1/datasets")
    ds_id = resp.json()["items"][0]["id"]

    # Issues query
    issues_resp = client.get(f"/api/v1/issues?dataset_id={ds_id}")
    assert issues_resp.status_code == 200
    issues_data = issues_resp.json()
    assert "items" in issues_data
    assert len(issues_data["items"]) > 0

    first_issue = issues_data["items"][0]
    issue_id = first_issue["id"]

    # Issue detail with citations
    detail_resp = client.get(f"/api/v1/issues/{issue_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert "evidence" in detail
    assert len(detail["evidence"]) > 0
    assert "priority_breakdown" in detail
    assert "recommendations" in detail

    # Analytics aggregates
    analytics_resp = client.get(f"/api/v1/datasets/{ds_id}/analytics")
    assert analytics_resp.status_code == 200
    analytics = analytics_resp.json()
    assert analytics["totals"]["rows_total"] == 7000
    assert analytics["totals"]["distinct_texts"] == 320
    assert "sentiment" in analytics
    assert "categories" in analytics
    assert "data_limitations" in analytics


def test_integrations_status():
    resp = client.get("/api/v1/integrations/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "adaption_labs" in data
    assert "sentiment" in data
    assert "clustering" in data
