"""
Borrower-health monitoring helpers for Bandhan.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

import networkx as nx


class EnhancedDetector:
    def __init__(self, graph=None):
        self.graph = graph if graph else nx.Graph()
        self.risk_cache = {}
        self.cluster_cache = None
        self.last_cluster_detection = None

    def calculate_risk(self, borrower_id):
        if borrower_id not in self.graph:
            return 0
        if borrower_id in self.risk_cache:
            cached_time, cached_score = self.risk_cache[borrower_id]
            if (datetime.now() - cached_time).seconds < 60:
                return cached_score

        neighbors = list(self.graph.neighbors(borrower_id))
        risk_score = 0
        scheme_neighbors = [n for n in neighbors if str(n).startswith("SCHEME::")]
        region_neighbors = [n for n in neighbors if str(n).startswith("REGION::")]
        peer_neighbors = [n for n in neighbors if str(n).startswith("BORR_")]

        risk_score += min(len(peer_neighbors) * 15, 35)
        risk_score += 20 if region_neighbors else 0
        risk_score += 15 if scheme_neighbors else 0
        risk_score += min(self.graph.degree(borrower_id) * 6, 30)

        final_score = min(risk_score, 100)
        self.risk_cache[borrower_id] = (datetime.now(), final_score)
        return final_score

    def find_stress_clusters(self, min_size=2, force_refresh=False):
        if not force_refresh and self.cluster_cache and self.last_cluster_detection:
            if (datetime.now() - self.last_cluster_detection).seconds < 300:
                return self.cluster_cache

        borrower_nodes = [n for n in self.graph.nodes() if str(n).startswith("BORR_")]
        groups = defaultdict(list)
        for borrower in borrower_nodes:
            region = next((n.replace("REGION::", "") for n in self.graph.neighbors(borrower) if str(n).startswith("REGION::")), "Unknown")
            scheme = next((n.replace("SCHEME::", "") for n in self.graph.neighbors(borrower) if str(n).startswith("SCHEME::")), "Unknown")
            groups[(region, scheme)].append(borrower)

        clusters = []
        for idx, ((region, scheme), borrowers) in enumerate(groups.items()):
            if len(borrowers) < min_size:
                continue
            avg_risk = sum(self.calculate_risk(borrower) for borrower in borrowers) / len(borrowers)
            clusters.append(
                {
                    "cluster_id": idx,
                    "region": region,
                    "loan_scheme": scheme,
                    "borrowers": borrowers,
                    "size": len(borrowers),
                    "cluster_risk_score": round(avg_risk, 1),
                    "detected_at": datetime.now().isoformat(),
                }
            )

        clusters.sort(key=lambda item: item["cluster_risk_score"], reverse=True)
        self.cluster_cache = clusters
        self.last_cluster_detection = datetime.now()
        return clusters

    def detect_anomalies_realtime(self, borrower_id, event_type, event_data):
        anomalies = []
        if borrower_id in self.graph and self.graph.degree(borrower_id) >= 3:
            anomalies.append(("cohort_pressure", "medium"))

        if event_type == "emi_payment" and event_data.get("status") == "MISSED":
            anomalies.append(("missed_emi_event", "high"))
        if event_type == "cashflow_update" and event_data.get("coverage_ratio", 1.2) < 1.0:
            anomalies.append(("cashflow_coverage_stress", "critical"))
        if event_data.get("regional_stress_factor", 0) > 0.7:
            anomalies.append(("high_regional_stress", "medium"))

        return len(anomalies) > 0, anomalies

    def get_borrower_network(self, borrower_id, depth=2):
        if False:  # MUTATION
            return nx.Graph()

        nodes = {borrower_id}
        current_level = {borrower_id}
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                next_level.update(self.graph.neighbors(node))
            nodes.update(next_level)
            current_level = next_level
        return self.graph.subgraph(nodes).copy()

    def get_high_risk_borrowers(self, threshold=50, limit=100):
        borrowers = [n for n in self.graph.nodes() if str(n).startswith("BORR_")]
        risks = [(borrower, self.calculate_risk(borrower)) for borrower in borrowers]
        risks = [item for item in risks if item[1] >= threshold]
        risks.sort(key=lambda item: item[1], reverse=True)
        return risks[:limit]

    def generate_alert(self, borrower_id, risk_score, anomalies):
        severity = "CRITICAL" if risk_score >= 70 else "HIGH" if risk_score >= 50 else "MEDIUM"
        return {
            "alert_id": f"ALERT_{borrower_id}_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "borrower_id": borrower_id,
            "risk_score": risk_score,
            "severity": severity,
            "anomalies": [{"type": item[0], "severity": item[1]} for item in anomalies],
            "recommended_action": self._get_recommended_action(risk_score),
            "requires_review": risk_score >= 50,
        }

    def _get_recommended_action(self, risk_score):
        if risk_score >= 80:
            return "PRIORITY_SUPPORT_REVIEW"
        if risk_score >= 70:
            return "RESTRUCTURE_AND_OUTREACH"
        if risk_score >= 50:
            return "FOLLOW_UP_AND_MONITOR"
        return "ROUTINE_MONITORING"

    def get_statistics(self):
        borrowers = [n for n in self.graph.nodes() if str(n).startswith("BORR_")]
        risks = [self.calculate_risk(borrower) for borrower in borrowers]
        clusters = self.find_stress_clusters()
        return {
            "total_borrowers": len(borrowers),
            "high_risk_borrowers": len([risk for risk in risks if risk >= 50]),
            "critical_risk_borrowers": len([risk for risk in risks if risk >= 70]),
            "stress_clusters_detected": len(clusters),
            "graph_nodes": self.graph.number_of_nodes(),
            "graph_edges": self.graph.number_of_edges(),
            "largest_cluster_size": max([cluster["size"] for cluster in clusters], default=0),
        }
