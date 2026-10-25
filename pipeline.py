"""
Bandhan — Feature Engineering
Transforms raw borrower + transaction + regional data into model input
"""

import numpy as np


FEATURES = [
    'repayment_consistency', 'inflow_stability', 'balance_trend',
    'missed_payments_90d', 'days_past_due',
    'txn_miss_rate', 'txn_delay_rate', 'txn_ontime_rate',
    'inflow_volatility', 'balance_trajectory',
    'emi_to_inflow_ratio', 'outstanding_to_loan', 'buffer_ratio',
    'inflow_outflow_gap',
    'regional_stress_factor', 'peer_score', 'peer_regional_gap',
    'npa_rate', 'economic_stress_index',
]


def engineer_features(borrower: dict, transactions: list, regional: dict) -> list:
    """
    Build the 19-feature vector for one borrower.

    Args:
        borrower    : dict of borrower row from Supabase
        transactions: list of transaction dicts for this borrower
        regional    : dict of regional context for borrower's region

    Returns:
        list of 19 floats ready for model input
    """

    # --- Transaction-derived features ---
    emi_txns = [t for t in transactions if t['transaction_type'] == 'EMI_PAYMENT']
    total    = len(emi_txns) if emi_txns else 1

    txn_miss_rate   = sum(1 for t in emi_txns if t['status'] == 'MISSED')  / total
    txn_delay_rate  = sum(1 for t in emi_txns if t['status'] == 'DELAYED') / total
    txn_ontime_rate = sum(1 for t in emi_txns if t['status'] == 'ON_TIME') / total

    inflow_txns = [t for t in transactions if t['transaction_type'] == 'BUSINESS_INFLOW']
    amounts     = [t['amount'] for t in inflow_txns]
    inflow_volatility = float(np.std(amounts)) if len(amounts) > 1 else 0.0

    sorted_txns       = sorted(transactions, key=lambda t: t['timestamp'])
    first_bal         = sorted_txns[0]['balance_after']  if sorted_txns else 0
    last_bal          = sorted_txns[-1]['balance_after'] if sorted_txns else 0
    balance_trajectory = (last_bal - first_bal) / (abs(first_bal) + 1)

    # --- Ratio features ---
    emi_to_inflow_ratio = borrower.get('emi_amount', 0) / (borrower.get('avg_monthly_inflow', 0) + 1)
    outstanding_to_loan = borrower.get('outstanding_amount', 0) / (borrower.get('loan_amount', 0) + 1)
    buffer_ratio        = borrower.get('current_balance', 0) / (borrower.get('emi_amount', 0) + 1)
    inflow_outflow_gap  = borrower.get('avg_monthly_inflow', 0) - borrower.get('avg_monthly_outflow', 0)

    # --- Contextual features ---
    peer_health_baseline = regional.get('peer_health_baseline', borrower.get('peer_score', 0))
    peer_regional_gap    = borrower.get('peer_score', 0) - peer_health_baseline

    features = [
        borrower.get('repayment_consistency', 0),
        borrower.get('inflow_stability', 0),
        borrower.get('balance_trend', 0),
        borrower.get('missed_payments_90d', 0),
        borrower.get('days_past_due', 0),
        txn_miss_rate,
        txn_delay_rate,
        txn_ontime_rate,
        inflow_volatility,
        balance_trajectory,
        emi_to_inflow_ratio,
        outstanding_to_loan,
        buffer_ratio,
        inflow_outflow_gap,
        borrower.get('regional_stress_factor', 0),
        borrower.get('peer_score', 0),
        peer_regional_gap,
        regional.get('npa_rate', 0),
        regional.get('economic_stress_index', 0),
    ]

    return [float(f) for f in features]


def compute_risk_score(borrower: dict, transactions: list, regional: dict) -> float:
    # EMI behaviour from transactions
    emi_txns = [t for t in transactions if t.get('transaction_type') == 'EMI_PAYMENT']
    total = len(emi_txns) if emi_txns else 1
    miss_rate = sum(1 for t in emi_txns if t.get('status') == 'MISSED') / total
    delay_rate = sum(1 for t in emi_txns if t.get('status') == 'DELAYED') / total

    def _val(v, default):
        if v is None:
            return default
        try:
            val = float(v)
            return default if np.isnan(val) else val
        except (ValueError, TypeError):
            return default

    # Core risk signal — weighted combination of real features
    repayment  = _val(borrower.get('repayment_consistency'), 0.8)
    missed     = _val(borrower.get('missed_payments_90d'), 0.0)
    dpd        = _val(borrower.get('days_past_due'), 0.0)
    peer       = _val(borrower.get('peer_score'), 80.0)
    stress     = _val(borrower.get('regional_stress_factor'), 0.5)
    inflow_st  = _val(borrower.get('inflow_stability'), 0.8)

    # Normalise days past due to 0-1
    dpd_norm = min(dpd / 90.0, 1.0)
    # Normalise missed payments to 0-1
    missed_norm = min(missed / 4.0, 1.0)
    # Peer score — lower is riskier, normalise inverted
    peer_norm = 1.0 - (peer / 100.0)

    # Weighted risk score
    risk = (
        missed_norm    * 0.30 +
        dpd_norm       * 0.25 +
        miss_rate      * 0.15 +
        delay_rate     * 0.10 +
        (1 - repayment)* 0.10 +
        stress         * 0.05 +
        peer_norm      * 0.03 +
        (1 - inflow_st)* 0.02
    )

    return round(float(min(max(risk, 0.0), 1.0)), 4)


def risk_band(probability: float) -> str:
    if probability >= 0.60:   return 'CRITICAL'
    elif probability >= 0.40: return 'HIGH'
    elif probability >= 0.20: return 'MODERATE'
    else:                     return 'LOW'


def recovery_action(probability: float) -> str:
    if probability >= 0.60:
        return 'Immediate Intervention: Restructuring / Legal Notice Review'
    elif probability >= 0.40:
        return 'Proactive Outreach: Restructure EMI / Offer Moratorium'
    elif probability >= 0.20:
        return 'Soft Alert: Relationship Manager Check-in'
    else:
        return 'Monitor: Standard Portfolio Review'

