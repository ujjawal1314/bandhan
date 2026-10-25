from __future__ import annotations

import os
import csv
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd
import requests

LOGS_FILE = "communication_logs.csv"

def get_branch_details(branch_name: str) -> dict:
    """Dynamically generates consistent contact details for any branch name."""
    prefix = branch_name.lower().replace(" branch", "").replace(" ", ".")
    email = f"manager.{prefix}@bandhanbank.co.in"
    # Create a stable, deterministic phone number based on branch name hash
    h = abs(hash(branch_name))
    phone = f"+91 {22 + (h % 80):02d} {2000000 + (h % 7000000):07d}"
    return {"phone": phone, "email": email}


class InHouseAIReasoningEngine:
    """Bandhan in-house local AI reasoning engine for message personalization."""

    @staticmethod
    def generate_message(
        name: str,
        loan_scheme: str,
        outstanding_amount: float,
        health_score: float,
        risk_level: str,
        days_past_due: int,
        last_emi_date: str,
        branch: str,
        message_type: str,
        custom_body: str = ""
    ) -> str:
        branch_meta = get_branch_details(branch)
        phone = branch_meta["phone"]
        email = branch_meta["email"]
        outstanding_str = f"Rs {outstanding_amount:,.2f}"

        # 1. Compute dynamic due date based on DPD or standard calendar
        today = datetime.date.today()
        if days_past_due > 0:
            due_date = today - datetime.timedelta(days=days_past_due)
            due_date_str = due_date.strftime("%d-%b-%Y")
        else:
            # Due on 5th of next month (or current month if today is before the 5th)
            due_month = today.month if today.day < 5 else (today.month % 12 + 1)
            due_year = today.year if today.day < 5 or today.month < 12 else today.year + 1
            due_date_str = f"05-{datetime.date(due_year, due_month, 1).strftime('%b-%Y')}"

        # 2. Select appropriate template & tone according to risk band and communication type
        if message_type == "EMI Reminder":
            return (
                f"Dear {name},\n\n"
                f"This is a reminder regarding your {loan_scheme} Loan account at {branch}. "
                f"Our records show that your EMI due date was/is {due_date_str}. "
                f"Your outstanding balance is {outstanding_str}, and your last successful EMI payment was recorded on {last_emi_date}.\n\n"
                f"Currently, your account holds a Health Score of {health_score}/100. "
                f"Kindly ensure your outstanding dues are cleared to maintain a healthy account standing and avoid late payment charges.\n\n"
                f"Suggested Next Action: Clear outstanding EMI within 3 working days.\n"
                f"For assistance, please visit {branch} or contact the manager at {phone} / email {email}.\n\n"
                f"Warm regards,\n"
                f"Bandhan Admin\n"
                f"Bandhan Bank Recovery Division"
            )
        elif message_type == "Early Warning Notice":
            return (
                f"Dear {name},\n\n"
                f"This is an early warning notification regarding your {loan_scheme} Loan account. "
                f"Bandhan's risk intelligence system has flagged early stress indicators on your account. "
                f"Your account currently has a Health Score of {health_score}/100, is in the {risk_level} Risk band, and has {days_past_due} days past due (Due Date: {due_date_str}).\n\n"
                f"We request you to address this matter immediately to prevent any change in your account classification or adverse impact on credit bureaus.\n\n"
                f"Suggested Next Action: Schedule an account review with your branch manager within 5 days.\n"
                f"Branch Contact: {branch}, Phone: {phone}, Email: {email}.\n\n"
                f"Warm regards,\n"
                f"Bandhan Admin\n"
                f"Bandhan Bank Recovery Division"
            )
        elif message_type == "Loan Restructuring Offer":
            return (
                f"Dear {name},\n\n"
                f"We understand that cash-flow fluctuations can affect business performance. "
                f"Regarding your {loan_scheme} Loan account (Health Score: {health_score}/100, DPD: {days_past_due}, Due Date: {due_date_str}), "
                f"Bandhan Bank is pleased to offer you special loan restructuring assistance.\n\n"
                f"Restructuring can help reduce your monthly EMI burden or extend your loan tenure to align with your current cash flows. "
                f"Kindly visit the branch office to review and sign the restructured loan agreement.\n\n"
                f"Suggested Next Action: Visit the branch with recent sales records to apply for restructuring.\n"
                f"Branch Contact: {branch}, Phone: {phone}, Email: {email}.\n\n"
                f"Warm regards,\n"
                f"Bandhan Admin\n"
                f"Bandhan Bank Recovery Division"
            )
        elif message_type == "Branch Visit Notification":
            return (
                f"Dear {name},\n\n"
                f"You are requested to visit the {branch} within the next 3 working days. "
                f"This visit is essential for a physical review of your active {loan_scheme} Loan account, "
                f"which shows an outstanding amount of {outstanding_str} and is currently overdue by {days_past_due} days (Due Date: {due_date_str}).\n\n"
                f"Please bring your recent sales summaries and bank statements so we can work out a regularization plan.\n\n"
                f"Suggested Next Action: Visit the branch manager with financial statements by Friday.\n"
                f"Branch Details: {branch}, Phone: {phone}, Email: {email}.\n\n"
                f"Warm regards,\n"
                f"Bandhan Admin\n"
                f"Bandhan Bank Recovery Division"
            )
        elif message_type == "Recovery Reminder":
            return (
                f"Dear {name},\n\n"
                f"URGENT NOTICE: Outstanding Recovery Action for your {loan_scheme} Loan (Outstanding: {outstanding_str}, DPD: {days_past_due}).\n\n"
                f"Despite our previous reminders, your account remains overdue since {due_date_str}. "
                f"Your account is categorized under {risk_level} Risk (Health Score: {health_score}/100). "
                f"Failure to regularize this account immediately will compel the bank to initiate official asset recovery protocols as per legal banking regulations.\n\n"
                f"Suggested Next Action: Remit the overdue amount immediately or visit the branch for resolution.\n"
                f"Branch Contact: {branch}, Phone: {phone}, Email: {email}.\n\n"
                f"Warm regards,\n"
                f"Bandhan Admin\n"
                f"Recovery & Enforcement Cell, Bandhan Bank"
            )
        else: # Custom Message
            body = custom_body or "This is a notification regarding your active loan account with us."
            return (
                f"Dear {name},\n\n"
                f"{body}\n\n"
                f"Account Details:\n"
                f"- Scheme: {loan_scheme}\n"
                f"- Outstanding: {outstanding_str}\n"
                f"- Due Date: {due_date_str}\n"
                f"- Health Score: {health_score}/100\n"
                f"- Risk Band: {risk_level}\n\n"
                f"Suggested Next Action: Contact your branch or visit online to manage your loan.\n"
                f"Contact details: {branch}, Phone: {phone}, Email: {email}.\n\n"
                f"Warm regards,\n"
                f"Bandhan Admin\n"
                f"Bandhan Bank"
            )


class CommunicationService:
    """Handles SMTP (email) and Twilio/Fast2SMS (SMS) transports, with fallback simulations."""

    @staticmethod
    def is_email_configured() -> bool:
        return bool(os.getenv("SMTP_SERVER") and os.getenv("SMTP_PASSWORD"))

    @staticmethod
    def is_sms_configured() -> bool:
        has_twilio = bool(os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN") and os.getenv("TWILIO_PHONE_NUMBER"))
        has_fast2sms = bool(os.getenv("FAST2SMS_API_KEY"))
        return has_twilio or has_fast2sms

    @staticmethod
    def send_email(to_email: str, subject: str, body: str) -> dict:
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = os.getenv("SMTP_PORT", "587")
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        smtp_from = os.getenv("SMTP_FROM_EMAIL", "alerts@bandhanbank.co.in")

        if not smtp_server or not smtp_password:
            # Simulation mode
            return {"status": "Simulated", "message": "Email simulated successfully (Credentials not configured)."}

        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(smtp_server, int(smtp_port))
            server.starttls()
            server.login(smtp_username or smtp_from, smtp_password)
            server.sendmail(smtp_from, to_email, msg.as_string())
            server.quit()
            return {"status": "Sent", "message": f"Email successfully sent to {to_email}."}
        except Exception as e:
            return {"status": "Failed", "message": f"SMTP error: {str(e)}"}

    @staticmethod
    def send_sms(mobile_number: str, body: str) -> dict:
        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
        fast2sms_key = os.getenv("FAST2SMS_API_KEY")

        # 1. Twilio Transport
        if twilio_sid and twilio_token and twilio_phone:
            try:
                url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
                payload = {
                    "From": twilio_phone,
                    "To": mobile_number,
                    "Body": body
                }
                res = requests.post(url, data=payload, auth=(twilio_sid, twilio_token), timeout=5)
                if res.status_code in [200, 201]:
                    return {"status": "Sent", "message": f"SMS successfully sent to {mobile_number} via Twilio."}
                else:
                    return {"status": "Failed", "message": f"Twilio API Error: {res.text}"}
            except Exception as e:
                return {"status": "Failed", "message": f"Twilio connection error: {str(e)}"}

        # 2. Fast2SMS Transport
        elif fast2sms_key:
            try:
                url = "https://www.fast2sms.com/dev/bulkV2"
                headers = {
                    "authorization": fast2sms_key,
                    "Content-Type": "application/json"
                }
                # Clean mobile number to 10-digit number for Indian SMS routing
                clean_num = "".join(filter(str.isdigit, mobile_number))
                if clean_num.startswith("91") and len(clean_num) > 10:
                    clean_num = clean_num[2:]

                payload = {
                    "route": "q",
                    "message": body,
                    "language": "english",
                    "numbers": clean_num
                }
                res = requests.post(url, json=payload, headers=headers, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("return"):
                        return {"status": "Sent", "message": f"SMS successfully sent to {mobile_number} via Fast2SMS."}
                    else:
                        return {"status": "Failed", "message": f"Fast2SMS error: {data.get('message')}"}
                else:
                    return {"status": "Failed", "message": f"Fast2SMS HTTP Error: {res.status_code}"}
            except Exception as e:
                return {"status": "Failed", "message": f"Fast2SMS connection error: {str(e)}"}

        # 3. Simulation Fallback
        else:
            return {"status": "Simulated", "message": "SMS simulated successfully (Credentials not configured)."}


# ─────────────────────────────────────────────
# LOGGING SYSTEM
# ─────────────────────────────────────────────

def init_logs_file():
    if not os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "admin_name", "borrower_id", "borrower_name",
                "channel", "message_type", "message_content", "delivery_status", "read_status"
            ])


def log_communication(
    admin_name: str,
    borrower_id: str,
    borrower_name: str,
    channel: str,
    message_type: str,
    message_content: str,
    delivery_status: str,
    read_status: str = "N/A"
):
    init_logs_file()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOGS_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            now_str, admin_name, borrower_id, borrower_name,
            channel, message_type, message_content, delivery_status, read_status
        ])


def get_communication_logs() -> pd.DataFrame:
    init_logs_file()
    try:
        df = pd.read_csv(LOGS_FILE)
        if df.empty:
            return df
        # Sort by timestamp descending
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp", ascending=False)
        df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        return df
    except Exception:
        return pd.DataFrame(columns=[
            "timestamp", "admin_name", "borrower_id", "borrower_name",
            "channel", "message_type", "message_content", "delivery_status", "read_status"
        ])


# ─────────────────────────────────────────────
# TWO-FACTOR AUTHENTICATION & SECURITY LOGGER
# ─────────────────────────────────────────────

ADMIN_SECURITY_LOGS_FILE = "admin_security_logs.csv"

def generate_otp() -> str:
    """Generates a cryptographically secure 6-digit random verification code."""
    import secrets
    return f"{secrets.randbelow(900000) + 100000}"


def send_otp_email(to_email: str, otp: str) -> dict:
    """Formats and dispatches the OTP verification code via SMTP."""
    subject = "Bandhan Bank Security - Your 2FA Verification Code"
    body = (
        f"Dear Bandhan Portal User,\n\n"
        f"Your Bandhan 2FA Verification OTP is: {otp}\n\n"
        f"This code will expire in 5 minutes (300 seconds) and is valid for a single use.\n\n"
        f"Security Warning: Bandhan Bank employees will never ask for your password or OTP. "
        f"If you did not request this login attempt, please notify the threat response team immediately.\n\n"
        f"Warm regards,\n"
        f"Bandhan Bank Security Operations Cell"
    )
    return CommunicationService.send_email(to_email, subject, body)


def send_otp_sms(mobile_number: str, otp: str) -> dict:
    """Formats and dispatches the OTP verification code via Twilio/Fast2SMS."""
    body = f"Bandhan Bank: Your 2FA Verification OTP is {otp}. Valid for 5 mins. Do not share."
    return CommunicationService.send_sms(mobile_number, body)


def init_admin_security_logs_file():
    if not os.path.exists(ADMIN_SECURITY_LOGS_FILE):
        with open(ADMIN_SECURITY_LOGS_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "username", "ip_address", "device_info", "status"])


def log_admin_login_attempt(username: str, ip: str, device: str, status: str):
    """Appends an admin login event (SUCCESS/FAILED) to the secure logs."""
    init_admin_security_logs_file()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ADMIN_SECURITY_LOGS_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([now_str, username, ip, device, status])


def get_admin_security_metrics(username: str) -> dict:
    """Computes last successful login timestamp and consecutive failed attempts counter."""
    init_admin_security_logs_file()
    metrics = {
        "last_successful_login": "Never",
        "last_successful_ip": "N/A",
        "last_successful_device": "N/A",
        "failed_login_count": 0,
        "logs": []
    }
    try:
        if not os.path.exists(ADMIN_SECURITY_LOGS_FILE):
            return metrics
            
        df = pd.read_csv(ADMIN_SECURITY_LOGS_FILE)
        # Filter for this username
        user_df = df[df["username"] == username].copy()
        if user_df.empty:
            return metrics
            
        # Parse timestamps and sort ascending
        user_df["timestamp"] = pd.to_datetime(user_df["timestamp"])
        user_df = user_df.sort_values("timestamp", ascending=True)
        
        # Calculate failed attempts since last successful login
        consecutive_failures = 0
        last_success = None
        
        for _, row in user_df.iterrows():
            status = str(row["status"]).upper()
            if status == "SUCCESS":
                last_success = row
                consecutive_failures = 0  # reset count on success
            elif status == "FAILED":
                consecutive_failures += 1
                
        if last_success is not None:
            metrics["last_successful_login"] = last_success["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            metrics["last_successful_ip"] = str(last_success["ip_address"])
            metrics["last_successful_device"] = str(last_success["device_info"])
            
        metrics["failed_login_count"] = consecutive_failures
        
        # Add formatted logs descending
        user_df_desc = user_df.sort_values("timestamp", ascending=False)
        user_df_desc["timestamp"] = user_df_desc["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        metrics["logs"] = user_df_desc.to_dict("records")
    except Exception:
        pass
        
    return metrics
