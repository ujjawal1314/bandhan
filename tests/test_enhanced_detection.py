"""
Tests for enhanced_detection.py
"""

import os
import sys

import networkx as nx
import pytest


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from enhanced_detection import EnhancedDetector


class TestEnhancedDetector:
    def test_initialization_empty(self):
        detector = EnhancedDetector()
        assert detector.graph is not None
        assert detector.risk_cache == {}

    def test_initialization_with_graph(self, sample_graph):
        detector = EnhancedDetector(sample_graph)
        assert detector.graph.number_of_nodes() > 0

    def test_calculate_risk_basic(self, sample_graph):
        detector = EnhancedDetector(sample_graph)
        risk = detector.calculate_risk("BORR_00001")
        assert isinstance(risk, (int, float))
        assert 0 <= risk <= 100

    def test_calculate_risk_exact_score(self):
        import networkx as nx

        graph = nx.Graph()
        graph.add_edges_from([
            ("BORR_1", "BORR_2"),
            ("BORR_1", "REGION::North"),
            ("BORR_1", "SCHEME::Personal"),
        ])

        detector = EnhancedDetector(graph)
        assert detector.calculate_risk("BORR_1") == 68

    def test_calculate_risk_nonexistent(self, sample_graph):
        detector = EnhancedDetector(sample_graph)
        assert detector.calculate_risk("BORR_99999") == 0

    def test_risk_caching(self, sample_graph):
        detector = EnhancedDetector(sample_graph)
        risk1 = detector.calculate_risk("BORR_00001")
        assert "BORR_00001" in detector.risk_cache
        risk2 = detector.calculate_risk("BORR_00001")
        assert risk1 == risk2

    def test_find_stress_clusters(self, sample_graph):
        detector = EnhancedDetector(sample_graph)
        clusters = detector.find_stress_clusters(min_size=2)
        assert isinstance(clusters, list)
        for cluster in clusters:
            assert "cluster_id" in cluster
            assert "size" in cluster
            assert "borrowers" in cluster
            assert "cluster_risk_score" in cluster

    def test_cluster_caching(self, sample_graph):
        detector = EnhancedDetector(sample_graph)
        clusters1 = detector.find_stress_clusters()
        assert detector.cluster_cache is not None
        clusters2 = detector.find_stress_clusters()
        assert clusters1 == clusters2

    def test_cluster_force_refresh(self, sample_graph):
        detector = EnhancedDetector(sample_graph)
        detector.find_stress_clusters()
        detector.find_stress_clusters(force_refresh=True)
        assert detector.last_cluster_detection is not None

    def test_detect_anomalies_realtime(self, sample_graph):
        detector = EnhancedDetector(sample_graph)
        is_anomaly, anomalies = detector.detect_anomalies_realtime(
            "BORR_00001",
            "cashflow_update",
            {"coverage_ratio": 0.92, "regional_stress_factor": 0.75},
        )
        assert isinstance(is_anomaly, bool)
        assert isinstance(anomalies, list)

    def test_detect_missed_emi_anomaly(self, sample_graph):
        detector = EnhancedDetector(sample_graph)
        _, anomalies = detector.detect_anomalies_realtime("BORR_00001", "emi_payment", {"status": "MISSED"})
        assert "missed_emi_event" in [item[0] for item in anomalies]

    def test_get_borrower_network(self, sample_graph):
        detector = EnhancedDetector(sample_graph)
        subgraph = detector.get_borrower_network("BORR_00001", depth=1)
        assert isinstance(subgraph, nx.Graph)
        assert "BORR_00001" in subgraph.nodes()

    def test_get_high_risk_borrowers(self, sample_graph):
        detector = EnhancedDetector(sample_graph)
        borrowers = detector.get_high_risk_borrowers(threshold=0, limit=10)
        assert isinstance(borrowers, list)
        assert len(borrowers) <= 10
        for borrower, risk in borrowers:
            assert borrower.startswith("BORR_")
            assert 0 <= risk <= 100

    def test_generate_alert(self, sample_graph):
        detector = EnhancedDetector(sample_graph)
        alert = detector.generate_alert("BORR_00001", 85, [("cashflow_coverage_stress", "critical")])
        assert "borrower_id" in alert
        assert alert["borrower_id"] == "BORR_00001"
        assert alert["severity"] == "CRITICAL"

    def test_recommended_actions(self, sample_graph):
        detector = EnhancedDetector(sample_graph)
        assert detector.generate_alert("BORR_00001", 85, [])["recommended_action"] == "PRIORITY_SUPPORT_REVIEW"
        assert detector.generate_alert("BORR_00001", 72, [])["recommended_action"] == "RESTRUCTURE_AND_OUTREACH"
        assert detector.generate_alert("BORR_00001", 55, [])["recommended_action"] == "FOLLOW_UP_AND_MONITOR"
        assert detector.generate_alert("BORR_00001", 35, [])["recommended_action"] == "ROUTINE_MONITORING"

    def test_get_statistics(self, sample_graph):
        detector = EnhancedDetector(sample_graph)
        stats = detector.get_statistics()
        assert "total_borrowers" in stats
        assert "stress_clusters_detected" in stats
        assert stats["graph_nodes"] == sample_graph.number_of_nodes()