from __future__ import annotations

from datetime import datetime
import json
import time
from typing import List

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import networkx as nx
import pandas as pd

from api_models import BorrowerActionRequest, InterventionSimulationRequest
from detection_engine import SatarkSetuDetector
from repositories import BorrowerRepository
from pipeline import compute_risk_score, risk_band, recovery_action
from model import RiskNet


try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass



app = FastAPI(title="SatarkSetu - Borrower Health Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections: List[WebSocket] = []
repo = BorrowerRepository()

borrower_df = pd.read_csv("borrowers.csv")
txn_df = pd.read_csv("loan_transactions.csv", parse_dates=["timestamp"])
regional_df = pd.read_csv("regional_context.csv")

detector = SatarkSetuDetector(borrower_df, txn_df, regional_df)
graph_stats = detector.build_graph()
graph = detector.get_networkx_graph()


def sync_borrower(borrower_id: str, default_status: str = "ACTIVE") -> dict:
    analysis = detector.analyze_borrower(borrower_id).as_dict()
    row = borrower_df[borrower_df["borrower_id"] == borrower_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Borrower not found")
    repo.upsert_borrower_risk(
        borrower_id,
        risk_score=analysis["risk_score"],
        health_score=analysis["health_score"],
        name=str(row.iloc[0]["name"]),
        default_status=default_status,
    )
    return analysis


def merged_borrower_record(borrower_id: str) -> dict:
    analysis = sync_borrower(borrower_id)
    repo_row = repo.get_borrower(borrower_id) or repo.ensure_borrower(borrower_id, name=analysis["name"])
    profile = borrower_df[borrower_df["borrower_id"] == borrower_id].iloc[0].to_dict()
    profile.update(analysis)
    profile["status"] = repo_row.get("status", "ACTIVE")
    return profile


def stream_events():
    top_borrowers = detector.get_flagged_borrowers(threshold=50)[:80]
    for item in top_borrowers:
        event = {
            "type": "borrower_alert",
            "timestamp": datetime.utcnow().isoformat(),
            "borrower_id": item["borrower_id"],
            "name": item["name"],
            "risk_score": item["risk_score"],
            "health_score": item["health_score"],
            "risk_level": item["risk_level"],
            "region": item["region"],
            "loan_scheme": item["loan_scheme"],
            "behavioral_flags": item["behavioral_flags"],
            "contextual_flags": item["contextual_flags"],
        }
        time.sleep(0.02)
        yield f"data: {json.dumps(event)}\n\n"


@app.get("/")
def root():
    return {
        "service": "SatarkSetu Borrower Health Backend",
        "status": "active",
        "version": "2.0",
        "endpoints": {
            "health": "/health",
            "stats": "/stats",
            "borrowers": "/borrowers",
            "borrower_analysis": "/borrowers/{borrower_id}",
            "analyze": "/analyze/{borrower_id}",
            "narrative": "/narrative/{borrower_id}",
            "explain": "/explain/{borrower_id}",
            "update_status": "POST /update-status/{borrower_id}",
            "portfolio_summary": "/portfolio/summary",
            "stress_clusters": "/clusters",
            "graph_stats": "/graph/stats",
            "support_action": "POST /borrowers/{borrower_id}/support",
            "resolve_action": "POST /borrowers/{borrower_id}/resolve",
            "simulate_intervention": "POST /interventions/simulate",
            "stream": "/stream",
        },
    }



@app.get("/stats")
def stats():
    summary = detector.portfolio_summary()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        **summary,
        "regional_hotspots": len(detector.detect_stress_clusters()),
        "watchlist_borrowers": repo.status_count("WATCHLIST"),
        "support_required_borrowers": repo.status_count("SUPPORT_REQUIRED"),
        "recovering_borrowers": repo.status_count("RECOVERING"),
        "graph": {"nodes": graph.number_of_nodes(), "edges": graph.number_of_edges()},
    }


@app.get("/graph/stats")
def graph_stats_endpoint():
    return {
        "graph": {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "density": nx.density(graph) if graph.number_of_nodes() > 1 else 0.0,
        },
        "node_types": graph_stats["node_types"],
    }


@app.get("/clusters")
def stress_clusters():
    clusters = detector.detect_stress_clusters()
    return {"count": len(clusters), "clusters": clusters}


@app.get("/borrowers")
def borrowers(min_risk: int = 0, limit: int = 100):
    records = []
    for borrower_id in borrower_df["borrower_id"]:
        analysis = sync_borrower(borrower_id)
        if analysis["risk_score"] < min_risk:
            continue
        repo_row = repo.get_borrower(borrower_id) or {}
        records.append({**analysis, "status": repo_row.get("status", "ACTIVE")})
    records.sort(key=lambda row: row["risk_score"], reverse=True)
    return {"count": len(records), "borrowers": records[:limit]}


@app.get("/borrowers/{borrower_id}")
def borrower_analysis(borrower_id: str):
    if borrower_id not in set(borrower_df["borrower_id"]):
        raise HTTPException(status_code=404, detail="Borrower not found")

    record = merged_borrower_record(borrower_id)
    txns = txn_df[txn_df["borrower_id"] == borrower_id].sort_values("timestamp")
    record["recent_transactions"] = txns.tail(12).to_dict("records")
    record["graph_degree"] = graph.degree(borrower_id) if borrower_id in graph else 0
    return record


@app.get("/borrowers/{borrower_id}/status")
def borrower_status(borrower_id: str):
    borrower = repo.get_borrower(borrower_id)
    if not borrower:
        sync_borrower(borrower_id)
        borrower = repo.get_borrower(borrower_id)
    if not borrower:
        raise HTTPException(status_code=404, detail="Borrower not found")
    return borrower


@app.post("/borrowers/{borrower_id}/support")
def mark_support_required(borrower_id: str, req: BorrowerActionRequest | None = None):
    analysis = sync_borrower(borrower_id, default_status="SUPPORT_REQUIRED")
    request = req or BorrowerActionRequest()
    borrower = repo.set_status(
        borrower_id,
        status="SUPPORT_REQUIRED",
        reason=request.reason,
        performed_by=request.performed_by,
    )
    return {"borrower": borrower, "analysis": analysis, "message": "Borrower marked for support review"}


@app.post("/borrowers/{borrower_id}/resolve")
def mark_recovering(borrower_id: str, req: BorrowerActionRequest | None = None):
    analysis = sync_borrower(borrower_id, default_status="RECOVERING")
    request = req or BorrowerActionRequest(reason="Borrower moved to recovery monitoring")
    borrower = repo.set_status(
        borrower_id,
        status="RECOVERING",
        reason=request.reason,
        performed_by=request.performed_by,
    )
    return {"borrower": borrower, "analysis": analysis, "message": "Borrower moved to recovery monitoring"}


@app.post("/interventions/simulate")
def simulate_intervention(req: InterventionSimulationRequest):
    if req.borrower_id not in set(borrower_df["borrower_id"]):
        raise HTTPException(status_code=404, detail="Borrower not found")
    current = detector.analyze_borrower(req.borrower_id).as_dict()
    improved_risk = max(0, current["risk_score"] - int(round(req.expected_impact)))
    improved_health = min(100, current["health_score"] + int(round(req.expected_impact)))
    return {
        "borrower_id": req.borrower_id,
        "support_type": req.support_type,
        "current_risk_score": current["risk_score"],
        "projected_risk_score": improved_risk,
        "current_health_score": current["health_score"],
        "projected_health_score": improved_health,
    }


@app.get("/stream")
def stream():
    return StreamingResponse(
        stream_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/stream/test")
def stream_test():
    events = []
    for item in detector.get_flagged_borrowers(threshold=60)[:5]:
        events.append(
            {
                "borrower_id": item["borrower_id"],
                "risk_score": item["risk_score"],
                "risk_level": item["risk_level"],
                "region": item["region"],
            }
        )
    return {"message": "Borrower alert stream test", "count": len(events), "events": events}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        await websocket.send_json(
            {
                "type": "connection",
                "message": "Connected to SatarkSetu borrower health backend",
                "stats": detector.portfolio_summary(),
            }
        )
        for item in detector.get_flagged_borrowers(threshold=60)[:25]:
            await websocket.send_json({"type": "borrower_alert", **item})
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)



@app.get("/health")
def health():
    return {"status": "ok", "model": "RiskNet loaded"}


@app.get("/analyze/{borrower_id}")
def analyze_borrower(borrower_id: str):
    """
    Run AI risk analysis for a single borrower.
    Called when user clicks 'AI Risk Analysis' button.
    """
    row = borrower_df[borrower_df["borrower_id"] == borrower_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Borrower {borrower_id} not found")

    borrower = row.iloc[0].to_dict()
    numeric_fields = [
        'loan_amount', 'outstanding_amount', 'emi_amount',
        'avg_monthly_inflow', 'avg_monthly_outflow', 'current_balance',
        'repayment_consistency', 'inflow_stability', 'balance_trend',
        'missed_payments_90d', 'days_past_due', 'peer_score',
        'regional_stress_factor'
    ]
    for field in numeric_fields:
        val = borrower.get(field)
        if val is None or pd.isna(val):
            borrower[field] = 0.0

    borrower_txns = txn_df[txn_df["borrower_id"] == borrower_id]
    transactions = borrower_txns.to_dict("records") if not borrower_txns.empty else []

    reg_rows = regional_df[regional_df["region"] == borrower.get("region", "")]
    regional = reg_rows.iloc[0].to_dict() if not reg_rows.empty else {}

    probability = compute_risk_score(borrower, transactions, regional)
    band = risk_band(probability)
    action = recovery_action(probability)

    emi_txns = [t for t in transactions if t.get('transaction_type') == 'EMI_PAYMENT']
    miss_rate = sum(1 for t in emi_txns if t.get('status') == 'MISSED') / (len(emi_txns) or 1)

    return {
        "borrower_id": borrower_id,
        "name": borrower.get("name", "Unknown"),
        "region": borrower.get("region", "Unknown"),
        "loan_scheme": borrower.get("loan_scheme", "Unknown"),
        "loan_amount": float(borrower.get("loan_amount", 0)),
        "outstanding_amount": float(borrower.get("outstanding_amount", 0)),
        "missed_payments": int(borrower.get("missed_payments_90d", 0)),
        "days_past_due": int(borrower.get("days_past_due", 0)),
        "risk_probability": round(probability, 4),
        "risk_band": band,
        "recovery_action": action,
        "key_signals": {
            "repayment_consistency": round(float(borrower.get("repayment_consistency", 0)), 2),
            "peer_score": round(float(borrower.get("peer_score", 0)), 1),
            "regional_stress": round(float(borrower.get("regional_stress_factor", 0)), 2),
            "txn_miss_rate": round(float(miss_rate if miss_rate > 0 else borrower.get("missed_payments_90d", 0) / 6.0), 3),
            "buffer_ratio": round(float(borrower.get("current_balance", 0) / (borrower.get("emi_amount", 1) + 1)), 2),
            "inflow_stability": round(float(borrower.get("inflow_stability", 0)), 2),
            "days_past_due": int(borrower.get("days_past_due", 0)),
        }
    }


@app.get("/narrative/{borrower_id}")
def get_narrative(borrower_id: str):
    row = borrower_df[borrower_df["borrower_id"] == borrower_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Borrower {borrower_id} not found")

    borrower = row.iloc[0].to_dict()
    for field in [
        'loan_amount', 'outstanding_amount', 'emi_amount',
        'avg_monthly_inflow', 'avg_monthly_outflow', 'current_balance',
        'repayment_consistency', 'inflow_stability', 'balance_trend',
        'missed_payments_90d', 'days_past_due', 'peer_score',
        'regional_stress_factor'
    ]:
        val = borrower.get(field)
        if val is None or pd.isna(val):
            borrower[field] = 0.0

    borrower_txns = txn_df[txn_df["borrower_id"] == borrower_id]
    transactions = borrower_txns.to_dict("records") if not borrower_txns.empty else []

    reg_rows = regional_df[regional_df["region"] == borrower.get("region", "")]
    regional = reg_rows.iloc[0].to_dict() if not reg_rows.empty else {}

    probability = compute_risk_score(borrower, transactions, regional)
    band = risk_band(probability)

    missed = int(borrower.get('missed_payments_90d', 0))
    dpd    = int(borrower.get('days_past_due', 0))
    region = borrower.get('region', 'the region')
    scheme = borrower.get('loan_scheme', 'the scheme')
    stress = float(borrower.get('regional_stress_factor', 0.5))
    peer   = float(borrower.get('peer_score', 80))
    repay  = float(borrower.get('repayment_consistency', 0.8))

    action_label = recovery_action(probability)
    next_step = (
        "Immediate outreach is advised to prevent NPA formation."
        if probability >= 0.60
        else "Monitor closely over the next 30 days for further deterioration signals."
        if probability >= 0.40
        else "Standard portfolio review protocols apply."
    )

    narrative = f"""
Borrower Risk Assessment — {band} Risk ({probability*100:.1f}%)

This borrower has recorded {missed} missed payment(s) in the last 90 days with {dpd} days past due, indicating {"significant" if missed >= 2 else "moderate" if missed == 1 else "minimal"} repayment stress. Their repayment consistency score of {repay:.2f} {"falls below" if repay < 0.75 else "is within"} the acceptable threshold.

The borrower operates under the {scheme} scheme in {region}, which carries a regional stress factor of {stress:.2f}. Their peer score of {peer:.0f} {"is below" if peer < 78 else "is in line with"} the regional cohort baseline, {"suggesting elevated peer-level credit stress in this segment" if peer < 78 else "suggesting stable peer-level performance"}.

Recommended Action: {action_label}. {next_step}
    """.strip()

    return {"narrative": narrative}


@app.get("/explain/{borrower_id}")
def explain_borrower(borrower_id: str):
    """
    Returns feature contribution breakdown for explainability chart.
    """
    row = borrower_df[borrower_df["borrower_id"] == borrower_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Borrower {borrower_id} not found")

    borrower = row.iloc[0].to_dict()
    for field in [
        'loan_amount', 'outstanding_amount', 'emi_amount',
        'avg_monthly_inflow', 'avg_monthly_outflow', 'current_balance',
        'repayment_consistency', 'inflow_stability', 'balance_trend',
        'missed_payments_90d', 'days_past_due', 'peer_score',
        'regional_stress_factor'
    ]:
        val = borrower.get(field)
        if val is None or pd.isna(val):
            borrower[field] = 0.0

    borrower_txns = txn_df[txn_df["borrower_id"] == borrower_id]
    transactions = borrower_txns.to_dict("records") if not borrower_txns.empty else []

    missed     = float(borrower.get('missed_payments_90d', 0))
    dpd        = float(borrower.get('days_past_due', 0))
    repayment  = float(borrower.get('repayment_consistency', 0.8))
    stress     = float(borrower.get('regional_stress_factor', 0.5))
    peer       = float(borrower.get('peer_score', 80))
    inflow_st  = float(borrower.get('inflow_stability', 0.8))

    emi_txns = [t for t in transactions if t.get('transaction_type') == 'EMI_PAYMENT']
    total = len(emi_txns) if emi_txns else 1
    miss_rate = sum(1 for t in emi_txns if t.get('status') == 'MISSED') / total
    delay_rate = sum(1 for t in emi_txns if t.get('status') == 'DELAYED') / total

    contributions = {
        "Missed Payments (90d)": round(min(missed / 4.0, 1.0) * 0.30, 4),
        "Days Past Due":         round(min(dpd / 90.0, 1.0) * 0.25, 4),
        "EMI Miss Rate":         round(miss_rate * 0.15, 4),
        "EMI Delay Rate":        round(delay_rate * 0.10, 4),
        "Repayment Consistency": round((1 - repayment) * 0.10, 4),
        "Regional Stress":       round(stress * 0.05, 4),
        "Peer Score Gap":        round((1 - peer / 100.0) * 0.03, 4),
        "Inflow Instability":    round((1 - inflow_st) * 0.02, 4),
    }

    total_risk = sum(contributions.values()) or 1
    percentages = {
        k: round((v / total_risk) * 100, 1)
        for k, v in contributions.items()
    }
    sorted_contributions = dict(
        sorted(percentages.items(), key=lambda x: x[1], reverse=True)
    )
    top_driver = max(contributions, key=contributions.get)

    return {
        "borrower_id": borrower_id,
        "feature_contributions": sorted_contributions,
        "raw_contributions": {k: round(v, 4) for k, v in contributions.items()},
        "top_driver": top_driver,
        "total_risk_score": round(total_risk, 4),
        "explanation_summary": (
            f"The primary driver of risk for this borrower is {top_driver}, "
            f"contributing {sorted_contributions[top_driver]:.1f}% of the total risk score."
        )
    }


@app.post("/update-status/{borrower_id}")
def update_borrower_status(borrower_id: str, payload: dict):
    """
    Updates borrower status in repository.
    payload: { "status": "SUPPORT_REQUIRED" } or { "status": "RECOVERING" }
    """
    new_status = payload.get("status")
    if new_status not in ["ACTIVE", "SUPPORT_REQUIRED", "RECOVERING", "WATCHLIST"]:
        raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")

    row = borrower_df[borrower_df["borrower_id"] == borrower_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"Borrower {borrower_id} not found")

    repo.set_status(
        borrower_id,
        status=new_status,
        reason=payload.get("reason", "Status updated via API"),
        performed_by=payload.get("performed_by", "dashboard"),
    )

    return {
        "success": True,
        "borrower_id": borrower_id,
        "new_status": new_status,
        "message": f"Status updated to {new_status}",
    }


@app.get("/portfolio/summary")
def portfolio_summary():
    """
    Returns risk band distribution across all borrowers.
    Used for dashboard overview.
    """
    records = []
    bands = {"CRITICAL": [], "HIGH": [], "MODERATE": [], "LOW": []}
    at_risk_exposure = 0.0

    reg_lookup = {r["region"]: r for r in regional_df.to_dict("records")}

    for _, row in borrower_df.iterrows():
        b = row.to_dict()
        b_id = b["borrower_id"]
        b_txns = txn_df[txn_df["borrower_id"] == b_id].to_dict("records")
        regional = reg_lookup.get(b.get("region", ""), {})

        prob = compute_risk_score(b, b_txns, regional)
        band = risk_band(prob)
        action = recovery_action(prob)

        out_amt = float(b.get("outstanding_amount", 0.0) or 0.0)
        record = {
            "borrower_id": b_id,
            "name": b.get("name", ""),
            "region": b.get("region", ""),
            "risk_band": band,
            "risk_probability": prob,
            "outstanding_amount": out_amt,
            "recovery_action": action,
        }
        records.append(record)
        if band in bands:
            bands[band].append(record)
        if band in ["CRITICAL", "HIGH"]:
            at_risk_exposure += out_amt

    return {
        "total_borrowers": len(records),
        "band_counts": {k: len(v) for k, v in bands.items()},
        "at_risk_exposure": round(at_risk_exposure, 2),
        "borrowers": records,
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting SatarkSetu Borrower Health Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

