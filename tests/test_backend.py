"""
Tests for backend.py
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend import app, borrower_df


client = TestClient(app)
KNOWN_BORROWER = borrower_df["borrower_id"].iloc[0]


@pytest.mark.slow
class TestBackendAPI:
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "status" in data

    def test_stats_endpoint(self):
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_borrowers" in data
        assert "average_health" in data
        assert "high_risk_borrowers" in data

    def test_graph_stats_endpoint(self):
        response = client.get("/graph/stats")
        assert response.status_code == 200
        data = response.json()
        assert "graph" in data
        assert "node_types" in data

    def test_clusters_endpoint(self):
        response = client.get("/clusters")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "clusters" in data

    def test_borrowers_endpoint(self):
        response = client.get("/borrowers?min_risk=45")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "borrowers" in data
        assert isinstance(data["borrowers"], list)

    def test_borrower_analysis_valid(self):
        response = client.get(f"/borrowers/{KNOWN_BORROWER}")
        assert response.status_code == 200
        data = response.json()
        assert data["borrower_id"] == KNOWN_BORROWER
        assert "risk_score" in data
        assert "health_score" in data
        assert "status" in data

    def test_borrower_analysis_invalid(self):
        response = client.get("/borrowers/BORR_99999")
        assert response.status_code == 404

    def test_support_action(self):
        response = client.post(f"/borrowers/{KNOWN_BORROWER}/support")
        assert response.status_code == 200
        data = response.json()
        assert data["borrower"]["status"] == "SUPPORT_REQUIRED"

    def test_resolve_action(self):
        response = client.post(f"/borrowers/{KNOWN_BORROWER}/resolve")
        assert response.status_code == 200
        data = response.json()
        assert data["borrower"]["status"] == "RECOVERING"

    def test_simulate_intervention(self):
        response = client.post(
            "/interventions/simulate",
            json={"borrower_id": KNOWN_BORROWER, "support_type": "RESTRUCTURE_REVIEW", "expected_impact": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["borrower_id"] == KNOWN_BORROWER
        assert data["projected_risk_score"] <= data["current_risk_score"]

    def test_stream_test_endpoint(self):
        response = client.get("/stream/test")
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert isinstance(data["events"], list)

    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_analyze_endpoint_valid(self):
        response = client.get(f"/analyze/{KNOWN_BORROWER}")
        assert response.status_code == 200
        data = response.json()
        assert data["borrower_id"] == KNOWN_BORROWER
        assert "risk_probability" in data
        assert "risk_band" in data
        assert "recovery_action" in data
        assert "key_signals" in data

    def test_analyze_endpoint_invalid(self):
        response = client.get("/analyze/BORR_NONEXISTENT")
        assert response.status_code == 404

    def test_narrative_endpoint(self):
        response = client.get(f"/narrative/{KNOWN_BORROWER}")
        assert response.status_code == 200
        data = response.json()
        assert "narrative" in data
        assert len(data["narrative"]) > 0

    def test_explain_endpoint(self):
        response = client.get(f"/explain/{KNOWN_BORROWER}")
        assert response.status_code == 200
        data = response.json()
        assert "feature_contributions" in data
        assert "top_driver" in data
        assert "explanation_summary" in data

    def test_update_status_endpoint(self):
        response = client.post(
            f"/update-status/{KNOWN_BORROWER}",
            json={"status": "SUPPORT_REQUIRED"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["new_status"] == "SUPPORT_REQUIRED"

    def test_update_status_invalid_status(self):
        response = client.post(
            f"/update-status/{KNOWN_BORROWER}",
            json={"status": "INVALID_STATUS"},
        )
        assert response.status_code == 400

    def test_portfolio_summary_endpoint(self):
        response = client.get("/portfolio/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_borrowers" in data
        assert "band_counts" in data
        assert "at_risk_exposure" in data
        assert "borrowers" in data



@pytest.mark.slow
class TestBackendPerformance:
    def test_stats_response_time(self):
        import time

        start = time.time()
        response = client.get("/stats")
        duration = time.time() - start
        assert response.status_code == 200
        assert duration < 30.0
