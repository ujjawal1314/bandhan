import os
import csv
import uuid
import datetime
import pandas as pd
import streamlit as st

AUDIT_LOGS_FILE = "audit_compliance_logs.csv"

def render_safe_html(content: str) -> None:
    """Render HTML safely without triggering Markdown indented code block parsing."""
    clean = "\n".join(line.strip() for line in content.splitlines() if line.strip())
    if hasattr(st, "html"):
        st.html(clean)
    else:
        st.markdown(clean, unsafe_allow_html=True)


class AuditComplianceService:
    @staticmethod
    def get_severity(category: str, action: str, risk_score: str = "N/A") -> str:
        """Classifies severity based on category, action type, and optional risk score."""
        action_upper = action.upper()
        
        # 1. Critical Actions
        if (
            "LOGIN" in action_upper and "ADMIN" in action_upper
        ) or "RESTRUCTURING APPROVED" in action_upper or "STATUS CHANGED" in action_upper:
            return "🔴 Critical Action"
        
        # Handle Risk Score Severity
        if "RISK SCORE" in action_upper or "CBHM" in action_upper:
            try:
                score = int(float(risk_score))
                if score >= 70:
                    return "🔴 Critical Action"
                elif score >= 45:
                    return "🟠 Medium Risk"
            except Exception:
                pass
        
        # 2. Medium Risk Actions
        if (
            "RESTRUCTURING RECOMMENDED" in action_upper 
            or "PASSWORD RESET" in action_upper 
            or "FLAGGED" in action_upper 
            or "ROLE CHANGED" in action_upper
        ):
            return "🟠 Medium Risk"
            
        # 3. Warnings
        if (
            "FAILED" in action_upper 
            or "WARNING" in action_upper 
            or "SMS" in action_upper 
            or "WHATSAPP" in action_upper 
            or "SCHEDULED" in action_upper 
            or "COMPLETED" in action_upper 
            or "UNFLAGGED" in action_upper
        ):
            return "🟡 Warning"
            
        # 4. Information
        return "🟢 Information"

    @staticmethod
    def init_file():
        """Initializes the immutable CSV log file. Pre-populates mock compliance records if empty."""
        columns = [
            "log_id", "timestamp", "user_id", "user_name", "user_role", 
            "branch", "borrower_id", "borrower_name", "action_category", 
            "action_performed", "previous_value", "new_value", "reason_for_change", 
            "ai_confidence", "ip_address", "device_info", "session_id", "severity"
        ]
        
        if not os.path.exists(AUDIT_LOGS_FILE) or os.path.getsize(AUDIT_LOGS_FILE) == 0:
            with open(AUDIT_LOGS_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
            
            # Pre-populate mock logs for BORR_00001 (Rahul Singh) & BORR_00002 (Ravi Saha) to demonstrate visual timelines
            mock_records = [
                # Rahul Singh (BORR_00001) Timeline
                ("AUD-A938C21B", "2026-06-01 10:15:30", "system", "System Scheduler", "SYSTEM", "Shimla Mall Road Branch", 
                 "BORR_00001", "Rahul Singh", "Administration", "Borrower Created", "N/A", "ACTIVE", 
                 "System auto-import from core banking ledger", "N/A", "127.0.0.1", "System Daemon Process", "SESS-SYSTEM0001", "🟢 Information"),
                
                ("AUD-B831F2A8", "2026-06-10 14:20:11", "system", "CBHM Engine", "SYSTEM", "Shimla Mall Road Branch", 
                 "BORR_00001", "Rahul Singh", "AI & Risk Engine", "CBHM Risk Score Generated", "100", "84", 
                 "Monthly batch run GNN analysis", "0.92", "127.0.0.1", "Bandhan CBHM v1.4", "SESS-SYSTEM0001", "🟢 Information"),
                 
                ("AUD-C927D4E3", "2026-06-20 09:30:45", "system", "CBHM Engine", "SYSTEM", "Shimla Mall Road Branch", 
                 "BORR_00001", "Rahul Singh", "AI & Risk Engine", "Risk Score Updated", "16", "40", 
                 "Repayment consistency metric decline detected", "0.88", "127.0.0.1", "Bandhan CBHM v1.4", "SESS-SYSTEM0001", "🟡 Warning"),
                 
                ("AUD-D826E2F4", "2026-06-25 11:42:10", "jyoti", "Jyoti", "ADMIN", "Mumbai Regional Branch", 
                 "BORR_00001", "Rahul Singh", "Recovery Operations", "Warning Email Sent", "N/A", "Email:Sent", 
                 "Automated reminder for 40 DPD outstanding dues", "N/A", "192.168.1.54", "MacBook Chrome", "SESS-JYOTI4491", "🟡 Warning"),
                 
                ("AUD-E715C3D2", "2026-07-01 16:10:05", "jyoti", "Jyoti", "ADMIN", "Mumbai Regional Branch", 
                 "BORR_00001", "Rahul Singh", "Recovery Operations", "Branch Visit Scheduled", "N/A", "Scheduled", 
                 "Customer missed repayment meeting contact", "N/A", "192.168.1.54", "MacBook Chrome", "SESS-JYOTI4491", "🟡 Warning"),
                 
                ("AUD-F614A5C1", "2026-07-04 13:05:00", "jyoti", "Jyoti", "ADMIN", "Mumbai Regional Branch", 
                 "BORR_00001", "Rahul Singh", "Recovery Operations", "Loan Restructuring Recommended", "N/A", "Offered", 
                 "Customer cited cash flow stress due to regional market slump", "0.85", "192.168.1.54", "MacBook Chrome", "SESS-JYOTI4491", "🟠 Medium Risk"),
                 
                ("AUD-G503A4B2", "2026-07-08 09:12:14", "system", "CBHM Engine", "SYSTEM", "Shimla Mall Road Branch", 
                 "BORR_00001", "Rahul Singh", "AI & Risk Engine", "Risk Score Updated", "40", "15", 
                 "Restructuring collateral approved, risk re-evaluated downward", "0.94", "127.0.0.1", "Bandhan CBHM v1.4", "SESS-SYSTEM0001", "🟢 Information"),

                # Ravi Saha (BORR_00002) Timeline
                ("AUD-H492F5C9", "2026-06-03 11:22:15", "system", "System Scheduler", "SYSTEM", "Srinagar Residency Road Branch", 
                 "BORR_00002", "Ravi Saha", "Administration", "Borrower Created", "N/A", "ACTIVE", 
                 "System auto-import from core banking ledger", "N/A", "127.0.0.1", "System Daemon Process", "SESS-SYSTEM0001", "🟢 Information"),
                
                ("AUD-I381E4A8", "2026-06-12 15:45:00", "system", "CBHM Engine", "SYSTEM", "Srinagar Residency Road Branch", 
                 "BORR_00002", "Ravi Saha", "AI & Risk Engine", "CBHM Risk Score Generated", "100", "75", 
                 "Monthly batch run GNN analysis", "0.89", "127.0.0.1", "Bandhan CBHM v1.4", "SESS-SYSTEM0001", "🔴 Critical Action"),

                ("AUD-J270D3E7", "2026-06-15 09:11:10", "system", "CBHM Engine", "SYSTEM", "Srinagar Residency Road Branch", 
                 "BORR_00002", "Ravi Saha", "AI & Risk Engine", "Risk Score Updated", "25", "70", 
                 "Days Past Due increased to 27", "0.91", "127.0.0.1", "Bandhan CBHM v1.4", "SESS-SYSTEM0001", "🔴 Critical Action"),

                ("AUD-K169C2B6", "2026-06-18 10:20:15", "sumedha", "Sumedha", "ADMIN", "Mumbai Regional Branch", 
                 "BORR_00002", "Ravi Saha", "Recovery Operations", "SMS Reminder Sent", "N/A", "SMS:Sent", 
                 "Proactive escalation text warning", "N/A", "192.168.1.102", "Windows Edge", "SESS-SUMEDHA991", "🟡 Warning"),

                ("AUD-L058B1A5", "2026-06-25 14:32:00", "sumedha", "Sumedha", "ADMIN", "Mumbai Regional Branch", 
                 "BORR_00002", "Ravi Saha", "Recovery Operations", "Branch Visit Scheduled", "N/A", "Scheduled", 
                 "Schedule direct visit from local recovery officer", "N/A", "192.168.1.102", "Windows Edge", "SESS-SUMEDHA991", "🟡 Warning"),
                 
                ("AUD-M947A0C4", "2026-07-02 11:10:00", "sumedha", "Sumedha", "ADMIN", "Mumbai Regional Branch", 
                 "BORR_00002", "Ravi Saha", "Recovery Operations", "Field Visit Completed", "N/A", "Visited", 
                 "Officer verified stock depletion, restructuring suggested", "N/A", "192.168.1.102", "Windows Edge", "SESS-SUMEDHA991", "🟡 Warning"),

                ("AUD-N836Z9Y3", "2026-07-06 10:00:00", "sumedha", "Sumedha", "ADMIN", "Mumbai Regional Branch", 
                 "BORR_00002", "Ravi Saha", "Recovery Operations", "Loan Restructuring Recommended", "N/A", "Offered", 
                 "Submitted to zonal manager for collateral adjustments", "0.87", "192.168.1.102", "Windows Edge", "SESS-SUMEDHA991", "🟠 Medium Risk"),

                # Administrative mock entries
                ("AUD-Z001A001", "2026-07-08 09:30:00", "ujjwal", "Ujjwal", "ADMIN", "Jaipur Corporate Office", 
                 "N/A", "N/A", "Administration", "System Settings Updated", "SMTP_Mode=Sandbox", "SMTP_Mode=Production", 
                 "Configuring secure gateway credentials", "N/A", "192.168.1.105", "MacBook Chrome", "SESS-UJJWAL192", "🟢 Information"),
                 
                ("AUD-Z002B002", "2026-07-08 09:32:15", "ujjwal", "Ujjwal", "ADMIN", "Jaipur Corporate Office", 
                 "BORR_00003", "Ananya Singh", "Administration", "Borrower Flagged", "ACTIVE", "SUPPORT_REQUIRED", 
                 "Dashboard manual marking by director review", "N/A", "192.168.1.105", "MacBook Chrome", "SESS-UJJWAL192", "🟠 Medium Risk")
            ]
            
            with open(AUDIT_LOGS_FILE, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for r in mock_records:
                    writer.writerow(r)

    @staticmethod
    def log_event(
        user_id: str,
        user_name: str,
        user_role: str,
        action_category: str,
        action_performed: str,
        branch: str = "N/A",
        borrower_id: str = "N/A",
        borrower_name: str = "N/A",
        previous_value: str = "N/A",
        new_value: str = "N/A",
        reason_for_change: str = "N/A",
        ai_confidence: str = "N/A",
        ip_address: str = "127.0.0.1",
        device_info: str = "Unknown Device",
        session_id: str = "N/A"
    ) -> str:
        """Appends an immutable audit event entry."""
        AuditComplianceService.init_file()
        log_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        severity = AuditComplianceService.get_severity(action_category, action_performed, new_value)
        
        with open(AUDIT_LOGS_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                log_id, timestamp, user_id, user_name, user_role,
                branch, borrower_id, borrower_name, action_category,
                action_performed, previous_value, new_value, reason_for_change,
                ai_confidence, ip_address, device_info, session_id, severity
            ])
        return log_id

    @staticmethod
    def get_logs() -> pd.DataFrame:
        """Returns all audit logs from the immutable CSV as a DataFrame sorted descending by time."""
        AuditComplianceService.init_file()
        try:
            df = pd.read_csv(AUDIT_LOGS_FILE)
            if df.empty:
                return df
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp", ascending=False)
            df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
            return df
        except Exception:
            return pd.DataFrame(columns=[
                "log_id", "timestamp", "user_id", "user_name", "user_role", 
                "branch", "borrower_id", "borrower_name", "action_category", 
                "action_performed", "previous_value", "new_value", "reason_for_change", 
                "ai_confidence", "ip_address", "device_info", "session_id", "severity"
            ])


def get_client_info():
    """Extracts client IP and device user-agent from Streamlit context headers with fallbacks."""
    try:
        headers = st.context.headers
        ip = headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]
        device = headers.get("User-Agent", "MacBook / Chrome Browser")
    except Exception:
        ip = "192.168.1.105"
        device = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    return ip, device


def audit_log(
    category: str,
    action: str,
    borrower_id: str = None,
    previous_value: str = None,
    new_value: str = None,
    reason: str = None,
    ai_confidence: str = None
):
    """Automatically resolves current session state and appends a compliance audit log."""
    user_id = "system"
    user_name = "System Scheduler"
    user_role = "SYSTEM"
    branch = "N/A"
    
    # 1. Resolve active user from session state
    if st.session_state.get("admin_authenticated"):
        user_id = st.session_state.get("admin_username", "admin")
        user_role = "ADMIN"
        
        # Admin mappings
        admin_meta = {
            "ujjwal": ("Ujjwal Singh", "Jaipur MI Road Branch"),
            "sumedha": ("Sumedha", "Mumbai Main Branch"),
            "jyoti": ("Jyoti", "Shimla Mall Road Branch")
        }
        meta = admin_meta.get(user_id.lower(), (user_id.title(), "Mumbai Main Branch"))
        user_name, branch = meta
        
    elif st.session_state.get("borrower_authenticated"):
        user_id = st.session_state.get("borrower_id", "borrower")
        user_role = "BORROWER"
        
        # Load borrower details from CSV
        try:
            borrowers = pd.read_csv("borrowers.csv")
            row = borrowers[borrowers["borrower_id"] == user_id]
            if not row.empty:
                user_name = str(row.iloc[0]["name"])
                branch = str(row.iloc[0]["branch"])
            else:
                user_name = f"Borrower {user_id}"
                branch = "N/A"
        except Exception:
            user_name = f"Borrower {user_id}"
            branch = "N/A"
            
    # 2. Resolve affected borrower name
    borrower_name = "N/A"
    if borrower_id and borrower_id != "N/A":
        try:
            borrowers = pd.read_csv("borrowers.csv")
            row = borrowers[borrowers["borrower_id"] == borrower_id]
            if not row.empty:
                borrower_name = str(row.iloc[0]["name"])
        except Exception:
            pass
            
    # 3. Resolve client connection details
    ip, device = get_client_info()
    
    # 4. Resolve session UUID
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"SESS-{uuid.uuid4().hex[:12].upper()}"
    session_id = st.session_state.session_id
    
    # 5. Append compliance log
    AuditComplianceService.log_event(
        user_id=user_id,
        user_name=user_name,
        user_role=user_role,
        branch=branch,
        borrower_id=borrower_id or "N/A",
        borrower_name=borrower_name or "N/A",
        action_category=category,
        action_performed=action,
        previous_value=str(previous_value) if previous_value is not None else "N/A",
        new_value=str(new_value) if new_value is not None else "N/A",
        reason_for_change=reason or "N/A",
        ai_confidence=str(ai_confidence) if ai_confidence is not None else "N/A",
        ip_address=ip,
        device_info=device,
        session_id=session_id
    )


def render_audit_compliance_center():
    """Renders the complete visual Audit & Compliance page inside the Admin Dashboard."""
    render_safe_html(
        """
        <div style="background: rgba(255,255,255,0.5);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.8);
            border-radius: 24px;
            padding: 24px 28px;
            margin-bottom: 24px;">
            <h2 style="margin:0 0 8px 0; color:#1c1c1e;">
                📋 Audit & Compliance Center
            </h2>
            <p style="margin:0; color:#48484a; font-weight:500;">
                Immutable append-only system logs, regulatory compliance tracking, and AI decision explainability audits.
            </p>
        </div>
        """
    )
    
    # Load all logs
    df = AuditComplianceService.get_logs()
    
    if df.empty:
        st.warning("No audit logs found. Please trigger some activity in the system.")
        return
        
    # ─────────────────────────────────────────────
    # SUMMARY CARDS
    # ─────────────────────────────────────────────
    # 1. Total logs today
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    total_today = len(df[df["timestamp"].astype(str).str.startswith(today_str)])
    
    # 2. High risk actions
    high_risk_actions = len(df[df["severity"].isin(["🔴 Critical Action", "🟠 Medium Risk"])])
    
    # 3. Failed login attempts
    failed_logins = len(df[df["action_performed"].astype(str).str.contains("failed login", case=False, na=False)])
    
    # 4. Communications sent
    comms_sent = len(df[
        (df["action_category"] == "Recovery Operations") & 
        (df["action_performed"].astype(str).str.contains("Sent", case=False, na=False))
    ])
    
    # 5. AI Decisions Generated
    ai_decisions = len(df[
        df["action_performed"].isin([
            "CBHM Risk Score Generated", 
            "Risk Score Updated", 
            "AI Recommendation Generated", 
            "Network Risk Recalculated"
        ])
    ])
    
    def render_metric_card(label: str, value: int, theme: str) -> str:
        themes = {
            "red": ("linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%)", "#991b1b"),
            "orange": ("linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%)", "#c2410c"),
            "green": ("linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)", "#166534"),
            "blue": ("linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%)", "#0369a1"),
            "purple": ("linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%)", "#6b21a8")
        }
        bg, text_color = themes.get(theme, ("linear-gradient(135deg, #ffffff 0%, #f3f4f6 100%)", "#1c1c1e"))
        return f"""
        <div style="background: {bg}; border: 1px solid rgba(0,0,0,0.06); border-radius: 18px; padding: 18px; min-height: 120px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 10px 20px rgba(0,0,0,0.015);">
            <span style="font-size:0.75rem; text-transform:uppercase; color:#636366; font-weight:700; letter-spacing:1px; line-height:1.2;">{label}</span>
            <div style="font-size: 2rem; font-weight: 800; color: {text_color}; margin-top: 8px;">{value}</div>
        </div>
        """
        
    card_cols = st.columns(5)
    with card_cols[0]:
        render_safe_html(render_metric_card("Total Logs Today", total_today, "blue"))
    with card_cols[1]:
        render_safe_html(render_metric_card("High-Risk Actions", high_risk_actions, "red"))
    with card_cols[2]:
        render_safe_html(render_metric_card("Failed Login Attempts", failed_logins, "orange"))
    with card_cols[3]:
        render_safe_html(render_metric_card("Communications Sent", comms_sent, "green"))
    with card_cols[4]:
        render_safe_html(render_metric_card("AI Decisions", ai_decisions, "purple"))
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ─────────────────────────────────────────────
    # TIMELINE VIEW (Visual Borrower Lifecycle)
    # ─────────────────────────────────────────────
    st.markdown("### 🕒 Borrower Lifecycle Timeline")
    st.markdown("Chronological history trace showing the progression of a borrower's credit health lifecycle.")
    
    # Get borrowers who have logs
    valid_mask = df["borrower_id"].notna() & (df["borrower_id"] != "N/A") & (df["borrower_id"].astype(str) != "nan")
    timeline_borrowers = df[valid_mask]["borrower_id"].unique()
    
    if len(timeline_borrowers) > 0:
        borr_list = list(timeline_borrowers)
        selected_borr = st.selectbox("Select Borrower to View Lifecycle", borr_list, key="timeline_borrower_select")
        
        # Get logs for this borrower sorted ASCENDING
        borr_logs = df[df["borrower_id"] == selected_borr].copy()
        borr_logs["timestamp"] = pd.to_datetime(borr_logs["timestamp"])
        borr_logs = borr_logs.sort_values("timestamp", ascending=True)
        
        # Render timeline
        timeline_html = """
        <div style="position: relative; padding-left: 36px; border-left: 2px solid #DFD7CC; margin: 24px 0 24px 16px;">
        """
        for _, row in borr_logs.iterrows():
            severity_str = str(row["severity"])
            dot_color = "#10b981" # Green info
            if "Critical" in severity_str:
                dot_color = "#ef4444" # Red
            elif "Medium" in severity_str:
                dot_color = "#f97316" # Orange
            elif "Warning" in severity_str:
                dot_color = "#f59e0b" # Yellow
                
            time_str = row["timestamp"].strftime("%Y-%m-%d %I:%M %p")
            
            prev_val = str(row.get('previous_value', '')).strip()
            new_val = str(row.get('new_value', '')).strip()
            prev_html = ""
            if prev_val and prev_val not in ["N/A", "nan", "None", ""] and pd.notna(row.get('previous_value')):
                new_display = new_val if new_val not in ["nan", "None"] else ""
                prev_html = f"<strong>Prev Value:</strong> <span style='color:#ef4444'>{prev_val}</span> &rarr; <strong>New Value:</strong> <span style='color:#10b981'>{new_display}</span><br>"
            
            ai_exp_html = ""
            if pd.notna(row.get('ai_confidence')) and str(row.get('ai_confidence')) not in ["N/A", "nan"] and "Score" in str(row.get('reason_for_change', '')):
                ai_exp_html = f"<div style='font-size:0.83rem; color:#6B3F23; margin-top:6px; font-weight:700;'>🧠 AI Decision Explainability Matrix: {row['reason_for_change']} (Confidence: {row['ai_confidence']})</div>"

            timeline_html += f"""
            <div style="position: relative; margin-bottom: 24px;">
                <div style="position: absolute; left: -46px; top: 4px; width: 18px; height: 18px; border-radius: 50%; background: {dot_color}; border: 3px solid #FAF7F2; box-shadow: 0 0 0 2px {dot_color}80;"></div>
                <div style="font-size: 0.76rem; color: #8C7B70; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">{time_str}</div>
                <div style="font-size: 1.02rem; font-weight: 700; color: #2C1E16; margin-top: 2px;">{row['action_performed']}</div>
                <div style="font-size: 0.88rem; color: #4A3E36; margin-top: 6px; line-height: 1.5; background: #FFFFFF; border: 1px solid #DFD7CC; border-radius: 10px; padding: 12px 16px; box-shadow: 0 1px 3px rgba(44, 30, 22, 0.04);">
                    <strong>User:</strong> {row['user_name']} ({row['user_role']}) &nbsp;|&nbsp; <strong>Branch:</strong> {row['branch']}<br>
                    <strong>Reason/Details:</strong> {row['reason_for_change']}<br>
                    {prev_html}
                    {ai_exp_html}
                </div>
            </div>
            """
        timeline_html += "</div>"
        render_safe_html(timeline_html)
    else:
        st.info("Perform borrower actions to generate lifecycle timeline views.")
        
    st.markdown("<br><hr style='border: 0; height: 1px; background: rgba(0,0,0,0.08);'><br>", unsafe_allow_html=True)
    
    # ─────────────────────────────────────────────
    # AUDIT LOGS TABLE & FILTERS
    # ─────────────────────────────────────────────
    st.markdown("### 📋 Historical Compliance Audit Logs")
    
    # Filter expander
    with st.expander("🔍 Filter Audit Trail", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        
        with f_col1:
            # Date Range
            min_date = pd.to_datetime(df["timestamp"]).min().date() if not df.empty else datetime.date.today()
            start_d = st.date_input("Start Date", min_date)
            end_d = st.date_input("End Date", datetime.date.today())
            
        with f_col2:
            # Action category
            cats = ["All"] + list(df["action_category"].dropna().unique())
            sel_cat = st.selectbox("Action Category", cats)
            
            # Severity
            sevs = ["All"] + list(df["severity"].dropna().unique())
            sel_sev = st.selectbox("Severity", sevs)
            
        with f_col3:
            # Branch
            branches = ["All"] + list(df["branch"].dropna().unique())
            sel_branch = st.selectbox("Filter Branch", branches)
            
            # User
            users = ["All"] + list(df["user_id"].dropna().unique())
            sel_user = st.selectbox("Filter User / Executor", users)
            
        with f_col4:
            # Affected Borrower ID
            borrs = ["All"] + list(df[df["borrower_id"] != "N/A"]["borrower_id"].dropna().unique())
            sel_borr_id = st.selectbox("Filter Borrower ID", borrs)
            
            # Success/Failure Status
            sel_status = st.selectbox("Outcome Status", ["All", "Success Only", "Failures Only"])
            
    # Search box
    search_q = st.text_input("🔍 Search Logs (User, Action Performed, Reason, Session ID, IP address...)", placeholder="Search keyword...")
    
    # Apply filtering
    filtered_df = df.copy()
    filtered_df["timestamp_parsed"] = pd.to_datetime(filtered_df["timestamp"])
    
    # Date filter
    filtered_df = filtered_df[
        (filtered_df["timestamp_parsed"].dt.date >= start_d) & 
        (filtered_df["timestamp_parsed"].dt.date <= end_d)
    ]
    
    # Category filter
    if sel_cat != "All":
        filtered_df = filtered_df[filtered_df["action_category"] == sel_cat]
        
    # Severity filter
    if sel_sev != "All":
        filtered_df = filtered_df[filtered_df["severity"] == sel_sev]
        
    # Branch filter
    if sel_branch != "All":
        filtered_df = filtered_df[filtered_df["branch"] == sel_branch]
        
    # User filter
    if sel_user != "All":
        filtered_df = filtered_df[filtered_df["user_id"] == sel_user]
        
    # Borrower filter
    if sel_borr_id != "All":
        filtered_df = filtered_df[filtered_df["borrower_id"] == sel_borr_id]
        
    # Status outcome filter
    if sel_status == "Success Only":
        filtered_df = filtered_df[
            filtered_df["action_performed"].astype(str).str.contains("failed", case=False).apply(lambda x: not x) &
            filtered_df["new_value"].astype(str).str.contains("Failed", case=False).apply(lambda x: not x)
        ]
    elif sel_status == "Failures Only":
        filtered_df = filtered_df[
            filtered_df["action_performed"].astype(str).str.contains("failed", case=False) |
            filtered_df["new_value"].astype(str).str.contains("Failed", case=False) |
            filtered_df["reason_for_change"].astype(str).str.contains("failed", case=False)
        ]
        
    # Text Search filter
    if search_q:
        q = search_q.lower()
        filtered_df = filtered_df[
            filtered_df["user_id"].astype(str).str.lower().str.contains(q) |
            filtered_df["user_name"].astype(str).str.lower().str.contains(q) |
            filtered_df["action_performed"].astype(str).str.lower().str.contains(q) |
            filtered_df["reason_for_change"].astype(str).str.lower().str.contains(q) |
            filtered_df["borrower_id"].astype(str).str.lower().str.contains(q) |
            filtered_df["borrower_name"].astype(str).str.lower().str.contains(q) |
            filtered_df["session_id"].astype(str).str.lower().str.contains(q) |
            filtered_df["ip_address"].astype(str).str.lower().str.contains(q)
        ]
        
    if filtered_df.empty:
        st.info("No logs matched the selected filter criteria.")
        return
        
    # Export Panel
    col_exp1, col_exp2, _ = st.columns([1, 1, 2])
    
    with col_exp1:
        # Export to CSV
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Filtered Logs to CSV",
            data=csv_data,
            file_name=f"bandhan_audit_trail_{datetime.date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    with col_exp2:
        # Export to HTML Printable (Save as PDF)
        html_rows = ""
        for _, row in filtered_df.iterrows():
            html_rows += f"""
            <tr>
                <td>{row['timestamp']}</td>
                <td>{row['user_name']} ({row['user_role']})</td>
                <td>{row['action_performed']}</td>
                <td>{row['borrower_name']} ({row['borrower_id']})</td>
                <td>{row['branch']}</td>
                <td>{row['severity']}</td>
                <td>{row['new_value']}</td>
            </tr>
            """
            
        html_report = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Bandhan Audit & Compliance Report</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; color: #1c1c1e; }}
                h1 {{ font-size: 24px; font-weight: 800; margin-bottom: 5px; }}
                p {{ color: #8e8e93; font-size: 14px; margin-bottom: 20px; }}
                table {{ border-collapse: collapse; width: 100%; font-size: 12px; margin-top: 20px; }}
                th, td {{ border: 1px solid #e5e5ea; padding: 10px 12px; text-align: left; }}
                th {{ background-color: #f2f2f7; font-weight: 700; color: #1c1c1e; }}
                tr:nth-child(even) {{ background-color: #fafafa; }}
            </style>
        </head>
        <body>
            <h1>Bandhan Audit & Compliance Report</h1>
            <p><strong>Date Generated:</strong> {datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")} | <strong>Logs Count:</strong> {len(filtered_df)}</p>
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>User / Executor</th>
                        <th>Action</th>
                        <th>Borrower / Target</th>
                        <th>Branch</th>
                        <th>Severity</th>
                        <th>Status / Outcome</th>
                    </tr>
                </thead>
                <tbody>
                    {html_rows}
                </tbody>
            </table>
        </body>
        </html>
        """
        st.download_button(
            label="📄 Export to Printable HTML (Save as PDF)",
            data=html_report.encode('utf-8'),
            file_name=f"bandhan_audit_compliance_report_{datetime.date.today()}.html",
            mime="text/html",
            use_container_width=True
        )
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ─────────────────────────────────────────────
    # AUDIT TABLE DISPLAY
    # ─────────────────────────────────────────────
    # Display Columns: Timestamp, User, Action, Borrower, Branch, Severity, Status
    display_df = filtered_df[[
        "timestamp", "user_name", "action_performed", "borrower_name", "branch", "severity", "new_value"
    ]].rename(columns={
        "timestamp": "Timestamp",
        "user_name": "User",
        "action_performed": "Action",
        "borrower_name": "Borrower",
        "branch": "Branch",
        "severity": "Severity",
        "new_value": "Status / Outcome"
    })
    
    # Pagination
    page_size = 10
    total_items = len(display_df)
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    
    col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
    with col_pag1:
        page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1, key="audit_page_num")
    with col_pag2:
        st.markdown(f"<div style='text-align: center; padding-top: 30px; font-weight: 600; color: #8e8e93;'>Showing {(page_num-1)*page_size + 1} - {min(total_items, page_num*page_size)} of {total_items} entries</div>", unsafe_allow_html=True)
        
    start_idx = (page_num - 1) * page_size
    end_idx = start_idx + page_size
    
    # Render table
    from dashboard_enhanced import render_glass_table
    render_glass_table(display_df.iloc[start_idx:end_idx], max_height=480)
