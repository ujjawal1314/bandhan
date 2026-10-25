import os
import csv
import datetime
import pandas as pd
import streamlit as st
from audit_compliance_engine import audit_log

RESTRUCTURING_FILE = "restructuring_requests.csv"

class RecoveryPortalEngine:
    @staticmethod
    def init_restructuring_file():
        if not os.path.exists(RESTRUCTURING_FILE) or os.path.getsize(RESTRUCTURING_FILE) == 0:
            with open(RESTRUCTURING_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "request_id", "borrower_id", "borrower_name", "timestamp",
                    "reason", "employment_status", "business_status", "monthly_income",
                    "recovery_timeline", "requested_emi", "status", "admin_remarks"
                ])
                
            # Pre-populate a couple of requests for demo purposes
            mock_requests = [
                ("REQ-A92B1C", "BORR_00003", "Ananya Singh", "2026-07-06 14:30:15",
                 "Supply chain delays affected seasonal sales volume", "Self-Employed", "Active but Stressed", "85000",
                 "6 Months", "15000", "PENDING", "Reviewing regional sector relief scheme eligibility"),
                ("REQ-B83C2D", "BORR_00004", "Aarav Reddy", "2026-07-07 10:15:30",
                 "Temporary medical leave reduced active business capacity", "Salaried", "N/A", "45000",
                 "3 Months", "5000", "PENDING", "Waiting for medical certificate upload verification")
            ]
            with open(RESTRUCTURING_FILE, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for r in mock_requests:
                    writer.writerow(r)

    @staticmethod
    def submit_restructuring_request(
        borrower_id: str,
        borrower_name: str,
        reason: str,
        employment_status: str,
        business_status: str,
        monthly_income: float,
        recovery_timeline: str,
        requested_emi: float
    ) -> str:
        """Saves a borrower's credit restructuring request."""
        RecoveryPortalEngine.init_restructuring_file()
        import uuid
        request_id = f"REQ-{uuid.uuid4().hex[:6].upper()}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(RESTRUCTURING_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                request_id, borrower_id, borrower_name, timestamp,
                reason, employment_status, business_status, str(monthly_income),
                recovery_timeline, str(requested_emi), "PENDING", "N/A"
            ])
        return request_id

    @staticmethod
    def get_restructuring_requests() -> pd.DataFrame:
        """Returns all restructuring requests."""
        RecoveryPortalEngine.init_restructuring_file()
        try:
            df = pd.read_csv(RESTRUCTURING_FILE)
            return df
        except Exception:
            return pd.DataFrame(columns=[
                "request_id", "borrower_id", "borrower_name", "timestamp",
                "reason", "employment_status", "business_status", "monthly_income",
                "recovery_timeline", "requested_emi", "status", "admin_remarks"
            ])

    @staticmethod
    def update_restructuring_request(request_id: str, status: str, remarks: str) -> bool:
        """Updates the status and admin remarks of a restructuring request."""
        RecoveryPortalEngine.init_restructuring_file()
        try:
            df = pd.read_csv(RESTRUCTURING_FILE)
            idx = df[df["request_id"] == request_id].index
            if not idx.empty:
                df.at[idx[0], "status"] = status
                df.at[idx[0], "admin_remarks"] = remarks
                df.to_csv(RESTRUCTURING_FILE, index=False)
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def simulate_impact(borrower_id: str, payment_amount: float, detector) -> dict:
        """Simulates the dynamic credit health improvement before payment is submitted."""
        # 1. Fetch current analysis
        analysis = detector.analyze_borrower(borrower_id)
        curr_health = analysis.health_score
        curr_risk = analysis.risk_score
        curr_risk_level = analysis.risk_level
        
        # Fetch borrower details
        row = detector._borrower_row(borrower_id)
        outstanding = float(row["outstanding_amount"])
        emi = float(row["emi_amount"])
        dpd = float(row["days_past_due"])
        
        # 2. Simulate payment impacts
        sim_outstanding = max(0.0, outstanding - payment_amount)
        
        # Estimate DPD reduction based on how many EMIs they pay
        emis_paid = payment_amount / emi if emi > 0 else 0
        sim_dpd = max(0.0, dpd - (emis_paid * 30.0))
        
        # 3. Recalculate health
        dpd_diff = dpd - sim_dpd
        outstanding_ratio_improved = (outstanding - sim_outstanding) / max(outstanding, 1.0)
        
        # Health boost formula
        health_boost = (dpd_diff * 0.35) + (outstanding_ratio_improved * 18.0)
        if sim_outstanding == 0:
            sim_health = 100.0
        else:
            sim_health = min(98.0, curr_health + health_boost)
            
        sim_risk = 100.0 - sim_health
        
        # Classify risk level
        if sim_risk >= 70:
            sim_risk_level = "High Risk"
        elif sim_risk >= 45:
            sim_risk_level = "Moderate Risk"
        else:
            sim_risk_level = "Low Risk"
            
        # Recovery probability estimate
        curr_recovery_prob = int(curr_health * 0.95)
        sim_recovery_prob = int(sim_health * 0.95)
        
        return {
            "current_health": int(curr_health),
            "simulated_health": int(sim_health),
            "current_risk": int(curr_risk),
            "simulated_risk": int(sim_risk),
            "current_risk_level": curr_risk_level,
            "simulated_risk_level": sim_risk_level,
            "current_outstanding": outstanding,
            "simulated_outstanding": sim_outstanding,
            "current_recovery_prob": min(99, max(5, curr_recovery_prob)),
            "simulated_recovery_prob": min(99, max(5, sim_recovery_prob))
        }

    @staticmethod
    def process_payment(borrower_id: str, payment_amount: float, payment_type: str, detector) -> dict:
        """Processes the payment transaction, writes database updates, logs audits, and triggers notifications."""
        # 1. Calculate simulated final states
        impact = RecoveryPortalEngine.simulate_impact(borrower_id, payment_amount, detector)
        
        # 2. Update borrowers.csv state
        borrowers_df = pd.read_csv("borrowers.csv")
        idx = borrowers_df[borrowers_df["borrower_id"] == borrower_id].index
        if idx.empty:
            return {"status": "Failed", "message": "Borrower not found."}
            
        old_outstanding = float(borrowers_df.at[idx[0], "outstanding_amount"])
        old_dpd = float(borrowers_df.at[idx[0], "days_past_due"])
        
        new_outstanding = impact["simulated_outstanding"]
        emi = float(borrowers_df.at[idx[0], "emi_amount"])
        emis_paid = payment_amount / emi if emi > 0 else 0
        new_dpd = max(0.0, old_dpd - (emis_paid * 30.0))
        
        # Update details
        borrowers_df.at[idx[0], "outstanding_amount"] = new_outstanding
        borrowers_df.at[idx[0], "days_past_due"] = int(new_dpd)
        
        # Save back to CSV
        borrowers_df.to_csv("borrowers.csv", index=False)
        
        # 3. Append to loan_transactions.csv
        txns_df = pd.read_csv("loan_transactions.csv")
        import uuid
        txn_id = f"TXN_{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        new_txn = pd.DataFrame([{
            "transaction_id": txn_id,
            "borrower_id": borrower_id,
            "amount": payment_amount,
            "transaction_type": "EMI_PAYMENT",
            "status": "SUCCESS",
            "timestamp": now_str,
            "balance_after": new_outstanding
        }])
        
        txns_df = pd.concat([txns_df, new_txn], ignore_index=True)
        txns_df.to_csv("loan_transactions.csv", index=False)
        
        # 4. Flush detector cache to trigger full GNN re-analysis on dashboard reload
        detector.analysis_cache.pop(borrower_id, None)
        detector.base_health_cache.pop(borrower_id, None)
        # Re-compute
        detector.borrower_df = pd.read_csv("borrowers.csv")
        detector.txn_df = pd.read_csv("loan_transactions.csv")
        detector.borrower_lookup = detector.borrower_df.set_index("borrower_id")
        detector.txn_grouped = dict(tuple(detector.txn_df.groupby("borrower_id")))
        detector.build_graph()
        
        # 5. Log compliance audit log
        audit_log(
            category="Recovery Operations",
            action="Payment Completed",
            borrower_id=borrower_id,
            previous_value=f"Outstanding: ₹{old_outstanding:,.2f}, DPD: {int(old_dpd)}",
            new_value=f"Outstanding: ₹{new_outstanding:,.2f}, DPD: {int(new_dpd)}",
            reason=f"Repayment Gateway type: {payment_type}. Recalculated Health: {impact['simulated_health']}/100"
        )
        
        # 6. Dispatch confirmations via SMS/Email templates
        from communication_engine import send_otp_email, send_otp_sms
        email = str(borrowers_df.at[idx[0], "email"])
        mobile = str(borrowers_df.at[idx[0], "mobile_number"])
        
        confirm_subject = "Bandhan Bank - Payment Receipt Confirmation"
        confirm_body = (
            f"Dear Customer,\n\n"
            f"We have successfully received your repayment transaction of Rs {payment_amount:,.2f} via Razorpay Checkout.\n\n"
            f"Transaction ID: {txn_id}\n"
            f"Updated Outstanding Loan Dues: Rs {new_outstanding:,.2f}\n"
            f"Updated Days Past Due: {int(new_dpd)}\n\n"
            f"Your credit profile health score has improved to {impact['simulated_health']}/100 ({impact['simulated_risk_level']}). "
            f"Keep maintaining regular repayments to achieve a healthy credit profile!\n\n"
            f"Best regards,\n"
            f"Bandhan Bank Loan Servicing Division"
        )
        # Send Email & SMS confirmations (Simulated or SMTP/Twilio as configured)
        from communication_engine import CommunicationService
        CommunicationService.send_email(email, confirm_subject, confirm_body)
        CommunicationService.send_sms(mobile, f"Bandhan Bank: Payment of Rs {payment_amount:,.2f} successful. Txn ID: {txn_id}. Outstanding: Rs {new_outstanding:,.2f}. DPD: {int(new_dpd)}.")
        
        return {
            "status": "Success",
            "txn_id": txn_id,
            "timestamp": now_str,
            "old_outstanding": old_outstanding,
            "new_outstanding": new_outstanding,
            "old_health": impact["current_health"],
            "new_health": impact["simulated_health"],
            "old_risk_level": impact["current_risk_level"],
            "new_risk_level": impact["simulated_risk_level"],
            "old_dpd": old_dpd,
            "new_dpd": new_dpd,
            "recovery_prob_old": impact["current_recovery_prob"],
            "recovery_prob_new": impact["simulated_recovery_prob"]
        }
