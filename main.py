"""
Bandhan — FastAPI Backend
Unified backend serving AI risk analysis, graph analytics, and borrower health management.
"""

from backend import app
from pipeline import engineer_features, risk_band, recovery_action, compute_risk_score
from model import RiskNet

__all__ = ["app", "engineer_features", "risk_band", "recovery_action", "compute_risk_score", "RiskNet"]


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Bandhan Risk & Health Backend...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
