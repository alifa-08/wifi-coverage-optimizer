import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_and_root():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "DETECT -> UNDERSTAND -> PREDICT -> OPTIMIZE -> VERIFY" in res_root.json()["workflow"]

def test_api_demo_pipeline():
    res = client.post("/api/v1/dashboard/demo?scenario_name=Laboratory%20Dead%20Zone")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["measurements_count"] > 0
    assert data["dead_zones_count"] >= 1
    assert data["ml_accuracy"] > 0.65

def test_api_dashboard_summary():
    res = client.get("/api/v1/dashboard/summary/1")
    assert res.status_code == 200
    summary = res.json()
    assert summary["has_data"] is True
    assert summary["current_dead_zones"] >= 1

def test_api_dead_zone_analytics():
    res = client.get("/api/v1/dead-zones/analytics/summary/1")
    assert res.status_code == 200
    data = res.json()
    assert "severity_breakdown" in data
    assert "total_dead_zone_area" in data

def test_api_ml_metrics():
    res = client.get("/api/v1/ml/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "accuracy" in data
    assert "confusion_matrix" in data
    assert "feature_importances" in data

def test_api_alerts():
    res = client.get("/api/v1/alerts")
    assert res.status_code == 200
    alerts = res.json()
    assert isinstance(alerts, list)
    if alerts:
        alert_id = alerts[0]["id"]
        res_resolve = client.put(f"/api/v1/alerts/{alert_id}/resolve")
        assert res_resolve.status_code == 200
        assert res_resolve.json()["status"] == "RESOLVED"
