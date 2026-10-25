"""
Bandhan — AI Early Warning Credit Intelligence Platform
Full ML Pipeline: Feature Engineering + RiskNet Training + Scored Output
Uses: scikit-learn MLPClassifier (Neural Network) + StandardScaler
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    classification_report, roc_auc_score,
    confusion_matrix, accuracy_score
)
import warnings
warnings.filterwarnings("ignore")

print("=" * 60)
print("  Bandhan — RiskNet ML Pipeline")
print("=" * 60)

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────
print("\n[1/6] Loading data...")

borrowers    = pd.read_csv("/mnt/user-data/uploads/1773992991058_borrowers.csv")
transactions = pd.read_csv("/mnt/user-data/uploads/1773992991058_loan_transactions.csv")
regional     = pd.read_csv("/mnt/user-data/uploads/1773992991057_regional_context.csv")

print(f"    Borrowers     : {len(borrowers):,}")
print(f"    Transactions  : {len(transactions):,}")
print(f"    Regions       : {len(regional):,}")

# ─────────────────────────────────────────────
# 2. TRANSACTION FEATURE ENGINEERING
# ─────────────────────────────────────────────
print("\n[2/6] Engineering transaction features...")

emi_txns    = transactions[transactions["transaction_type"] == "EMI_PAYMENT"].copy()
inflow_txns = transactions[transactions["transaction_type"] == "BUSINESS_INFLOW"].copy()
outflow_txns= transactions[transactions["transaction_type"] == "BUSINESS_OUTFLOW"].copy()

# EMI payment behaviour
emi_features = emi_txns.groupby("borrower_id").agg(
    emi_on_time_count = ("status", lambda x: (x == "ON_TIME").sum()),
    emi_delayed_count = ("status", lambda x: (x == "DELAYED").sum()),
    emi_missed_count  = ("status", lambda x: (x == "MISSED").sum()),
    emi_total         = ("status", "count"),
).reset_index()
emi_features["emi_on_time_ratio"] = emi_features["emi_on_time_count"] / emi_features["emi_total"]
emi_features["emi_miss_ratio"]    = emi_features["emi_missed_count"]  / emi_features["emi_total"]

# Inflow volatility
inflow_agg = inflow_txns.groupby("borrower_id").agg(
    txn_inflow_mean = ("amount", "mean"),
    txn_inflow_std  = ("amount", "std"),
).reset_index()

# Outflow
outflow_agg = outflow_txns.groupby("borrower_id").agg(
    txn_outflow_mean = ("amount", "mean"),
).reset_index()

# Latest balance
latest_bal = (
    transactions.sort_values("timestamp")
    .groupby("borrower_id")["balance_after"].last()
    .reset_index().rename(columns={"balance_after": "latest_balance"})
)

txn_features = (
    emi_features
    .merge(inflow_agg,  on="borrower_id", how="left")
    .merge(outflow_agg, on="borrower_id", how="left")
    .merge(latest_bal,  on="borrower_id", how="left")
)
txn_features["cash_flow_strain"] = (
    txn_features["txn_outflow_mean"] /
    txn_features["txn_inflow_mean"].replace(0, np.nan)
).fillna(1.0)

print(f"    Transaction features built: {txn_features.shape[1]-1} features per borrower")

# ─────────────────────────────────────────────
# 3. MERGE EVERYTHING
# ─────────────────────────────────────────────
print("\n[3/6] Merging all feature layers...")

regional_extra = regional[["region", "npa_rate", "economic_stress_index", "peer_health_baseline"]]
df = (
    borrowers
    .merge(txn_features,    on="borrower_id", how="left")
    .merge(regional_extra,  on="region",      how="left")
)

# Label: at_risk if DPD > 30 OR missed >= 3
df["at_risk"] = ((df["days_past_due"] > 30) | (df["missed_payments_90d"] >= 3)).astype(int)

print(f"    At-risk borrowers: {df['at_risk'].sum()} / {len(df)} ({df['at_risk'].mean()*100:.1f}%)")

# ─────────────────────────────────────────────
# 4. FEATURE SELECTION
# ─────────────────────────────────────────────
FEATURE_COLS = [
    # Behavioural
    "repayment_consistency",
    "inflow_stability",
    "balance_trend",
    "missed_payments_90d",
    "days_past_due",
    "avg_monthly_inflow",
    "avg_monthly_outflow",
    # Contextual / regional
    "regional_stress_factor",
    "peer_score",
    "npa_rate",
    "economic_stress_index",
    # Transaction-derived
    "emi_on_time_ratio",
    "emi_miss_ratio",
    "txn_inflow_std",
    "cash_flow_strain",
    "latest_balance",
]

X_raw = df[FEATURE_COLS].fillna(df[FEATURE_COLS].median())
y     = df["at_risk"].values

# ─────────────────────────────────────────────
# 5. SPLIT + SCALE
# ─────────────────────────────────────────────
X_tr, X_te, y_tr, y_te = train_test_split(
    X_raw.values, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_tr_s = scaler.fit_transform(X_tr)
X_te_s  = scaler.transform(X_te)

print(f"\n    Train: {len(X_tr)} | Test: {len(X_te)}")

# ─────────────────────────────────────────────
# 6. RISKNET — Multi-Layer Perceptron
#    Architecture: 16 → 64 → 32 → 16 → 1
# ─────────────────────────────────────────────
print("\n[4/6] Training RiskNet (MLP)...")

model = MLPClassifier(
    hidden_layer_sizes=(64, 32, 16),
    activation="relu",
    solver="adam",
    learning_rate_init=0.001,
    max_iter=300,
    random_state=42,
    early_stopping=True,
    validation_fraction=0.15,
    n_iter_no_change=20,
    verbose=False,
)

model.fit(X_tr_s, y_tr)
print(f"    ✅ Converged in {model.n_iter_} iterations")

# ─────────────────────────────────────────────
# 7. EVALUATION
# ─────────────────────────────────────────────
print("\n[5/6] Evaluating...")

probs = model.predict_proba(X_te_s)[:, 1]
preds = (probs >= 0.5).astype(int)

auc    = roc_auc_score(y_te, probs)
acc    = accuracy_score(y_te, preds)
cm     = confusion_matrix(y_te, preds)
report = classification_report(y_te, preds, target_names=["Low Risk", "At Risk"])

print(f"\n    ROC-AUC Score : {auc:.4f}")
print(f"    Accuracy      : {acc:.4f}")
print(f"\n    Confusion Matrix:")
print(f"                  Pred Low  Pred High")
print(f"    Actual Low      {cm[0,0]:5d}     {cm[0,1]:5d}")
print(f"    Actual High     {cm[1,0]:5d}     {cm[1,1]:5d}")
print(f"\n    Classification Report:\n{report}")

# ─────────────────────────────────────────────
# 8. SCORE ALL 420 BORROWERS + EXPORT
# ─────────────────────────────────────────────
print("\n[6/6] Scoring all 420 borrowers...")

X_all_s   = scaler.transform(X_raw.values)
all_probs  = model.predict_proba(X_all_s)[:, 1]

def assign_tier(p):
    if p >= 0.70: return "CRITICAL"
    if p >= 0.50: return "HIGH"
    if p >= 0.30: return "MEDIUM"
    return "LOW"

def recommend_action(row):
    p      = row["risk_score"]
    dpd    = row["days_past_due"]
    missed = row["missed_payments_90d"]
    if p >= 0.70:
        return "Immediate outreach + restructure assessment"
    if p >= 0.50 and dpd > 20:
        return "Proactive call + repayment rescheduling"
    if p >= 0.50:
        return "Flag for relationship manager review"
    if missed >= 2:
        return "Early warning SMS + financial counselling"
    return "Monitor — routine check-in at next EMI cycle"

output = df[[
    "borrower_id", "name", "loan_scheme", "borrower_category",
    "region", "loan_amount", "outstanding_amount",
    "days_past_due", "missed_payments_90d",
    "repayment_consistency", "inflow_stability",
    "peer_score", "regional_stress_factor", "at_risk"
]].copy()

output["risk_score"]      = np.round(all_probs, 4)
output["risk_tier"]       = output["risk_score"].apply(assign_tier)
output["recovery_action"] = output.apply(recommend_action, axis=1)
output = output.sort_values("risk_score", ascending=False).reset_index(drop=True)
output.index = output.index + 1
output.index.name = "risk_rank"

output_path = "/mnt/user-data/outputs/satarksetu_risk_scores.csv"
output.to_csv(output_path)

print(f"\n    ── Risk Tier Distribution ──")
tier_counts = output["risk_tier"].value_counts()
for tier in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
    count = tier_counts.get(tier, 0)
    pct   = count / len(output) * 100
    bar   = "█" * int(pct / 2.5)
    print(f"    {tier:8s}  {count:3d} ({pct:4.1f}%)  {bar}")

print(f"\n    ── Top 10 Highest Risk Borrowers ──")
cols = ["borrower_id", "name", "region", "risk_score", "risk_tier", "recovery_action"]
print(output[cols].head(10).to_string())

print(f"\n    ✅ Output → {output_path}")
print("\n" + "=" * 60)
print("  Bandhan Pipeline Complete")
print("=" * 60)
