from __future__ import annotations

import calendar
import subprocess
from html import escape
from pathlib import Path
import textwrap
from textwrap import dedent

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from detection_engine import SatarkSetuDetector
from repositories import BorrowerRepository
import os

from communication_engine import (
    InHouseAIReasoningEngine,
    CommunicationService,
    log_communication,
    get_communication_logs,
    generate_otp,
    send_otp_email,
    send_otp_sms,
    log_admin_login_attempt,
    get_admin_security_metrics
)
from audit_compliance_engine import audit_log, render_audit_compliance_center
from recovery_portal_engine import RecoveryPortalEngine
from rm_copilot_engine import RMCopilotEngine

def render_safe_html(content: str) -> None:
    """Render HTML safely without triggering Markdown indented code block parsing."""
    clean = "\n".join(line.strip() for line in content.splitlines() if line.strip())
    if hasattr(st, "html"):
        st.html(clean)
    else:
        st.markdown(clean, unsafe_allow_html=True)

API_BASE_URL = os.getenv("API_BASE_URL")
if not API_BASE_URL:
    API_BASE_URL = "http://localhost:8000"

DEBUG = False
if DEBUG:
    st.write("Backend URL:", API_BASE_URL)

DATA_FILES = ["borrowers.csv", "loan_transactions.csv", "regional_context.csv"]
ADMIN_CREDENTIALS = {
    "admin": "admin123",
    "ujjwal": "ujjwal",
    "sumedha": "sumedha",
    "jyoti": "jyoti",
}
ADMIN_EMAILS = {
    "admin": "admin@bandhanbank.co.in",
    "ujjwal": "ujjwal@bandhanbank.co.in",
    "sumedha": "sumedha@bandhanbank.co.in",
    "jyoti": "jyoti@bandhanbank.co.in",
}
ADMIN_MOBILES = {
    "admin": "+91 9999900000",
    "ujjwal": "+91 9999900001",
    "sumedha": "+91 9999900002",
    "jyoti": "+91 9999900003",
}
BORROWER_PASSWORD = "borrower123"


def ensure_demo_data() -> None:
    required = ["borrowers.csv", 
                "loan_transactions.csv", 
                "regional_context.csv"]
    if all(Path(f).exists() for f in required):
        return
    subprocess.run(
        ["python3", "data_generator.py"], check=True
    )


@st.cache_data(show_spinner=False)
def load_data():
    ensure_demo_data()
    borrowers = pd.read_csv("borrowers.csv")
    transactions = pd.read_csv("loan_transactions.csv", parse_dates=["timestamp"])
    regional = pd.read_csv("regional_context.csv")
    return borrowers, transactions, regional


@st.cache_resource(show_spinner=False)
def initialize_detector(borrowers: pd.DataFrame, transactions: pd.DataFrame, regional: pd.DataFrame):
    detector = SatarkSetuDetector(borrowers, transactions, regional)
    detector.build_graph()
    return detector


st.set_page_config(page_title="Bandhan", layout="wide", page_icon="🏦")

st.markdown(
    """
    <style>
    [data-testid="stStatusWidget"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    
    /* Main App Canvas */
    .stApp {
        background-color: #F8F5EE !important;
        background-image: 
            radial-gradient(circle at 10% 8%, rgba(200, 170, 140, 0.12), transparent 35%),
            radial-gradient(circle at 90% 92%, rgba(107, 63, 35, 0.06), transparent 45%) !important;
        color: #2C1E16 !important;
    }
    
    .main h1, .main h2, .main h3, .main h4, .main p, .main label, .main span, .main div {
        color: #2C1E16;
    }
    
    div[data-testid="stMarkdownContainer"] > h1, 
    div[data-testid="stMarkdownContainer"] > h2, 
    div[data-testid="stMarkdownContainer"] > h3 {
        color: #2C1E16 !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
    }

    /* Top Breadcrumb Bar */
    .top-breadcrumb-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0 18px 0;
        border-bottom: 1px solid #EDE6DC;
        margin-bottom: 24px;
    }
    .breadcrumb-text {
        font-size: 0.88rem;
        color: #7D6C63;
        font-weight: 500;
    }
    .breadcrumb-text b {
        color: #2C1E16;
        font-weight: 700;
    }
    .top-user-chip {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        background: #FFFFFF;
        border: 1px solid #E8E1D5;
        padding: 5px 12px;
        border-radius: 999px;
        box-shadow: 0 1px 4px rgba(44,30,22,0.04);
    }
    .user-avatar-circle {
        width: 26px;
        height: 26px;
        border-radius: 50%;
        background: #6B3F23;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.72rem;
        font-weight: 700;
    }

    /* Card Containers */
    .hero, .focus-card, .section-card {
        background: #FFFFFF !important;
        border: 1px solid #E8E1D5 !important;
        border-radius: 12px !important;
        padding: 24px 28px !important;
        box-shadow: 0 2px 8px rgba(44, 30, 22, 0.04) !important;
        margin-bottom: 20px;
    }
    .hero h1 {
        color: #2C1E16 !important;
        font-weight: 800 !important;
        margin-bottom: 0.5rem;
    }
    .hero p {
        margin: 0;
        color: #6E5D53;
        font-size: 0.98rem;
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background: #FFFFFF !important;
        border: 1px solid #E8E1D5 !important;
        border-radius: 12px !important;
        padding: 18px 22px !important;
        box-shadow: 0 2px 8px rgba(44, 30, 22, 0.04) !important;
    }
    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] p {
        color: #7D6C63 !important;
        font-weight: 700 !important;
        font-size: 0.74rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.07em !important;
    }
    [data-testid="stMetricValue"] {
        color: #2C1E16 !important;
        font-weight: 800 !important;
        font-size: 2.1rem !important;
        letter-spacing: -0.02em !important;
    }

    /* Pill Badges */
    .flag-pill {
        background: #FFFFFF;
        border: 1px solid #E8E1D5;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 10px;
        box-shadow: 0 1px 4px rgba(44, 30, 22, 0.04);
        color: #2C1E16;
        font-weight: 600;
        font-size: 0.92rem;
        display: block;
    }

    /* Tabs (Executive Warm Palette) */
    [data-baseweb="tab-list"] {
        gap: 6px;
        padding: 6px;
        background: #EDE6DC;
        border-radius: 10px;
        border: 1px solid #DFD7CC;
        display: flex;
        width: 100%;
    }
    [data-testid="stTabs"] button[role="tab"] {
        color: #6E5D53 !important;
        background: transparent !important;
        border-radius: 6px !important;
        border: none !important;
        padding: 10px 16px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        transition: all 0.2s ease !important;
        flex: 1 !important;
        text-align: center !important;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: #2C1E16 !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(44, 30, 22, 0.16) !important;
        border-bottom: none !important;
        outline: none !important;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="false"] {
        color: #6E5D53 !important;
    }
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {
        display: none !important;
    }

    /* Standard and Primary Buttons */
    .stButton button {
        border-radius: 8px !important;
        border: 1px solid #DFD7CC !important;
        background: #FFFFFF !important;
        color: #2C1E16 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        min-height: 42px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(44, 30, 22, 0.06) !important;
    }
    .stButton button:hover {
        background: #FAF7F2 !important;
        border-color: #C6B9A8 !important;
        color: #6B3F23 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 10px rgba(44, 30, 22, 0.08) !important;
    }
    .stForm [data-testid="stFormSubmitButton"] button,
    button[kind="primary"] {
        background: #6B3F23 !important;
        color: #FFFFFF !important;
        border: 1px solid #54311A !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 6px rgba(107, 63, 35, 0.2) !important;
    }

    .run-ai-btn button,
    .run-contagion-btn button {
        background: linear-gradient(135deg, #6B3F23 0%, #8D5430 100%) !important;
        color: #ffffff !important;
        border: 1px solid #54311A !important;
        box-shadow: 0 4px 14px rgba(107, 63, 35, 0.25) !important;
    }
    .run-ai-btn button:hover,
    .run-contagion-btn button:hover {
        background: linear-gradient(135deg, #54311A 0%, #6B3F23 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 18px rgba(107, 63, 35, 0.35) !important;
    }
    .stForm [data-testid="stFormSubmitButton"] button p,
    .stForm [data-testid="stFormSubmitButton"] button span,
    button[kind="primary"] p,
    button[kind="primary"] span,
    .run-ai-btn button p,
    .run-ai-btn button span,
    .run-contagion-btn button p,
    .run-contagion-btn button span {
        color: #ffffff !important;
    }

    /* Enterprise Dark Espresso Sidebar */
    [data-testid="stSidebar"] {
        background: #2C1E16 !important;
        border-right: 1px solid #3E2B20 !important;
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.15) !important;
    }
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    [data-testid="stSidebar"] * {
        color: #E8E0D5 !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] [data-baseweb="input"] > div {
        background: #3A281E !important;
        border: 1px solid #4E3629 !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-baseweb="input"] *,
    [data-testid="stSidebar"] .stSlider * {
        color: #FFFFFF !important;
    }
    /* Sidebar Navigation Menu Buttons */
    [data-testid="stSidebar"] .stButton {
        margin-bottom: 2px !important;
    }
    [data-testid="stSidebar"] .stButton button {
        background: transparent !important;
        border: 1px solid transparent !important;
        color: #C4B5A5 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 9px 14px !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        width: 100% !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        background: #3A281E !important;
        border-color: transparent !important;
        color: #FFFFFF !important;
        transform: none !important;
    }
    [data-testid="stSidebar"] .stButton button[kind="primary"] {
        background: #3E2B20 !important;
        border: 1px solid #5A4032 !important;
        border-left: 3px solid #D4A373 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] .stButton button p {
        color: #C4B5A5 !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        text-align: left !important;
    }
    [data-testid="stSidebar"] .stButton button[kind="primary"] p {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] .stButton button:hover p {
        color: #FFFFFF !important;
    }
    .sidebar-signout-container button {
        background: #3A281E !important;
        border: 1px solid #4E3629 !important;
        color: #E8E0D5 !important;
        justify-content: center !important;
        text-align: center !important;
        font-weight: 600 !important;
        margin-top: 4px !important;
    }
    .sidebar-signout-container button p {
        text-align: center !important;
        color: #E8E0D5 !important;
    }
    .sidebar-signout-container button:hover {
        background: #4E3629 !important;
        border-color: #D4A373 !important;
        color: #FFFFFF !important;
    }
    .sidebar-signout-container button:hover p {
        color: #FFFFFF !important;
    }

    /* Section Cards */
    .section-card {
        background: #FFFFFF !important;
        border: 1px solid #E8E1D5 !important;
        border-radius: 14px !important;
        padding: 24px;
        box-shadow: 0 2px 8px rgba(44, 30, 22, 0.04) !important;
    }

    /* Headers Fix */
    div[data-testid="stMarkdownContainer"] > h1, 
    div[data-testid="stMarkdownContainer"] > h2, 
    div[data-testid="stMarkdownContainer"] > h3 {
        color: #2C1E16 !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    /* Enterprise Banking Tables */
    .glass-table-shell {
        background: #FFFFFF !important;
        border: 1px solid #E8E1D5 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(44, 30, 22, 0.04) !important;
        overflow: hidden;
    }
    .glass-table-wrap {
        overflow-x: auto;
    }
    .glass-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        color: #2C1E16;
        font-size: 0.88rem;
        background: #FFFFFF;
    }
    .glass-table thead th {
        position: sticky;
        top: 0;
        z-index: 1;
        background: #FAF7F2 !important;
        color: #6E5F52 !important;
        text-align: left;
        padding: 12px 16px;
        font-weight: 700;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        border-bottom: 1px solid #E8E1D5;
    }
    .glass-table tbody td {
        padding: 13px 16px;
        background: #FFFFFF;
        border-bottom: 1px solid #F0EAE1;
        color: #2C1E16;
    }
    .glass-table tbody tr:nth-child(even) td {
        background: #FCFAF7;
    }
    .glass-table tbody tr:hover td {
        background: #F5EFEB;
    }

    /* Status Pills */
    .status-pill {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.76rem;
        font-weight: 600;
        text-align: center;
        white-space: nowrap;
    }
    .status-success {
        background: #EDF7ED !important;
        color: #1E7E34 !important;
        border: 1px solid #C8E6C9 !important;
    }
    .status-error {
        background: #FFF0F0 !important;
        color: #C53030 !important;
        border: 1px solid #FCD4D4 !important;
    }
    .status-warning {
        background: #FFF4E5 !important;
        color: #C05621 !important;
        border: 1px solid #FDE2C2 !important;
    }
    .status-neutral {
        background: #F3F4F6 !important;
        color: #4B5563 !important;
        border: 1px solid #E5E7EB !important;
    }
    /* Turfingo Blueprint */
    .landing-hero {
        padding: 4vh 2vw 2vh 2vw;
        display: grid;
        grid-template-columns: minmax(0, 1.15fr) minmax(360px, 0.85fr);
        gap: 36px;
        align-items: center;
        min-height: 75vh;
        position: relative;
        overflow: hidden;
    }
    .landing-copy {
        position: relative;
        z-index: 2;
    }
    .landing-logo-chip {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 88px;
        height: 88px;
        margin-bottom: 20px;
        border-radius: 24px;
        background: rgba(255,255,255,0.38);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.75);
        box-shadow: 0 18px 32px rgba(120, 60, 80, 0.12);
    }
    .landing-logo-chip img {
        width: 62px;
        height: 62px;
        object-fit: contain;
    }
    .landing-hero h1 {
        font-size: clamp(3.2rem, 5.2vw, 5.2rem);
        font-weight: 800;
        font-style: italic;
        line-height: 1.05;
        letter-spacing: -2px;
        color: #2C1E16;
        margin: 0 0 24px 0;
        text-transform: uppercase;
        white-space: nowrap;
    }
    .landing-hero p.subtext {
        font-size: 1.35rem;
        color: #5A493B;
        max-width: 580px;
        line-height: 1.6;
        font-weight: 500;
        margin-bottom: 48px;
        border-left: 4px solid #6B3F23;
        padding-left: 24px;
    }
    .landing-metrics {
        display: flex;
        gap: 80px;
        border-top: 1px solid rgba(107, 63, 35, 0.15);
        padding-top: 32px;
        margin-top: 60px;
    }
    .metric-box h3 {
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0 0 4px 0;
        color: #6B3F23;
    }
    .metric-box p {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #8C7E72;
        margin: 0;
        font-weight: 700;
    }
    .landing-art {
        position: relative;
        min-height: 620px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .hero-cutout {
        position: absolute;
        overflow: hidden;
        border-radius: 34px;
        background: rgba(255,255,255,0.14);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.55);
        box-shadow: 0 26px 44px rgba(120, 60, 80, 0.14);
    }
    .hero-cutout img {
        position: absolute;
        max-width: none;
        filter: drop-shadow(0 18px 26px rgba(15, 60, 34, 0.14));
    }
    .hero-cutout.main {
        width: 56%;
        height: 78%;
        right: 6%;
        top: 10%;
        transform: rotate(7deg);
    }
    .hero-cutout.main img {
        width: 132%;
        left: -18%;
        top: -8%;
        transform: rotate(-5deg);
    }
    .hero-cutout.hand {
        width: 30%;
        height: 34%;
        left: 8%;
        top: 18%;
        transform: rotate(-10deg);
    }
    .hero-cutout.hand img {
        width: 188%;
        left: -96%;
        top: 2%;
    }
    .hero-cutout.bag {
        width: 28%;
        height: 32%;
        left: 24%;
        bottom: 14%;
        transform: rotate(9deg);
    }
    .hero-cutout.bag img {
        width: 186%;
        left: -18%;
        top: -54%;
    }
    .hero-cutout.arrow {
        width: 24%;
        height: 22%;
        right: 18%;
        bottom: 8%;
        transform: rotate(-8deg);
    }
    .hero-cutout.arrow img {
        width: 165%;
        left: -66%;
        top: -16%;
    }
    .hero-echo {
        position: absolute;
        width: 78%;
        max-width: none;
        opacity: 0.08;
        right: 2%;
        top: 9%;
        transform: rotate(8deg);
    }
    @media (max-width: 1100px) {
        .landing-hero {
            grid-template-columns: 1fr;
            gap: 20px;
        }
        .landing-art {
            min-height: 440px;
        }
        .landing-hero h1 {
            font-size: 5.4rem;
        }
    }
    
    .mission-row {
        padding: 10vh 2vw;
        border-top: 1px solid rgba(107, 63, 35, 0.15);
        background: transparent;
    }
    .mission-card {
        padding: 20px 40px;
        height: 100%;
        background: transparent;
        border-right: 1px solid rgba(107, 63, 35, 0.15);
    }
    .mission-card:last-child {
        border-right: none;
    }
    .mission-number {
        font-size: 3.5rem;
        font-weight: 300;
        font-style: italic;
        color: rgba(107, 63, 35, 0.2);
        margin-bottom: 24px;
        line-height: 1;
    }
    .mission-card h3 {
        font-size: 2.2rem;
        font-weight: 800;
        font-style: italic;
        margin-bottom: 16px;
        color: #2C1E16;
    }
    .mission-card p {
        font-size: 1.1rem;
        color: #5A493B;
        line-height: 1.6;
    }

    .about-section {
        padding: 10vh 2vw;
        border-top: 1px solid rgba(107, 63, 35, 0.15);
    }
    .about-mini-title {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 700;
        color: #6B3F23;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .about-mini-title::before {
        content: "";
        display: inline-block;
        width: 32px;
        height: 2px;
        background: #6B3F23;
    }
    .about-header {
        font-size: 5rem;
        font-weight: 800;
        font-style: italic;
        text-transform: uppercase;
        color: #2C1E16;
        line-height: 1.1;
        margin-bottom: 32px;
        letter-spacing: -2px;
    }
    .about-text {
        font-size: 1.3rem;
        color: #3a3a3c;
        max-width: 500px;
        line-height: 1.6;
        font-weight: 500;
    }
    .staggered-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px;
        margin-top: 40px;
    }
    .staggered-item {
        background: rgba(255,255,255,0.4);
        border: 1px solid rgba(255,255,255,0.6);
        border-radius: 20px;
        height: 280px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 16px 40px rgba(0,0,0,0.06);
        font-weight: 700;
        font-size: 1.2rem;
        color: #174229;
        overflow: hidden;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }
    .staggered-item:nth-child(2n) {
        transform: translateY(60px);
    }
    .contact-card {
        background: rgba(255,255,255,0.7);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        border: 1px solid rgba(255,255,255,0.9);
        box-shadow: 0 8px 24px rgba(0,0,0,0.03);
    }
    .contact-card p.small {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #636366;
        margin: 0 0 8px 0;
        font-weight: 700;
    }
    .contact-card h4 {
        margin: 0;
        font-size: 1.2rem;
        font-weight: 700;
        color: #1c1c1e;
    }
    /* Fix all widget labels — clear, warm corporate text */
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label,
    .stSlider label,
    .stSelectbox label {
        color: #5A493B !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        opacity: 1 !important;
    }

    /* Fix selectbox & input — crisp white background, subtle border */
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div {
        background: #FFFFFF !important;
        border: 1px solid #DFD7CC !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 2px rgba(44, 30, 22, 0.04) !important;
    }
    [data-baseweb="select"] span,
    [data-baseweb="select"] div,
    [data-baseweb="input"] input {
        color: #2C1E16 !important;
        background: transparent !important;
        font-size: 0.9rem !important;
    }

    /* Fix slider value */
    [data-testid="stSlider"] p {
        color: #2C1E16 !important;
        font-weight: 600 !important;
    }

    /* Fix metric labels and values */
    [data-testid="stMetricLabel"] p {
        color: #8C7E72 !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.8px !important;
        text-transform: uppercase !important;
        opacity: 1 !important;
    }
    [data-testid="stMetricValue"] div {
        color: #2C1E16 !important;
        font-weight: 800 !important;
        font-size: 1.8rem !important;
    }

    /* Selected tab styling */
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #FFFFFF !important;
        background: #2C1E16 !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 6px rgba(44, 30, 22, 0.2) !important;
    }

    /* Unselected tab text */
    [data-testid="stTabs"] button[role="tab"][aria-selected="false"] {
        color: #5A493B !important;
        background: transparent !important;
        font-weight: 600 !important;
    }

    /* Ensure radio options are warm dark */
    [data-testid="stRadio"] label p,
    [data-testid="stRadio"] label span {
        color: #2C1E16 !important;
        background: transparent !important;
        font-weight: 500 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_resource(show_spinner=False)
def get_detector():
    d = SatarkSetuDetector(
        borrowers_df, transactions_df, regional_df
    )
    d.build_graph()
    return d

@st.cache_resource(show_spinner=False)  
def get_repo():
    return BorrowerRepository()

_loading = st.empty()
_loading.markdown(
    """
    <div style="
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        background: #F8F5EE;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    ">
        <div style="
            background: #FFFFFF;
            border: 1px solid #E8E1D5;
            border-radius: 20px;
            padding: 44px 50px;
            text-align: center;
            box-shadow: 0 12px 36px rgba(44,30,22,0.08);
            min-width: 360px;
        ">
            <div style="
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 48px;
                height: 48px;
                background: #6B3F23;
                color: #FFFFFF;
                border-radius: 10px;
                font-weight: 800;
                font-size: 1.4rem;
                margin-bottom: 16px;
            ">B</div>
            <div style="
                font-size: 1.8rem;
                font-weight: 800;
                color: #2C1E16;
                letter-spacing: -0.5px;
                margin-bottom: 4px;
            ">BANDHAN</div>
            <div style="
                font-size: 0.85rem;
                color: #8C7E72;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 28px;
            ">
                Loan Recovery Management Intelligence
            </div>
            <div style="
                width: 100%;
                height: 5px;
                background: #EDE6DC;
                border-radius: 999px;
                overflow: hidden;
                margin-bottom: 14px;
            ">
                <div style="
                    height: 100%;
                    width: 100%;
                    background: #6B3F23;
                    border-radius: 999px;
                    animation: loadbar 1.5s ease-in-out infinite;
                "></div>
            </div>
            <div style="
                font-size: 0.82rem;
                color: #8C7E72;
                font-weight: 500;
            ">
                Loading portfolio intelligence & risk models...
            </div>
        </div>
        <style>
            @keyframes loadbar {
                0%   { transform: translateX(-100%); }
                50%  { transform: translateX(0%); }
                100% { transform: translateX(100%); }
            }
        </style>
    </div>
    """,
    unsafe_allow_html=True
)

borrowers_df, transactions_df, regional_df = \
    load_data()
detector = get_detector()
repo     = get_repo()

_loading.empty()


def style_figure(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template=None,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#2C1E16", family="Plus Jakarta Sans, Inter, sans-serif"),
        title_font=dict(color="#2C1E16", size=18, family="Plus Jakarta Sans, Inter, sans-serif"),
        legend=dict(
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#E8E1D5",
            borderwidth=1,
            font=dict(color="#2C1E16", size=12),
        ),
        margin=dict(l=16, r=16, t=48, b=48),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#F0EAE1",
        zeroline=False,
        linecolor="#DFD7CC",
        tickfont=dict(color="#6E5F52", size=11),
        title_font=dict(color="#2C1E16", size=13),
        title_standoff=14,
        automargin=True,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#F0EAE1",
        zeroline=False,
        linecolor="#DFD7CC",
        tickfont=dict(color="#6E5F52", size=11),
        title_font=dict(color="#2C1E16", size=13),
        title_standoff=12,
        automargin=True,
    )
    return fig


def render_glass_table(df: pd.DataFrame, *, max_height: int | None = None) -> None:
    if df.empty:
        st.info("No records available.")
        return

    display_df = df.fillna("")
    cols = display_df.columns.tolist()
    head_html = "".join(f"<th>{escape(str(column))}</th>" for column in cols)
    body_rows = []
    for row in display_df.itertuples(index=False):
        cells = []
        for i, col in enumerate(cols):
            val = str(row[i])
            col_lower = col.lower()
            if col_lower in ["status", "delivery status", "read status", "comm status", "current risk band"]:
                status_lower = val.lower()
                if any(x in status_lower for x in ["paid", "completed", "success", "posted", "active", "sent", "low", "read"]):
                    color_class = "status-success"
                elif any(x in status_lower for x in ["delayed", "failed", "overdue", "support required", "support_required", "critical", "high", "unread"]):
                    color_class = "status-error"
                else:
                    color_class = "status-warning"
                cells.append(f'<td><span class="status-pill {color_class}">{escape(val)}</span></td>')
            else:
                cells.append(f"<td>{escape(val)}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    height_style = f"max-height:{max_height}px;" if max_height else ""
    st.markdown(
        f"""
        <div class="glass-table-shell">
            <div class="glass-table-wrap" style="{height_style}">
                <table class="glass-table">
                    <thead><tr>{head_html}</tr></thead>
                    <tbody>{''.join(body_rows)}</tbody>
                </table>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

@st.cache_data(ttl=600, show_spinner=False)
def build_portfolio_df(_borrowers_df, _transactions_df, 
                       _regional_df):
    borrowers  = _borrowers_df.copy()
    regional   = _regional_df.copy()
    
    # Merge regional data into borrowers directly
    # instead of calling detector per borrower
    merged = borrowers.merge(
        regional[["region", "npa_rate", 
                  "economic_stress_index",
                  "peer_health_baseline"]],
        on="region", how="left"
    )
    
    # Compute risk score vectorised — no per-borrower loop
    missed_norm = (merged["missed_payments_90d"]
                   .clip(0, 4) / 4.0)
    dpd_norm    = (merged["days_past_due"]
                   .clip(0, 90) / 90.0)
    peer_norm   = 1.0 - (merged["peer_score"] / 100.0)
    stress      = merged["regional_stress_factor"]
    repayment   = merged["repayment_consistency"]
    inflow_st   = merged["inflow_stability"]

    risk_score = (
        missed_norm    * 30 +
        dpd_norm       * 25 +
        peer_norm      * 15 +
        (1 - repayment)* 15 +
        stress         * 10 +
        (1 - inflow_st)* 5
    ).clip(0, 100).round(1)

    merged["risk_score"]   = risk_score
    merged["health_score"] = (100 - risk_score).round(1)

    def risk_level(score):
        if score >= 70:   return "High Risk"
        elif score >= 50: return "Medium Risk"
        elif score >= 30: return "Low Risk"
        else:             return "Healthy"

    merged["risk_level"] = merged["risk_score"].apply(
        risk_level
    )
    merged["status"] = "ACTIVE"
    merged["name"]   = merged["name"].str.title()

    return merged


def logout() -> None:
    role = "ADMIN" if st.session_state.get("admin_authenticated") else "BORROWER" if st.session_state.get("borrower_authenticated") else "GUEST"
    user_id = st.session_state.get("admin_username") or st.session_state.get("borrower_id") or "unknown"
    audit_log("Authentication", f"{role.title()} Logout", borrower_id=(st.session_state.get("borrower_id") or "N/A"), reason="User explicitly initiated session termination")
    
    for key in ["view", "admin_authenticated", "borrower_authenticated", "borrower_id", "admin_username"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def render_app_hero() -> None:
    st.markdown(
        """
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 60px 40px 40px 40px;">
            <div style="width: 64px; height: 64px; background: rgba(212, 163, 115, 0.18); border: 2px solid #D4A373; border-radius: 16px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 2rem; color: #6B3F23; margin-bottom: 20px;">B</div>
            <h1 style="font-size: 4.5rem; line-height: 1.1; margin-bottom: 20px; color: #2C1E16; display: inline-block; font-weight: 800; letter-spacing: -2px; white-space: nowrap;">Bandhan</h1>
            <p style="font-size: 1.3rem; color: #5A493B; max-width: 800px; line-height: 1.5; font-weight: 500;">Borrower health and contextual recovery intelligence for MSME and government-scheme portfolios.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_segmented_health_bar(score: int, title: str = "Health score") -> str:
    total_segments = 28
    filled = max(0, min(total_segments, round((score / 100.0) * total_segments)))
    segs = "".join(
        [
            f'<div style="width: 8px; height: 34px; background: {"linear-gradient(180deg, #76d596 0%, #47bf6a 100%)" if i < filled else "#eef1f7"}; border-radius: 999px;"></div>'
            for i in range(total_segments)
        ]
    )

    return dedent(
        f"""
        <div style="background: rgba(255,255,255,0.92); border-radius: 28px; padding: 26px 24px; border: 1px solid rgba(255,255,255,0.88); box-shadow: 0 18px 34px rgba(180,140,150,0.10); margin-top: 8px; margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <span style="font-size: 1.05rem; font-weight: 600; color: #1c1c1e;">{title}</span>
            </div>
            <div style="border-top: 1px solid rgba(28,28,30,0.08); margin-bottom: 20px;"></div>
            <h3 style="margin: 0 0 8px 0; font-size: 2.5rem; font-weight: 500; color: #1c1c1e; letter-spacing: -1px;">Your credit score is {score}</h3>
            <p style="margin: 0 0 22px 0; color: #636366; font-size: 0.98rem;">Build a stronger repayment history to keep improving this score.</p>
            <div style="display: flex; gap: 5px; margin-bottom: 24px; width: 100%; align-items: end;">{segs}</div>
            <div style="border-top: 1px solid rgba(28,28,30,0.08); padding-top: 18px;">
                <p style="margin: 0; color: #636366; font-size: 0.92rem; line-height: 1.55;">Your credit score reflects your payment reliability. A higher score supports smoother loan servicing and better repayment standing.</p>
            </div>
        </div>
        """
    ).strip()


def render_transaction_days_card(txns: pd.DataFrame, selected_window_days: int | None = None) -> str:
    if txns.empty:
        return """
        <div style="background: rgba(255,255,255,0.92); border-radius: 28px; padding: 26px 24px; border: 1px solid rgba(255,255,255,0.88); box-shadow: 0 18px 34px rgba(180,140,150,0.10); margin-bottom: 24px;">
            <h3 style="margin: 0 0 10px 0; font-size: 1.9rem; font-weight: 500; color: #1c1c1e;">Transactions days</h3>
            <p style="margin: 0; color: #636366;">No recent transactions available.</p>
        </div>
        """

    recent = txns.copy().sort_values("timestamp")
    recent["day"] = recent["timestamp"].dt.normalize()
    end_day = recent["day"].max()
    available_days = max(1, int((end_day - recent["day"].min()).days) + 1)
    if selected_window_days is None:
        window_days = min(62, max(21, available_days))
    else:
        window_days = min(selected_window_days, available_days)
    days = pd.date_range(end=end_day, periods=window_days, freq="D")
    recent = recent[recent["day"].isin(days)]

    per_day: dict[pd.Timestamp, list[dict]] = {}
    for _, row in recent.iterrows():
        per_day.setdefault(row["day"], []).append(row.to_dict())

    def cell_style(entries: list[dict] | None) -> tuple[str, str]:
        if not entries:
            return ("background:#e9edf7;", "&nbsp;")
        paid = sum(1 for item in entries if str(item["transaction_type"]).upper() == "EMI_PAYMENT" and str(item["status"]).upper() in {"ON_TIME", "COMPLETED", "SUCCESS", "PAID"})
        missed = sum(1 for item in entries if str(item["transaction_type"]).upper() == "EMI_PAYMENT" and str(item["status"]).upper() in {"MISSED", "DELAYED", "FAILED", "OVERDUE"})
        inflow = sum(1 for item in entries if str(item["transaction_type"]).upper() == "BUSINESS_INFLOW")
        outflow = sum(1 for item in entries if str(item["transaction_type"]).upper() == "BUSINESS_OUTFLOW")
        other = len(entries) - paid - missed
        if missed:
            return ("background:#ff8d61; color:white;", str(missed))
        if paid:
            return ("background:#64c983; color:white;", str(paid))
        if inflow:
            return ("background:#4d61e8; color:white;", str(other))
        if outflow:
            return ("background:#8a7cf4; color:white;", str(other))
        return ("background:#e9edf7;", "&nbsp;")

    week_labels = "".join(f"<div style='text-align:center; color:#5e6472; font-size:0.92rem;'>{day}</div>" for day in ["M", "T", "W", "T", "F", "S", "S"])

    start_pad = days[0].weekday()
    cells = ["<div></div>" for _ in range(start_pad)]
    active_days = 0
    paid_days = 0
    missed_days = 0
    inflow_days = 0
    outflow_days = 0
    paid_amount = 0.0
    missed_amount = 0.0
    inflow_amount = 0.0
    outflow_amount = 0.0
    for day in days:
        entries = per_day.get(day.normalize())
        if entries:
            active_days += 1
            paid_today = [item for item in entries if str(item["transaction_type"]).upper() == "EMI_PAYMENT" and str(item["status"]).upper() in {"ON_TIME", "COMPLETED", "SUCCESS", "PAID"}]
            missed_today = [item for item in entries if str(item["transaction_type"]).upper() == "EMI_PAYMENT" and str(item["status"]).upper() in {"MISSED", "DELAYED", "FAILED", "OVERDUE"}]
            inflow_today = [item for item in entries if str(item["transaction_type"]).upper() == "BUSINESS_INFLOW"]
            outflow_today = [item for item in entries if str(item["transaction_type"]).upper() == "BUSINESS_OUTFLOW"]
            paid_days += bool(paid_today)
            missed_days += bool(missed_today)
            inflow_days += bool(inflow_today)
            outflow_days += bool(outflow_today)
            paid_amount += sum(float(item.get("amount") or 0) for item in paid_today)
            missed_amount += sum(float(item.get("amount") or 0) for item in missed_today)
            inflow_amount += sum(float(item.get("amount") or 0) for item in inflow_today)
            outflow_amount += sum(float(item.get("amount") or 0) for item in outflow_today)
        style, value = cell_style(entries)
        cells.append(
            f"<div style='width:48px;height:48px;border-radius:999px;display:flex;align-items:center;justify-content:center;font-size:1.45rem;font-weight:500;{style}'>{value}</div>"
        )
    cells_html = "".join(cells)
    start_day = days.min()
    if start_day.month == end_day.month:
        month_label = f"{calendar.month_name[end_day.month]} {end_day.year}"
    else:
        month_label = f"{calendar.month_abbr[start_day.month]}-{calendar.month_abbr[end_day.month]} {end_day.year}"

    return dedent(
        f"""
        <div style="background: rgba(255,255,255,0.92); border-radius: 28px; padding: 26px 24px; border: 1px solid rgba(255,255,255,0.88); box-shadow: 0 18px 34px rgba(180,140,150,0.10); margin-bottom: 24px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;">
                <h3 style="margin:0; font-size:1.9rem; font-weight:500; color:#1c1c1e;">Transactions days</h3>
                <div style="width:48px;height:48px;border-radius:999px;border:1px solid rgba(28,28,30,0.08);display:flex;align-items:center;justify-content:center;color:#a1a7b3;font-size:1.7rem;">⋮</div>
            </div>
            <div style="border-top:1px solid rgba(28,28,30,0.08); margin-bottom:20px;"></div>
            <div style="display:flex; align-items:center; gap:14px; margin-bottom:22px; flex-wrap:wrap;">
                <div style="font-size:3rem; line-height:1; color:#1c1c1e;">{window_days}</div>
                <div style="font-size:1.5rem; color:#5e6472;">Days</div>
                <div style="margin-left:12px; width:54px;height:54px;border-radius:999px;border:1px solid rgba(28,28,30,0.08);display:flex;align-items:center;justify-content:center;font-size:2rem;color:#1c1c1e;">{active_days}</div>
                <div style="font-size:1.35rem; color:#4b5563;">{month_label}</div>
                <div style="margin-left:auto; display:flex; gap:10px; flex-wrap:wrap;">
                    <span style="padding:8px 12px; border-radius:999px; background:#eef8f1; color:#2f8c57; font-size:0.88rem;">Paid EMI: {paid_days}</span>
                    <span style="padding:8px 12px; border-radius:999px; background:#fff0eb; color:#d86a43; font-size:0.88rem;">Delayed: {missed_days}</span>
                    <span style="padding:8px 12px; border-radius:999px; background:#eef1ff; color:#4d61e8; font-size:0.88rem;">Inflow days: {inflow_days}</span>
                    <span style="padding:8px 12px; border-radius:999px; background:#f1eeff; color:#7a69d9; font-size:0.88rem;">Outflow days: {outflow_days}</span>
                </div>
            </div>
            <div style="border-top:1px solid rgba(28,28,30,0.08); padding-top:18px;">
                <div style="display:grid; grid-template-columns: repeat(7, 48px); gap:12px 14px; justify-content:start; margin-bottom:16px;">{week_labels}</div>
                <div style="display:grid; grid-template-columns: repeat(7, 48px); gap:12px 14px; justify-content:start;">{cells_html}</div>
            </div>
            <div style="margin-top:22px; border-top:1px solid rgba(28,28,30,0.08); padding-top:18px;">
                <p style="margin:0 0 10px 0; color:#636366; font-size:0.95rem; line-height:1.45;">Green shows successful EMI payments, orange shows missed or delayed EMI days, blue marks business inflows, and purple marks business outflows in this borrower's latest activity window.</p>
                <div style="display:flex; gap:20px; flex-wrap:wrap; color:#4b5563; font-size:0.95rem;">
                    <span><strong>Rs {paid_amount:,.0f}</strong> EMI paid</span>
                    <span><strong>Rs {missed_amount:,.0f}</strong> delayed/default EMI</span>
                    <span><strong>Rs {inflow_amount:,.0f}</strong> inflow received</span>
                    <span><strong>Rs {outflow_amount:,.0f}</strong> outflow posted</span>
                </div>
            </div>
        </div>
        """
    ).strip()


def get_branch_details(branch_name: str) -> dict:
    branch_clean = str(branch_name).lower().replace(" ", "_")
    return {
        "email": f"rm.{branch_clean}@bandhanbank.co.in",
        "phone": "+91 80 4910 2883",
        "name": f"{branch_name} Branch"
    }


def generate_flagged_reasoning(borrower_id: str, detector) -> list:
    row = detector._borrower_row(borrower_id)
    reasons = []
    
    dpd = int(row["days_past_due"])
    missed_90d = int(row["missed_payments_90d"])
    consistency = float(row["repayment_consistency"])
    inflow_stability = float(row["inflow_stability"])
    balance_trend = float(row["balance_trend"])
    regional_stress = float(row["regional_stress_factor"])
    
    if dpd > 0:
        reasons.append(f"⚠️ **Delayed Payment DPD**: Account is currently {dpd} days past due on outstanding repayments.")
    if missed_90d > 0:
        reasons.append(f"⚠️ **Missed EMIs**: You have missed {missed_90d} scheduled repayments over the past 90 days.")
    if consistency < 0.85:
        reasons.append(f"📉 **Repayment Consistency Stress**: Your consistency score dropped to {consistency:.0%}, signaling cash-flow timing friction.")
    if inflow_stability < 0.80:
        reasons.append(f"📉 **Inflow Stability Stress**: Income volatility detected on business operations ledger (stability metric: {inflow_stability:.2f}).")
    if balance_trend < -0.1:
        reasons.append(f"📉 **Declining Cash Reserves**: Active bank ledger balances show a declining trend of {-balance_trend:.1%}, reducing repayment buffers.")
    if regional_stress >= 0.55:
        reasons.append(f"🌍 **Macroeconomic Environment**: Elevated default stress rates ({regional_stress:.2f}) observed in your business region.")
    
    try:
        G = detector.graph
        if borrower_id in G:
            neighbors = list(G.neighbors(borrower_id))
            high_risk_neighbors = 0
            for n in neighbors:
                if not str(n).startswith("SCHEME::") and not str(n).startswith("REGION::") and not str(n).startswith("CATEGORY::"):
                    if detector.calculate_risk_score(n) >= 50:
                        high_risk_neighbors += 1
            if high_risk_neighbors > 0:
                reasons.append(f"🕸️ **Network Stress Contagion**: Connected peer entities in your regional cohort show high default stress flags.")
    except Exception:
        pass
        
    if not reasons:
        reasons.append("🟢 Your account is stable and within normal compliance health limits. Keep regular deposits to maintain this profile!")
        
    return reasons


def render_borrower_timeline(borrower_id: str, detector):
    row = detector._borrower_row(borrower_id)
    dpd = int(row["days_past_due"])
    risk = detector.calculate_risk_score(borrower_id)
    
    try:
        from audit_compliance_engine import AuditComplianceService
        logs = AuditComplianceService.get_logs()
        user_logs = logs[logs["borrower_id"] == borrower_id]
        warning_sent = not user_logs[user_logs["action_performed"] == "Warning Email Sent"].empty
        payment_done = not user_logs[user_logs["action_performed"] == "Payment Completed"].empty
    except Exception:
        warning_sent = False
        payment_done = False
        
    steps = [
        ("Loan Issued", "Success", True),
        ("Healthy Borrower", "Success", dpd == 0 and risk < 45),
        ("Missed EMI", "Warning" if dpd > 0 else "Pending", dpd > 0),
        ("Risk Increased", "Danger" if risk >= 70 else "Warning" if risk >= 45 else "Pending", risk >= 45),
        ("Warning Sent", "Warning" if warning_sent else "Pending", warning_sent),
        ("Payment Completed", "Success" if payment_done else "Pending", payment_done),
        ("Health Improved", "Success" if (payment_done and risk < 45) else "Pending", payment_done and risk < 45),
        ("Risk Reduced", "Success" if (payment_done and risk < 35) else "Pending", payment_done and risk < 35)
    ]
    
    html = """
    <div style="display: flex; justify-content: space-between; align-items: center; overflow-x: auto; padding: 20px 10px; margin-bottom: 24px; background: rgba(255,255,255,0.4); border: 1px solid rgba(0,0,0,0.04); border-radius: 20px;">
    """
    for idx, (name, status, active) in enumerate(steps):
        if active:
            if status == "Success":
                color = "#22c55e"
            elif status == "Danger":
                color = "#ef4444"
            else:
                color = "#f59e0b"
            border_style = f"border: 3px solid {color}; background: {color}15; font-weight: 700; color: #1c1c1e;"
            dot_color = color
        else:
            border_style = "border: 2px solid #e5e5ea; background: white; color: #8e8e93;"
            dot_color = "#e5e5ea"
            
        html += f"""
        <div style="text-align: center; flex: 1; min-width: 90px; display: flex; flex-direction: column; align-items: center; position: relative;">
            <div style="width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; {border_style} font-size: 11px;">
                {idx + 1}
            </div>
            <div style="font-size: 0.72rem; margin-top: 8px; font-weight: 600; color: { '#1c1c1e' if active else '#8e8e93' }">{name}</div>
        </div>
        """
        if idx < len(steps) - 1:
            line_color = dot_color if active else "#e5e5ea"
            html += f"""
            <div style="height: 2px; flex: 0.5; background: {line_color}; min-width: 20px; margin-top: -16px;"></div>
            """
            
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_post_payment_success_page():
    data = st.session_state.payment_success_data
    
    st.markdown(
        """
        <style>
        .success-box {
            background: rgba(255,255,255,0.92) !important;
            border-radius: 32px !important;
            padding: 40px 44px !important;
            border: 1px solid rgba(255,255,255,0.95) !important;
            box-shadow: 0 24px 48px rgba(180,140,150,0.14) !important;
            max-width: 650px;
            margin: 40px auto;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown('<div class="success-box">', unsafe_allow_html=True)
    
    st.markdown(
        """
        <div style="font-size: 4rem; margin-bottom: 16px;">🎉</div>
        <h2 style="font-size:2.2rem; font-weight:800; color:#10b981; margin-bottom:4px;">Payment Successful</h2>
        <p style="color:#636366; font-size:0.95rem; font-weight:500;">Your repayment transaction has been successfully processed in Razorpay test mode.</p>
        <div style="height:1px; background:rgba(0,0,0,0.06); margin:24px 0;"></div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("##### ⚙️ Recalculating Borrower Health...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    import time
    
    status_text.markdown("🔄 *Re-evaluating days past due (DPD) criteria...*")
    progress_bar.progress(25)
    time.sleep(0.4)
    
    status_text.markdown("🔄 *Recalculating business cash-flow coverage ratio...*")
    progress_bar.progress(50)
    time.sleep(0.4)
    
    status_text.markdown("🔄 *Propagating GNN peer network threat updates...*")
    progress_bar.progress(75)
    time.sleep(0.4)
    
    status_text.markdown("✅ *Credit scores re-evaluation complete!*")
    progress_bar.progress(100)
    time.sleep(0.2)
    
    progress_bar.empty()
    status_text.empty()
    
    # Display comparison card
    st.markdown(
        f"""
        <div style="background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.12); border-radius: 20px; padding: 20px; text-align: left; margin-bottom: 24px;">
            <h4 style="margin: 0 0 12px 0; color: #10b981;">📈 Credit Profile Re-evaluation Results</h4>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="color:#636366; font-weight:500;">Health Score</span>
                <span style="font-weight: 700; color:#1c1c1e;">{data['old_health']}/100 &rarr; <span style="color:#10b981;">{data['new_health']}/100</span></span>
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="color:#636366; font-weight:500;">Risk Band</span>
                <span style="font-weight: 700; color:#1c1c1e;">{data['old_risk_level']} &rarr; <span style="color:#10b981;">{data['new_risk_level']}</span></span>
            </div>
            
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="color:#636366; font-weight:500;">Outstanding Dues</span>
                <span style="font-weight: 700; color:#1c1c1e;">₹{data['old_outstanding']:,.2f} &rarr; <span style="color:#10b981;">₹{data['new_outstanding']:,.2f}</span></span>
            </div>

            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="color:#636366; font-weight:500;">Days Past Due</span>
                <span style="font-weight: 700; color:#1c1c1e;">{int(data['old_dpd'])} days &rarr; <span style="color:#10b981;">{int(data['new_dpd'])} days</span></span>
            </div>
            
            <div style="display: flex; justify-content: space-between;">
                <span style="color:#636366; font-weight:500;">Estimated Recovery Probability</span>
                <span style="font-weight: 700; color:#1c1c1e;">{data['recovery_prob_old']}% &rarr; <span style="color:#10b981;">{data['recovery_prob_new']}%</span></span>
            </div>
        </div>
        """, unsafe_allow_html=True
    )
    
    st.markdown(
        """
        <p style="font-size: 1.05rem; color: #1c1c1e; font-weight: 600; line-height: 1.5; margin-bottom: 24px;">
            Your financial health has successfully improved.<br>
            Continue timely repayments to maintain a healthy borrower profile.
        </p>
        """, unsafe_allow_html=True
    )
    
    if st.button("Return to Recovery Hub", type="primary", use_container_width=True):
        st.session_state.pop("payment_success_data", None)
        st.rerun()
        
    st.markdown('</div>', unsafe_allow_html=True)


def render_borrower_dashboard(borrower_id: str) -> None:
    # 1. Access verification logging
    if f"logged_view_{borrower_id}" not in st.session_state:
        st.session_state[f"logged_view_{borrower_id}"] = True
        audit_log("Borrower Actions", "Health Dashboard Viewed", borrower_id=borrower_id, reason="Borrower logged in and accessed credit health dashboard")

    # 2. Redirect to post-payment success screen if set
    if st.session_state.get("payment_success_data") is not None:
        render_post_payment_success_page()
        st.stop()

    # Load borrower properties
    transparency = detector.analyze_borrower(borrower_id).as_dict()
    borrower_profile = borrowers_df[borrowers_df["borrower_id"] == borrower_id].iloc[0]
    borrower_state = repo.get_borrower(borrower_id) or repo.ensure_borrower(borrower_id, transparency["name"])
    
    borrower_name = transparency.get("name", "Borrower").title()

    # Enterprise Dark Espresso Sidebar matching Bandhan Loan Recovery Mgmt reference
    sidebar_slot = st.sidebar.empty()
    with sidebar_slot.container():
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 12px; padding: 4px 0 20px 0; border-bottom: 1px solid #3E2B20; margin-bottom: 16px;">
                <div style="
                    width: 36px; height: 36px; min-width: 36px;
                    background: rgba(212, 163, 115, 0.2);
                    border: 1px solid rgba(212, 163, 115, 0.45);
                    border-radius: 8px;
                    display: flex; align-items: center; justify-content: center;
                    font-weight: 800; font-size: 1.2rem; color: #D4A373;
                ">B</div>
                <div>
                    <div style="font-size: 0.92rem; font-weight: 800; letter-spacing: 1.2px; color: #FFFFFF; line-height: 1.1;">BANDHAN</div>
                    <div style="font-size: 0.65rem; font-weight: 600; color: #A8988B; letter-spacing: 0.8px;">BORROWER PORTAL</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        b_tabs = [
            ("🏥", "My Recovery Hub"),
            ("📅", "Payments & Ledgers"),
            ("🛠️", "Request Restructuring"),
        ]
        curr_b_tab = st.session_state.get("borrower_active_tab", "🏥 My Recovery Hub")
        for icon, label in b_tabs:
            tab_name = f"{icon} {label}"
            is_active = (curr_b_tab == tab_name)
            if st.button(
                f"{icon}  {label}",
                key=f"b_nav_{label.lower().replace(' ', '_')}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.borrower_active_tab = tab_name
                st.rerun()

        st.markdown("<div style='border-top: 1px solid #3E2B20; margin-top: 24px; margin-bottom: 12px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sidebar-signout-container">', unsafe_allow_html=True)
        if st.button("Sign Out", key="borrower_sidebar_logout", use_container_width=True):
            logout()
        st.markdown('</div>', unsafe_allow_html=True)

    # Top Breadcrumb and Profile Header
    bc_col, profile_col = st.columns([6, 3])
    with bc_col:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; font-size: 0.84rem; color: #8C7E72; font-weight: 600; padding: 2px 0 12px 0;">
                <span>Home</span>
                <span style="color: #C6B9A8;">›</span>
                <span style="color: #2C1E16;">Borrower Portal</span>
                <span style="color: #C6B9A8;">›</span>
                <span style="color: #6B3F23;">{borrower_id}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with profile_col:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: flex-end; gap: 10px; margin-bottom: 8px;">
                <div style="
                    background: #FFFFFF; border: 1px solid #DFD7CC; border-radius: 999px; padding: 3px 12px 3px 6px;
                    display: flex; align-items: center; gap: 8px; box-shadow: 0 1px 2px rgba(44,30,22,0.04);
                ">
                    <div style="
                        width: 28px; height: 28px; border-radius: 50%; background: #6B3F23; color: #FFFFFF;
                        display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700;
                    ">{borrower_name[:2].upper()}</div>
                    <div style="text-align: left; line-height: 1.15;">
                        <div style="font-size: 0.8rem; font-weight: 700; color: #2C1E16;">{escape(borrower_name)}</div>
                        <div style="font-size: 0.65rem; color: #8C7E72;">Branch: {borrower_profile['branch']}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div style="margin-bottom: 16px;">
            <h1 style="font-size: 1.95rem; font-weight: 800; color: #2C1E16; margin: 0 0 4px 0; letter-spacing: -0.5px;">Hello, {escape(borrower_name)} 👋</h1>
            <p style="font-size: 0.88rem; color: #6E5F52; margin: 0;">Borrower ID: <strong>{borrower_id}</strong> &nbsp;|&nbsp; Branch: <strong>{borrower_profile['branch']}</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Chronological lifecycle timeline
    render_borrower_timeline(borrower_id, detector)

    # Core Hub Tabs selectors (using session state variable)
    if "borrower_active_tab" not in st.session_state:
        st.session_state.borrower_active_tab = "🏥 My Recovery Hub"
        
    c_tab1, c_tab2, c_tab3 = st.columns(3)
    with c_tab1:
        if st.button("🏥 My Recovery Hub", use_container_width=True, type="primary" if st.session_state.borrower_active_tab == "🏥 My Recovery Hub" else "secondary"):
            st.session_state.borrower_active_tab = "🏥 My Recovery Hub"
            st.rerun()
    with c_tab2:
        if st.button("📅 Payments & Ledgers", use_container_width=True, type="primary" if st.session_state.borrower_active_tab == "📅 Payments & Ledgers" else "secondary"):
            st.session_state.borrower_active_tab = "📅 Payments & Ledgers"
            st.rerun()
    with c_tab3:
        if st.button("🛠️ Request Restructuring", use_container_width=True, type="primary" if st.session_state.borrower_active_tab == "🛠️ Request Restructuring" else "secondary"):
            st.session_state.borrower_active_tab = "🛠️ Request Restructuring"
            st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ─────────────────────────────────────────────
    # TAB 1: SMART RECOVERY HUB
    # ─────────────────────────────────────────────
    if st.session_state.borrower_active_tab == "🏥 My Recovery Hub":
        # Summary Cards
        sum_col1, sum_col2, sum_col3, sum_col4, sum_col5 = st.columns(5)
        
        # Calculate Next EMI Due Date
        dpd = int(borrower_profile["days_past_due"])
        if dpd > 0:
            import datetime
            due_date = (datetime.date.today() - datetime.timedelta(days=dpd)).strftime("%Y-%m-%d")
        else:
            import datetime
            today = datetime.date.today()
            if today.month == 12:
                due_date = f"{today.year + 1}-01-05"
            else:
                due_date = f"{today.year}-{today.month + 1:02d}-05"
                
        def render_summary_pill(label: str, value: str, theme: str) -> str:
            colors = {
                "red": ("rgba(239, 68, 68, 0.08)", "#b91c1c", "border: 1px solid rgba(239, 68, 68, 0.18)"),
                "green": ("rgba(34, 197, 94, 0.08)", "#15803d", "border: 1px solid rgba(34, 197, 94, 0.18)"),
                "orange": ("rgba(245, 158, 11, 0.08)", "#b45309", "border: 1px solid rgba(245, 158, 11, 0.18)"),
                "blue": ("rgba(59, 130, 246, 0.08)", "#1d4ed8", "border: 1px solid rgba(59, 130, 246, 0.18)")
            }
            bg, txt, border = colors.get(theme, ("rgba(255,255,255,0.4)", "#1c1c1e", "border: 1px solid rgba(0,0,0,0.06)"))
            return f"""
            <div style="background:{bg}; {border}; border-radius:16px; padding:16px; text-align:center; min-height:100px; display:flex; flex-direction:column; justify-content:center; box-shadow:0 8px 16px rgba(0,0,0,0.01);">
                <span style="font-size:0.72rem; color:#636366; text-transform:uppercase; font-weight:700; letter-spacing:0.5px; margin-bottom:6px;">{label}</span>
                <span style="font-size:1.25rem; font-weight:800; color:{txt};">{value}</span>
            </div>
            """
            
        with sum_col1:
            st.markdown(render_summary_pill("Loan Health Score", f"{transparency['health_score']}/100", "green" if transparency['health_score']>=70 else "orange" if transparency['health_score']>=45 else "red"), unsafe_allow_html=True)
        with sum_col2:
            st.markdown(render_summary_pill("Risk Band", transparency["risk_level"], "green" if transparency['risk_score']<35 else "orange" if transparency['risk_score']<70 else "red"), unsafe_allow_html=True)
        with sum_col3:
            st.markdown(render_summary_pill("Outstanding Amount", f"₹{borrower_profile['outstanding_amount']:,.2f}", "blue"), unsafe_allow_html=True)
        with sum_col4:
            st.markdown(render_summary_pill("Next EMI Due Date", due_date, "orange" if dpd > 0 else "blue"), unsafe_allow_html=True)
        with sum_col5:
            st.markdown(render_summary_pill("Loan Status", borrower_state.get("status", "ACTIVE").replace("_", " "), "green" if borrower_state.get("status") == "ACTIVE" else "orange"), unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2. Borrower Health Section
        col_health, col_why = st.columns([1.1, 1])
        
        with col_health:
            st.markdown("### 🏥 Loan Health Diagnostics")
            st.markdown(render_segmented_health_bar(transparency['health_score'], "Your Profile Health"), unsafe_allow_html=True)
            st.markdown(f"📈 **Peer Cohort Baseline**: {transparency['peer_score']}/100 (average health score of similar borrowers in stand-up/MSME schemes)")
            st.markdown(f"🌍 **Regional Stress factor**: {transparency['regional_stress_factor']} (local economic stress context)")
            st.markdown(f"🕸️ **Network Exposure Score**: {transparency['graph_degree']} (number of operational risk connections)")
            
            # Risk trend
            trend = "Declining 📉" if dpd > 15 else "Stable 📊" if dpd == 0 else "Proactive 📈"
            color = "#ef4444" if dpd > 15 else "#3b82f6" if dpd == 0 else "#22c55e"
            st.markdown(f"📉 **Risk Trend**: <span style='color:{color}; font-weight:700;'>{trend}</span>", unsafe_allow_html=True)
            
        with col_why:
            st.markdown(
                """
                <div style="background: rgba(255,95,46,0.06); border: 1px solid rgba(255,95,46,0.14); border-radius: 20px; padding: 24px; min-height: 250px;">
                    <h4 style="margin: 0 0 12px 0; color: #ff5f2e;">🧠 Why was my account flagged?</h4>
                    <p style="font-size:0.88rem; color:#48484a; line-height:1.45; margin-bottom:16px;">
                        Our GNN reasoning engine evaluates your cash-flow consistency, payment timeline logs, and regional risk exposure:
                    </p>
                """, unsafe_allow_html=True
            )
            reasons = generate_flagged_reasoning(borrower_id, detector)
            for r in reasons:
                st.markdown(f"<div style='font-size:0.88rem; color:#1c1c1e; margin-bottom:8px; line-height:1.4;'>{r}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        st.markdown("<br><hr style='border: 0; height: 1px; background: rgba(0,0,0,0.06);'><br>", unsafe_allow_html=True)
        
        # 3. Recovery Action Center
        st.markdown("### ⚡ Recovery Action Center")
        st.markdown("Select a repayment action or request relief below.")
        
        col_act1, col_act2, col_act3, col_act4 = st.columns(4)
        
        with col_act1:
            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.7); border:1px solid rgba(0,0,0,0.06); border-radius:18px; padding:20px; min-height:230px; display:flex; flex-direction:column; justify-content:space-between; box-shadow:0 8px 24px rgba(0,0,0,0.015);">
                    <div>
                        <div style="font-size:1.6rem; margin-bottom:8px;">💳</div>
                        <h4 style="margin:0 0 6px 0; color:#1c1c1e;">Pay Scheduled EMI</h4>
                        <p style="font-size:0.8rem; color:#636366; line-height:1.4; margin:0;">Pay your scheduled monthly EMI dues securely.</p>
                        <div style="font-size:1.15rem; font-weight:800; color:#22c55e; margin-top:8px;">₹{borrower_profile['emi_amount']:,.2f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
            if st.button("Pay Full EMI Now", key="pay_full_emi_btn", type="primary", use_container_width=True):
                st.session_state.checkout_active = True
                st.session_state.checkout_pay_type = "Full EMI Payment"
                st.rerun()
                
        with col_act2:
            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.7); border:1px solid rgba(0,0,0,0.06); border-radius:18px; padding:20px; min-height:230px; display:flex; flex-direction:column; justify-content:space-between; box-shadow:0 8px 24px rgba(0,0,0,0.015);">
                    <div>
                        <div style="font-size:1.6rem; margin-bottom:8px;">💵</div>
                        <h4 style="margin:0 0 6px 0; color:#1c1c1e;">Partial Payment</h4>
                        <p style="font-size:0.8rem; color:#636366; line-height:1.4; margin:0;">Reduce your outstanding loan balance with any custom amount.</p>
                        <div style="font-size:0.9rem; font-weight:600; color:#8e8e93; margin-top:8px;">Outstanding: ₹{borrower_profile['outstanding_amount']:,.2f}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
            if st.button("Enter Custom Dues", key="pay_partial_emi_btn", use_container_width=True):
                st.session_state.checkout_active = True
                st.session_state.checkout_pay_type = "Partial EMI Payment"
                st.rerun()
                
        with col_act3:
            st.markdown(
                """
                <div style="background: rgba(255,255,255,0.7); border:1px solid rgba(0,0,0,0.06); border-radius:18px; padding:20px; min-height:230px; display:flex; flex-direction:column; justify-content:space-between; box-shadow:0 8px 24px rgba(0,0,0,0.015);">
                    <div>
                        <div style="font-size:1.6rem; margin-bottom:8px;">🛠️</div>
                        <h4 style="margin:0 0 6px 0; color:#1c1c1e;">Request Restructure</h4>
                        <p style="font-size:0.8rem; color:#636366; line-height:1.4; margin:0;">Apply for temporary EMI adjustment or repayment timeline holiday.</p>
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
            if st.button("Apply Restructure", key="nav_restruct_btn", use_container_width=True):
                st.session_state.borrower_active_tab = "🛠️ Request Restructuring"
                st.rerun()
                
        with col_act4:
            branch_details = get_branch_details(borrower_profile["branch"])
            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.7); border:1px solid rgba(0,0,0,0.06); border-radius:18px; padding:20px; min-height:230px; display:flex; flex-direction:column; justify-content:space-between; box-shadow:0 8px 24px rgba(0,0,0,0.015);">
                    <div>
                        <div style="font-size:1.6rem; margin-bottom:8px;">📞</div>
                        <h4 style="margin:0 0 6px 0; color:#1c1c1e;">Branch Help Desk</h4>
                        <p style="font-size:0.78rem; color:#636366; line-height:1.35; margin:0;">
                            <b>Email:</b> {branch_details['email']}<br>
                            <b>Tel:</b> {branch_details['phone']}<br>
                            Speak to your dedicated Relationship Manager.
                        </p>
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
            if st.button("Request Callback", key="rm_callback_btn", use_container_width=True):
                audit_log(
                    category="Recovery Operations",
                    action="Branch Visit Scheduled",
                    borrower_id=borrower_id,
                    reason="Borrower requested callback consultation from Relationship Manager"
                )
                st.success("✅ Callback requested! An officer will call you within 24 hours.")
                
        # ─────────────────────────────────────────────
        # REPAYMENT AREA & LIVE IMPACT PREVIEW
        # ─────────────────────────────────────────────
        if st.session_state.get("checkout_active"):
            st.markdown("<br><hr style='border: 0; height: 1px; background: rgba(0,0,0,0.06);'><br>", unsafe_allow_html=True)
            st.markdown("### 💳 Razorpay Repayment Portal")
            
            pay_options_list = ["Full EMI Payment", "Partial EMI Payment", "Outstanding Charges", "Advance EMI Payment"]
            init_idx = pay_options_list.index(st.session_state.get("checkout_pay_type", "Full EMI Payment"))
            
            c_pay_type = st.selectbox("Select Payment Options", pay_options_list, index=init_idx)
            
            outstanding_amount = float(borrower_profile["outstanding_amount"])
            emi_amount = float(borrower_profile["emi_amount"])
            
            if c_pay_type == "Full EMI Payment":
                pay_amt = emi_amount
                st.info(f"Dues Resolved: ₹{pay_amt:,.2f}")
            elif c_pay_type == "Outstanding Charges":
                pay_amt = outstanding_amount
                st.info(f"Dues Resolved: ₹{pay_amt:,.2f}")
            elif c_pay_type == "Advance EMI Payment":
                pay_amt = emi_amount * 2
                st.info(f"Dues Resolved: ₹{pay_amt:,.2f}")
            else:
                pay_amt = st.slider("Payment Amount (₹)", min_value=1000.0, max_value=outstanding_amount, value=float(emi_amount*0.5), step=500.0)
                
            # LIVE IMPACT PREVIEW
            st.markdown("#### 📈 Live Impact Preview")
            st.markdown("See the projected impact of this repayment on your credit profile before checkout:")
            
            impact = RecoveryPortalEngine.simulate_impact(borrower_id, pay_amt, detector)
            
            st.markdown(
                f"""
                <div style="background: rgba(34,197,94,0.05); border: 1px dashed rgba(34,197,94,0.3); border-radius: 20px; padding: 24px; margin-bottom: 24px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                        <span style="color:#636366; font-weight:500;">Projected Loan Health Score</span>
                        <span style="font-weight:700; color:#1c1c1e;">{impact['current_health']}/100 &rarr; <span style="color:#22c55e;">{impact['simulated_health']}/100</span></span>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                        <span style="color:#636366; font-weight:500;">Projected Risk Band</span>
                        <span style="font-weight:700; color:#1c1c1e;">{impact['current_risk_level']} &rarr; <span style="color:#22c55e;">{impact['simulated_risk_level']}</span></span>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                        <span style="color:#636366; font-weight:500;">Outstanding Balance after payment</span>
                        <span style="font-weight:700; color:#1c1c1e;">₹{impact['current_outstanding']:,.2f} &rarr; <span style="color:#22c55e;">₹{impact['simulated_outstanding']:,.2f}</span></span>
                    </div>
                    <div style="display:flex; justify-content:space-between;">
                        <span style="color:#636366; font-weight:500;">Estimated Profile Recovery Probability</span>
                        <span style="font-weight:700; color:#1c1c1e;">{impact['current_recovery_prob']}% &rarr; <span style="color:#22c55e;">{impact['simulated_recovery_prob']}%</span></span>
                    </div>
                </div>
                """, unsafe_allow_html=True
            )
            
            if st.button("Proceed to Razorpay Checkout", type="primary", use_container_width=True):
                st.session_state.razorpay_modal_active = True
                st.rerun()
                
        if st.session_state.get("razorpay_modal_active"):
            st.markdown(
                f"""
                <div style="background: rgba(15,23,42,0.92); border: 2px solid rgba(255,255,255,0.15); border-radius: 28px; padding: 32px; margin-top:20px; box-shadow: 0 30px 60px rgba(0,0,0,0.5);">
                    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:16px; margin-bottom:20px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="background:#1d4ed8; color:white; font-weight:800; font-size:0.9rem; padding:4px 10px; border-radius:6px;">R</span>
                            <span style="color:white; font-weight:800; font-size:1.15rem; letter-spacing:-0.5px;">Razorpay Checkout</span>
                        </div>
                        <span style="background:rgba(255,255,255,0.1); color:rgba(255,255,255,0.7); font-size:0.75rem; font-weight:700; padding:4px 8px; border-radius:12px; text-transform:uppercase;">Test Mode</span>
                    </div>
                    
                    <div style="color:white; margin-bottom:20px;">
                        <span style="font-size:0.85rem; color:rgba(255,255,255,0.6);">PAYMENT AMOUNT</span>
                        <div style="font-size:1.8rem; font-weight:800; color:#38bdf8;">₹{pay_amt:,.2f}</div>
                    </div>
                """, unsafe_allow_html=True
            )
            
            pay_opt = st.selectbox("Select Repayment Gateway Method", ["UPI / GPay / PhonePe", "Credit / Debit Card", "Net Banking"])
            
            if pay_opt == "UPI / GPay / PhonePe":
                vpa = st.text_input("Enter UPI Virtual Payment Address (VPA)", placeholder="username@upi")
            elif pay_opt == "Credit / Debit Card":
                cc_num = st.text_input("Card Number", placeholder="4111 2222 3333 4444")
                cc_cols = st.columns(2)
                cc_cols[0].text_input("Expiry Date", placeholder="MM/YY")
                cc_cols[1].text_input("CVV", type="password", placeholder="***")
                
            pay_cols = st.columns(2)
            if pay_cols[0].button("Authorize Payment (Razorpay Test Mode)", type="primary", key="auth_rzp_btn", use_container_width=True):
                result = RecoveryPortalEngine.process_payment(borrower_id, pay_amt, pay_opt, detector)
                if result.get("status") == "Success":
                    st.session_state.payment_success_data = result
                    st.session_state.pop("checkout_active", None)
                    st.session_state.pop("razorpay_modal_active", None)
                    st.rerun()
                else:
                    st.error(f"Payment Authorization Error: {result.get('message')}")
                    
            if pay_cols[1].button("Cancel Checkout", key="cancel_rzp_btn", use_container_width=True):
                st.session_state.pop("razorpay_modal_active", None)
                st.rerun()
                
            st.markdown("</div>", unsafe_allow_html=True)
            
    # ─────────────────────────────────────────────
    # TAB 2: PAYMENTS & LEDGERS
    # ─────────────────────────────────────────────
    elif st.session_state.borrower_active_tab == "📅 Payments & Ledgers":
        txns = transactions_df[transactions_df["borrower_id"] == borrower_id].sort_values("timestamp", ascending=False)
        
        st.markdown("### 🕒 Recent Ledger Activity Trail")
        borrower_window_label = st.selectbox(
            "Transaction Activity Window",
            ["30 Days", "60 Days", "90 Days", "All Available"],
            index=1,
            key=f"borrower_window_{borrower_id}",
        )
        borrower_window_days = {"30 Days": 30, "60 Days": 60, "90 Days": 90, "All Available": 10000}[borrower_window_label]
        st.markdown(render_transaction_days_card(txns, borrower_window_days), unsafe_allow_html=True)

        st.markdown("### 🗓️ Future Repayment Schedule")
        schedule_data = []
        for _, row in txns.iterrows():
            if pd.notnull(row["timestamp"]):
                date_str = row["timestamp"].strftime("%m/%d/%Y") if hasattr(row["timestamp"], "strftime") else str(row["timestamp"])
            else:
                date_str = ""
            schedule_data.append({
                "Payment Date": date_str,
                "Name": transparency["name"],
                "Payment Amount": f"Rs {row['amount']:,.2f}" if pd.notna(row['amount']) else "-",
                "Type": str(row["transaction_type"]).replace("_", " ").title(),
                "Status": "Paid" if str(row["status"]).upper() in ["COMPLETED", "SUCCESS", "PAID"] else str(row["status"]).title(),
                "Balance Left": f"Rs {row['balance_after']:,.2f}" if pd.notna(row['balance_after']) else "-"
            })
        schedule_df = pd.DataFrame(schedule_data)
        if not schedule_df.empty:
            render_glass_table(schedule_df, max_height=450)
        else:
            st.info("No payment history available.")
            
        st.markdown("<br><hr style='border: 0; height: 1px; background: rgba(0,0,0,0.06);'><br>", unsafe_allow_html=True)
        st.markdown("### 🕸️ Local Knowledge Contagion Network")
        st.caption("This visualization maps peer stress contagion vectors within a 2-hop radius of your business.")
        render_borrower_knowledge_graph(borrower_id, detector, portfolio_df)

    # ─────────────────────────────────────────────
    # TAB 3: REQUEST RESTRUCTURING
    # ─────────────────────────────────────────────
    elif st.session_state.borrower_active_tab == "🛠️ Request Restructuring":
        st.markdown("### 🛠️ Loan Restructuring Request Portal")
        st.markdown(
            """
            Submit a formal proposal to adjust your scheduled repayment parameters. 
            Applications are logged to the regulatory compliance database and reviewed by the Branch Officer within 48 hours.
            """
        )
        
        reqs = RecoveryPortalEngine.get_restructuring_requests()
        my_reqs = reqs[reqs["borrower_id"] == borrower_id].copy()
        
        if not my_reqs.empty:
            st.markdown("#### 🕒 My Submitted Proposals")
            display_reqs = my_reqs[[
                "request_id", "timestamp", "requested_emi", "recovery_timeline", "status", "admin_remarks"
            ]].rename(columns={
                "request_id": "Proposal ID",
                "timestamp": "Submitted On",
                "requested_emi": "Proposed EMI",
                "recovery_timeline": "Timeline Holiday",
                "status": "Verification Status",
                "admin_remarks": "Branch Review Remarks"
            })
            render_glass_table(display_reqs, max_height=200)
            st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("#### 📝 Apply for Restructuring Scheme")
        with st.form("borrower_restruct_form", border=True):
            r_reason = st.text_area("Reason for Restructuring Relief", placeholder="Detailed explanation of cash-flow stress or operational difficulty...")
            
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                r_employment = st.selectbox("Employment / Activity Status", ["Self-Employed", "Salaried", "Business Owner", "Other"])
                r_business = st.selectbox("Business Condition", ["Active & Operational", "Temporary Suspended", "Closed Operations", "N/A"])
                r_income = st.number_input("Current Monthly Net Income (₹)", min_value=0.0, value=50000.0, step=1000.0)
            with r_col2:
                r_timeline = st.selectbox("Expected Recovery Holiday Timeline", ["3 Months", "6 Months", "9 Months", "12 Months", "More than 12 Months"])
                r_emi = st.number_input(f"Proposed Adjusted Monthly EMI (Current: ₹{borrower_profile['emi_amount']:,.2f})", min_value=1000.0, value=float(borrower_profile['emi_amount']*0.5), step=500.0)
                
            r_submit = st.form_submit_button("Submit Restructuring Proposal →", type="primary")
            
        if r_submit:
            if not r_reason:
                st.error("Please supply a valid reason explaining your repayment difficulty.")
            else:
                import time
                with st.spinner("Submitting proposal to compliance database..."):
                    req_id = RecoveryPortalEngine.submit_restructuring_request(
                        borrower_id=borrower_id,
                        borrower_name=transparency["name"],
                        reason=r_reason,
                        employment_status=r_employment,
                        business_status=r_business,
                        monthly_income=r_income,
                        recovery_timeline=r_timeline,
                        requested_emi=r_emi
                    )
                    
                    # Log compliance audit event
                    audit_log(
                        category="Recovery Operations",
                        action="Loan Restructuring Recommended",
                        borrower_id=borrower_id,
                        reason=f"Borrower restructuring requested: {req_id}. Proposed EMI: ₹{r_emi:,.2f}"
                    )
                    
                    st.success(f"✅ Credit Restructuring Proposal successfully submitted! ID: {req_id}")
                    time.sleep(0.5)
                    st.rerun()


def render_borrower_knowledge_graph(borrower_id: str, detector, portfolio_df: pd.DataFrame) -> None:
    G_full = detector.get_networkx_graph()
    if not G_full or borrower_id not in G_full.nodes:
        st.info("Graph data not available for this borrower.")
        return

    import networkx as nx
    G = nx.ego_graph(G_full, borrower_id, radius=2)
    
    pos = nx.spring_layout(G, k=0.25, iterations=40, seed=42)
    
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.4, color='rgba(160, 160, 175, 0.5)'),
        hoverinfo='none',
        mode='lines'
    )

    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    node_symbol = []
    node_line_width = []
    node_line_color = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        node_type = G.nodes[node].get("type", "unknown")
        
        if node == borrower_id:
            node_size.append(22)
            node_line_width.append(4)
            node_line_color.append('rgba(0,0,0,0.9)')
        else:
            node_line_width.append(1)
            node_line_color.append('rgba(255,255,255,0.8)')
            
        if node_type == "borrower":
            try:
                b_risk = portfolio_df.loc[portfolio_df["borrower_id"] == node, "risk_score"].values[0]
                b_name = portfolio_df.loc[portfolio_df["borrower_id"] == node, "name"].values[0]
            except:
                b_risk = 50
                b_name = node
            node_color.append(b_risk)
            if node != borrower_id:
                node_size.append(12)
            node_symbol.append('circle')
            h_text = "<b>(Selected) " if node == borrower_id else ""
            node_text.append(f"{h_text}Borrower: {b_name}<br>GNN Risk: {b_risk}")
        elif node_type == "scheme":
            node_color.append(30)
            if node != borrower_id: node_size.append(24)
            node_symbol.append('diamond')
            node_text.append(f"Scheme Hub<br>{str(node).replace('SCHEME::', '')}")
        elif node_type == "region":
            node_color.append(75)
            if node != borrower_id: node_size.append(28)
            node_symbol.append('square')
            node_text.append(f"Region Hub<br>{str(node).replace('REGION::', '')}")
        else:
            node_color.append(50)
            if node != borrower_id: node_size.append(20)
            node_symbol.append('star')
            node_text.append(f"Category Hub<br>{str(node).replace('CATEGORY::', '')}")

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=True,
            colorscale='YlOrRd',
            color=node_color,
            size=node_size,
            symbol=node_symbol,
            colorbar=dict(
                thickness=10,
                title='Embedded Risk'
            ),
            line=dict(width=node_line_width, color=node_line_color)
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode='closest',
            height=450,
            margin=dict(b=10,l=5,r=5,t=10),
            paper_bgcolor="rgba(255,255,255,0.45)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
    )
    
    fig.update_layout(
        margin=dict(l=16, r=16, t=16, b=16),
        paper_bgcolor="rgba(255, 255, 255, 0.45)"
    )

    st.plotly_chart(fig, use_container_width=True, theme=None)


def render_ego_network(borrower_id: str, detector) -> None:
    import networkx as nx
    import plotly.graph_objects as go
    
    G = detector.get_networkx_graph()
    if borrower_id not in G:
        st.warning("Borrower not found in the graph.")
        return
        
    ego = nx.ego_graph(G, borrower_id, radius=2)
    pos = nx.spring_layout(ego, seed=42)
    
    edge_x = []
    edge_y = []
    for edge in ego.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='rgba(150, 150, 150, 0.5)'),
        hoverinfo='none',
        mode='lines'
    )
    
    node_x = []
    node_y = []
    node_color = []
    node_text = []
    node_size = []
    
    for node in ego.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        if node == borrower_id:
            color = '#3b82f6'  # Blue center
            size = 24
        elif str(node).startswith("SCHEME") or str(node).startswith("REGION") or str(node).startswith("CATEGORY"):
            color = '#9ca3af'  # Gray for attributes
            size = 12
        else:
            try:
                risk = detector.calculate_risk_score(node)
                if risk >= 70:
                    color = '#ef4444' # Red
                elif risk >= 45:
                    color = '#f59e0b' # Yellow
                else:
                    color = '#10b981' # Green
            except Exception:
                color = '#10b981'
            size = 16
            
        node_color.append(color)
        node_size.append(size)
        node_text.append(str(node))
        
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color=node_color,
            size=node_size,
            line=dict(width=1, color='white')
        ),
        text=node_text
    )
    
    fig = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0,l=0,r=0,t=0),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                 )
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True, theme=None)

def render_explainability(borrower_id: str) -> None:
    import requests
    import plotly.graph_objects as go
    try:
        resp = requests.get(
            f"{API_BASE_URL}/explain/{borrower_id}",
            timeout=10
        )
        data = resp.json()
        
        if resp.status_code != 200:
            st.error("Could not load explainability data.")
            return

        contributions = data["feature_contributions"]
        top_driver    = data["top_driver"]
        summary       = data["explanation_summary"]

        st.markdown(
            f"""
            <div style="
                background: rgba(255,255,255,0.65);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid rgba(255,255,255,0.85);
                border-radius: 24px;
                padding: 28px 32px;
                margin-top: 24px;
                box-shadow: 0 16px 40px 
                    rgba(180,140,150,0.12);
            ">
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 20px;
                    padding-bottom: 16px;
                    border-bottom: 1px solid 
                        rgba(28,28,30,0.08);
                ">
                    <div style="
                        width: 40px; height: 40px;
                        background: linear-gradient(
                            135deg, #174229, #2c5e3f);
                        border-radius: 12px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 1.2rem;
                    ">🔍</div>
                    <div>
                        <div style="font-weight:700; 
                            font-size:1.1rem; 
                            color:#1c1c1e;">
                            Explainable AI — Decision Breakdown
                        </div>
                        <div style="font-size:0.82rem; 
                            color:#636366;">
                            RBI SACHET Compliant · Feature 
                            Contribution Analysis
                        </div>
                    </div>
                    <div style="
                        margin-left: auto;
                        background: rgba(23,66,41,0.08);
                        border-radius: 999px;
                        padding: 6px 14px;
                        font-size: 0.8rem;
                        font-weight: 600;
                        color: #174229;
                    ">Explainable AI v1.0</div>
                </div>
                <p style="
                    margin: 0 0 20px 0;
                    color: #48484a;
                    font-size: 0.95rem;
                    line-height: 1.6;
                    padding: 12px 16px;
                    background: rgba(23,66,41,0.06);
                    border-radius: 12px;
                    border-left: 3px solid #174229;
                ">{summary}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Build horizontal bar chart
        features = list(contributions.keys())
        values   = list(contributions.values())

        # Colour each bar by contribution size
        bar_colors = []
        for v in values:
            if v >= 30:
                bar_colors.append("#ef4444")
            elif v >= 20:
                bar_colors.append("#f97316")
            elif v >= 10:
                bar_colors.append("#eab308")
            else:
                bar_colors.append("#22c55e")

        fig = go.Figure(go.Bar(
            x=values,
            y=features,
            orientation="h",
            marker_color=bar_colors,
            text=[f"{v:.1f}%" for v in values],
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Contribution: %{x:.1f}%"
                "<extra></extra>"
            )
        ))

        fig.update_layout(
            title="Feature Contribution to Risk Score",
            xaxis_title="Contribution (%)",
            xaxis=dict(
                range=[0, max(values) * 1.3],
                showgrid=True,
                gridcolor="rgba(120,120,135,0.16)",
                zeroline=False,
                tickfont=dict(color="#3a3a3c"),
            ),
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(
                    color="#1c1c1e", 
                    size=13
                ),
            ),
            height=380,
            margin=dict(l=16, r=60, t=48, b=32),
            paper_bgcolor="rgba(255,255,255,0.18)",
            plot_bgcolor="rgba(255,255,255,0.10)",
            font=dict(color="#1c1c1e"),
            showlegend=False,
        )

        st.plotly_chart(
            fig, use_container_width=True, theme=None
        )

        # Colour legend
        st.markdown(
            """
            <div style="display:flex; gap:16px; 
                flex-wrap:wrap; margin-top:8px;
                font-size:0.85rem;">
                <span style="display:flex; 
                    align-items:center; gap:6px;">
                    <span style="width:12px;height:12px;
                        border-radius:3px;
                        background:#ef4444;
                        display:inline-block;"></span>
                    <span style="color:#48484a;">
                        Major Driver (≥30%)
                    </span>
                </span>
                <span style="display:flex; 
                    align-items:center; gap:6px;">
                    <span style="width:12px;height:12px;
                        border-radius:3px;
                        background:#f97316;
                        display:inline-block;"></span>
                    <span style="color:#48484a;">
                        Significant (≥20%)
                    </span>
                </span>
                <span style="display:flex; 
                    align-items:center; gap:6px;">
                    <span style="width:12px;height:12px;
                        border-radius:3px;
                        background:#eab308;
                        display:inline-block;"></span>
                    <span style="color:#48484a;">
                        Moderate (≥10%)
                    </span>
                </span>
                <span style="display:flex; 
                    align-items:center; gap:6px;">
                    <span style="width:12px;height:12px;
                        border-radius:3px;
                        background:#22c55e;
                        display:inline-block;"></span>
                    <span style="color:#48484a;">
                        Minor Factor (&lt;10%)
                    </span>
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(
            f"Explainability unavailable: {e}"
        )

def process_nlp_query(query: str, df: pd.DataFrame) -> dict:
    import re
    q = query.lower()
    
    # --- LAYER 1: Intent Classification Layer ---
    intents = {
        "HIGH_RISK_DETECTION": ["high risk", "critical", "danger", "risky", "stress", "vulnerable"],
        "MISSED_REPAYMENT": ["missed", "delay", "default", "late", "past due", "history"],
        "LOW_RISK_TREND": ["low risk", "safe", "stable", "good standing", "reliable"],
        "EXPOSURE_QUERY": ["exposure", "value", "largest", "biggest", "amount", "top"],
        "REGION_FILTER": ["region", "area", "districts"],
    }
    
    scores = {intent: 0 for intent in intents}
    for intent, keywords in intents.items():
        for kw in keywords:
            if kw in q:
                scores[intent] += 1
                
    primary_intent = max(scores, key=scores.get)
    if scores[primary_intent] == 0:
        primary_intent = "GENERAL_PORTFOLIO_QUERY"
        
    # --- LAYER 2: Entity Extraction Layer ---
    extracted_entities = {}
    
    regions = df.get("region", pd.Series()).dropna().unique()
    for r in regions:
        if r.lower() in q:
            extracted_entities["region"] = r
            break
    schemes = df.get("loan_scheme", pd.Series()).dropna().unique()
    for s in schemes:
        if s.lower() in q:
            extracted_entities["scheme"] = s
            break
            
    risk_keywords = ["low", "moderate", "medium", "high", "critical"]
    for r_kw in risk_keywords:
        if re.search(rf"\b{r_kw}\b", q):
            extracted_entities["risk_level"] = r_kw
            break

    # --- LAYER 3: Reasoning & Response Generation Layer ---
    matched_df = df.copy()
    reason_parts = [f"Classified Intent as {primary_intent.replace('_', ' ')}"]
    
    if "region" in extracted_entities:
        matched_df = matched_df[matched_df["region"] == extracted_entities["region"]]
        reason_parts.append(f"isolated to '{extracted_entities['region']}'")
    if "scheme" in extracted_entities:
        matched_df = matched_df[matched_df["loan_scheme"] == extracted_entities["scheme"]]
        reason_parts.append(f"under scheme '{extracted_entities['scheme']}'")

    if "risk_level" in extracted_entities:
        RISK_MAP = {
            "low": ["LOW"],
            "moderate": ["MEDIUM", "MODERATE"],
            "medium": ["MEDIUM", "MODERATE"],
            "high": ["HIGH"],
            "critical": ["CRITICAL"]
        }
        allowed_risks = RISK_MAP.get(extracted_entities["risk_level"], [])
        if allowed_risks:
            if "risk_level" in matched_df.columns:
                matched_df = matched_df[matched_df["risk_level"].isin(allowed_risks)]
            elif "risk_band" in matched_df.columns:
                matched_df = matched_df[matched_df["risk_band"].isin(allowed_risks)]
            reason_parts.append(f"filtered to strict {extracted_entities['risk_level'].title()} Risk")

    sort_col = "risk_score" if "risk_score" in matched_df.columns else None
    sort_asc = False
    
    if primary_intent == "HIGH_RISK_DETECTION" and sort_col:
        matched_df = matched_df[matched_df["risk_score"] >= 50]
        reason_parts.append("exhibiting elevated High Risk markers")
    elif primary_intent == "LOW_RISK_TREND" and sort_col:
        matched_df = matched_df[matched_df["risk_score"] < 50]
        reason_parts.append("exhibiting Low Risk stability")
        sort_asc = True
    elif primary_intent == "MISSED_REPAYMENT" and "missed_payments_90d" in matched_df.columns:
        matched_df = matched_df[matched_df["missed_payments_90d"] > 0]
        reason_parts.append("showing recent missed payment behaviors")
    elif primary_intent == "EXPOSURE_QUERY" and "outstanding_amount" in matched_df.columns:
        sort_col = "outstanding_amount"
        reason_parts.append("prioritizing maximum outstanding financial value")
        
    summary = "System Response: \n" + " • ".join(reason_parts) + "."
    
    if sort_col:
        try:
            matched_df = matched_df.sort_values(sort_col, ascending=sort_asc).head(10)
        except Exception:
            matched_df = matched_df.head(10)
    else:
        matched_df = matched_df.head(10)
    
    if matched_df.empty:
        if "risk_level" in extracted_entities:
            action = "No intervention needed."
            insight = "No borrowers found for selected risk level."
        else:
            action = "No intervention needed."
            insight = "All clear: No targets matched precisely."
    else:
        avg_risk = matched_df["risk_score"].mean() if "risk_score" in matched_df.columns else 50
        if primary_intent == "LOW_RISK_TREND":
            action = "Maintain standard retention protocols. No urgent risk."
            insight = f"Stable performance. Average risk for this group is {avg_risk:.1f}."
        elif avg_risk >= 70 or primary_intent == "MISSED_REPAYMENT":
            action = "Urgent: Deploy branch recovery team immediately for physical verification."
            insight = f"Critical Exposure detected. Average risk profile requires action ({avg_risk:.1f})."
        elif avg_risk >= 50:
            action = "Action Required: Enqueue for tele-calling and SMS escalation protocols."
            insight = f"Moderate Exposure. Watchful tracking required (Avg risk {avg_risk:.1f})."
        else:
            action = "Standard protocol applies. Review in next cycle."
            insight = f"Stable subset. Routine monitoring sufficient."

    results = []
    for _, row in matched_df.iterrows():
        b_risk = float(row.get("risk_score", 0))
        if b_risk >= 70:
            band = "CRITICAL"
        elif b_risk >= 50:
            band = "HIGH"
        elif b_risk >= 30:
            band = "MODERATE"
        else:
            band = "LOW"
            
        results.append({
            "borrower_id": row.get("borrower_id", "Unknown"),
            "name": row.get("name", "Unknown"),
            "risk_band": band,
            "reason": f"Matches {primary_intent} [Risk: {b_risk}]"
        })
        
    return {
        "intent_detected": primary_intent,
        "entities_found": extracted_entities,
        "answer": summary,
        "matching_borrowers": results,
        "action": action,
        "insight": insight
    }

def render_satark_recover_tab(filtered: pd.DataFrame, portfolio_df: pd.DataFrame, detector, repo) -> None:
    # NLP Interface Section
    st.subheader("Portfolio Intelligence Query")
    
    st.markdown("""
        <div style="background: rgba(255,255,255,0.4); backdrop-filter: blur(10px); 
             border:1px solid rgba(255,255,255,0.6); padding: 16px; border-radius: 12px; margin-bottom: 24px;">
            <p style="margin:0; font-size:0.95rem; color:#48484a;">
                <b>Local Intelligence Engine Active</b> — Ask natural language questions about your portfolio internally. Data never leaves the device.
                <br><i>E.g., "Find high risk borrowers in Himachal Pradesh with missed payments."</i>
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    query = st.text_input("Ask Bandhan Intelligence:", placeholder="Type your query here...")
    
    col1, col2, col3, _ = st.columns([1.5, 1.5, 1.5, 2])
    trigger_q1 = col1.button("🔥 High-risk in Himachal", use_container_width=True)
    trigger_q2 = col2.button("⏱️ Missed payments", use_container_width=True)
    trigger_q3 = col3.button("🛡️ Stable Mudra loans", use_container_width=True)
    
    active_query = query
    if trigger_q1: active_query = "high risk borrowers in Himachal Pradesh"
    if trigger_q2: active_query = "borrowers with missed payments"
    if trigger_q3: active_query = "low risk stable mudra"
    
    if st.button("Ask Bandhan Intelligence", type="primary") or (active_query and active_query != ""):
        with st.spinner("Processing locally using Custom Intent Engine..."):
            import time
            time.sleep(0.4) # Artificial delay for UX feel
            ans = process_nlp_query(active_query, portfolio_df)
            
            e_str = " | ".join(f"{k.title()}: {v}" for k, v in ans["entities_found"].items()) if ans["entities_found"] else "None extracted"
            
            st.markdown(f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; padding:16px; border-radius:12px; margin-bottom:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #cbd5e1; padding-bottom:12px; margin-bottom:12px;">
                    <div>
                        <span style="font-size:0.8rem; text-transform:uppercase; color:#64748b; font-weight:700; letter-spacing:1px;">Detected Intent</span><br>
                        <span style="font-size:1.1rem; color:#0f172a; font-weight:600;">{ans['intent_detected'].replace('_', ' ')}</span>
                    </div>
                    <div style="text-align:right;">
                        <span style="font-size:0.8rem; text-transform:uppercase; color:#64748b; font-weight:700; letter-spacing:1px;">Entities Extracted</span><br>
                        <span style="font-size:0.95rem; color:#0f172a;">{e_str}</span>
                    </div>
                </div>
                <h4 style="margin:0 0 8px 0; color:#1e293b;">Query Answer</h4>
                <div style="color:#334155; font-size:1.05rem;">{ans['answer']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            c1.markdown(f"""
            <div style="background:#fffbeb; border:1px solid #fde68a; padding:16px; border-radius:12px; height: 100%;">
                <h4 style="margin:0 0 8px 0; color:#b45309;">Recommended Action</h4>
                <div style="color:#78350f;">{ans['action']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            c2.markdown(f"""
            <div style="background:#f0fdf4; border:1px solid #bbf7d0; padding:16px; border-radius:12px; height: 100%;">
                <h4 style="margin:0 0 8px 0; color:#15803d;">Key Insight 💡</h4>
                <div style="color:#166534;">{ans['insight']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("#### Matching Borrowers")
            if "risk_level" in ans["entities_found"]:
                st.caption(f"Filter: {ans['entities_found']['risk_level'].title()} Risk")
            if ans["matching_borrowers"]:
                render_glass_table(pd.DataFrame(ans["matching_borrowers"]), max_height=300)
            else:
                st.info("No matching borrowers to display based on your query criteria.")
                
    st.markdown("<br><hr><br>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────
    # RESTRUCTURING REQUESTS AUDITING & ACTIONS
    # ─────────────────────────────────────────────
    st.subheader("📋 Credit Restructuring Applications")
    st.markdown("Verify, approve, reject, or request more information for borrower restructuring proposals.")
    
    req_df = RecoveryPortalEngine.get_restructuring_requests()
    if req_df.empty:
        st.info("No active credit restructuring requests submitted.")
    else:
        pending_reqs = req_df[req_df["status"] == "PENDING"]
        
        # Display all proposals in a table
        display_reqs = req_df[[
            "request_id", "borrower_id", "borrower_name", "timestamp", "requested_emi", "recovery_timeline", "status"
        ]].rename(columns={
            "request_id": "Proposal ID",
            "borrower_id": "Borrower ID",
            "borrower_name": "Borrower Name",
            "timestamp": "Submitted On",
            "requested_emi": "Proposed EMI",
            "recovery_timeline": "Timeline Holiday",
            "status": "Status"
        })
        render_glass_table(display_reqs, max_height=220)
        
        if not pending_reqs.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            sel_req_id = st.selectbox("Select Restructuring Request to Review", pending_reqs["request_id"].tolist())
            req_row = pending_reqs[pending_reqs["request_id"] == sel_req_id].iloc[0]
            
            st.markdown(
                f"""
                <div style="background: rgba(255,255,255,0.4); border: 1px solid rgba(0,0,0,0.06); border-radius: 16px; padding: 18px; margin-bottom: 16px;">
                    <b>Borrower:</b> {req_row['borrower_name']} ({req_row['borrower_id']})<br>
                    <b>Proposed Adjusted EMI:</b> ₹{float(req_row['requested_emi']):,.2f}<br>
                    <b>Employment Status:</b> {req_row['employment_status']} | <b>Business Status:</b> {req_row['business_status']}<br>
                    <b>Monthly Net Income:</b> ₹{float(req_row['monthly_income']):,.2f} | <b>Proposed Timeline:</b> {req_row['recovery_timeline']}<br>
                    <b>Reason cited:</b> <i>"{req_row['reason']}"</i>
                </div>
                """, unsafe_allow_html=True
            )
            
            admin_rem = st.text_input("Remarks / Conditions for this decision", placeholder="Enter official review remarks...")
            
            col_dec1, col_dec2, col_dec3 = st.columns(3)
            with col_dec1:
                if st.button("✔️ Approve Proposal", key=f"app_req_{sel_req_id}", type="primary", use_container_width=True):
                    if not admin_rem:
                        st.error("Review remarks are required for approval.")
                    else:
                        RecoveryPortalEngine.update_restructuring_request(sel_req_id, "APPROVED", admin_rem)
                        
                        # Log audit
                        audit_log(
                            category="Recovery Operations",
                            action="Loan Restructuring Approved",
                            borrower_id=req_row["borrower_id"],
                            new_value="APPROVED",
                            reason=f"Restructuring approved. Remarks: {admin_rem}"
                        )
                        
                        # Trigger dispatch confirmations
                        from communication_engine import send_otp_email, send_otp_sms
                        borrowers_list = pd.read_csv("borrowers.csv")
                        b_meta = borrowers_list[borrowers_list["borrower_id"] == req_row["borrower_id"]]
                        if not b_meta.empty:
                            email = str(b_meta.iloc[0]["email"])
                            mobile = str(b_meta.iloc[0]["mobile_number"])
                            from communication_engine import CommunicationService
                            CommunicationService.send_email(email, "Bandhan Bank - Restructuring Proposal Approved", f"Dear Client,\n\nYour credit restructuring request {sel_req_id} has been APPROVED.\nConditions: {admin_rem}\n\nBest regards,\nBandhan Bank Operations")
                            CommunicationService.send_sms(mobile, f"Bandhan Bank: Restructuring request {sel_req_id} APPROVED. Remarks: {admin_rem}")

                        st.success(f"Restructuring request {sel_req_id} approved!")
                        import time
                        time.sleep(0.5)
                        st.rerun()
                        
            with col_dec2:
                if st.button("❌ Reject Proposal", key=f"rej_req_{sel_req_id}", use_container_width=True):
                    if not admin_rem:
                        st.error("Review remarks are required for rejection.")
                    else:
                        RecoveryPortalEngine.update_restructuring_request(sel_req_id, "REJECTED", admin_rem)
                        
                        # Log audit
                        audit_log(
                            category="Recovery Operations",
                            action="Risk Status Changed",
                            borrower_id=req_row["borrower_id"],
                            new_value="REJECTED",
                            reason=f"Restructuring rejected. Remarks: {admin_rem}"
                        )
                        
                        borrowers_list = pd.read_csv("borrowers.csv")
                        b_meta = borrowers_list[borrowers_list["borrower_id"] == req_row["borrower_id"]]
                        if not b_meta.empty:
                            email = str(b_meta.iloc[0]["email"])
                            mobile = str(b_meta.iloc[0]["mobile_number"])
                            from communication_engine import CommunicationService
                            CommunicationService.send_email(email, "Bandhan Bank - Restructuring Proposal Rejected", f"Dear Client,\n\nWe regret to inform you that your restructuring request {sel_req_id} was REJECTED.\nReason: {admin_rem}\n\nBest regards,\nBandhan Bank Operations")
                            CommunicationService.send_sms(mobile, f"Bandhan Bank: Restructuring request {sel_req_id} REJECTED. Remarks: {admin_rem}")
                            
                        st.warning(f"Restructuring request {sel_req_id} rejected.")
                        import time
                        time.sleep(0.5)
                        st.rerun()
                        
            with col_dec3:
                if st.button("ℹ️ Request Additional Info", key=f"info_req_{sel_req_id}", use_container_width=True):
                    if not admin_rem:
                        st.error("Please supply the details of additional information requested.")
                    else:
                        RecoveryPortalEngine.update_restructuring_request(sel_req_id, "INFO_REQUESTED", admin_rem)
                        
                        # Log audit
                        audit_log(
                            category="Recovery Operations",
                            action="Risk Status Changed",
                            borrower_id=req_row["borrower_id"],
                            new_value="INFO_REQUESTED",
                            reason=f"Additional details requested: {admin_rem}"
                        )
                        
                        borrowers_list = pd.read_csv("borrowers.csv")
                        b_meta = borrowers_list[borrowers_list["borrower_id"] == req_row["borrower_id"]]
                        if not b_meta.empty:
                            email = str(b_meta.iloc[0]["email"])
                            mobile = str(b_meta.iloc[0]["mobile_number"])
                            from communication_engine import CommunicationService
                            CommunicationService.send_email(email, "Bandhan Bank - Additional Restructuring Details Required", f"Dear Client,\n\nWe require additional information to process your restructuring request {sel_req_id}.\nDetails requested: {admin_rem}\n\nBest regards,\nBandhan Bank Operations")
                            CommunicationService.send_sms(mobile, f"Bandhan Bank: Restructuring request {sel_req_id} requires details: {admin_rem}")
                            
                        st.info(f"Additional details requested for request {sel_req_id}.")
                        import time
                        time.sleep(0.5)
                        st.rerun()
        else:
            st.success("🎉 All restructuring requests reviewed!")

    st.markdown("<br><hr><br>", unsafe_allow_html=True)

    # Original Deep Drill-down Logic
    st.subheader("Deep AI Drill-Down (Single Borrower)")
    
    borrower_options = filtered["borrower_id"].tolist() if not filtered.empty else portfolio_df["borrower_id"].tolist()
    selected_borrower = st.selectbox("Select borrower for AI Analysis", borrower_options, key="satark_recover_select")
    
    if not selected_borrower:
        return

    borrower_record = detector.analyze_borrower(selected_borrower).as_dict()
    profile_series = borrowers_df[borrowers_df["borrower_id"] == selected_borrower]
    if profile_series.empty:
        return
    borrower_profile = profile_series.iloc[0]
    
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### Borrower Summary: {borrower_record['name']}")
        st.write(f"Scheme: {borrower_record['loan_scheme']} | Region: {borrower_record['region']}")
        st.write(f"Loan Amount: Rs {borrower_profile.loan_amount:,.0f}")
        st.write(f"Final Risk Level: {borrower_record['risk_level']}")
    
    with col2:
        st.metric("Behavioural Risk Score", borrower_record['risk_score'])
        st.metric("Peer Comparison", f"{borrower_record['peer_score']} (Baseline)")
        st.metric("Regional Stress", format(borrower_record['regional_stress_factor'], ".2f"))

    st.markdown("---")
    
    st.markdown("### Local Risk Exposure Network")
    st.caption("This network represents borrower risk propagation patterns used by the AI risk model.")
    render_ego_network(selected_borrower, detector)

    st.markdown("---")
    

    clicked_ai = st.button(
    "Run AI Risk Analysis",
    use_container_width=True,
    key="run_ai_analysis_btn"
    )
   
    st.markdown('</div>', unsafe_allow_html=True)

    if clicked_ai:
        import requests
        with st.spinner("Connecting to RiskNet AI..."):
            try:
                res = requests.get(f"{API_BASE_URL}/analyze/{selected_borrower}")
                res.raise_for_status()
                data = res.json()
                
                band = data.get("risk_band", "LOW")
                prob = data.get("risk_probability", 0.0) * 100
                action = data.get("recovery_action", "Monitor")
                signals = data.get("key_signals", {})
                
                # Log AI recommendation and explainability decision
                audit_log(
                    category="AI & Risk Engine",
                    action="CBHM Risk Score Generated",
                    borrower_id=selected_borrower,
                    new_value=f"Risk Probability: {prob:.1f}%, Risk Band: {band}",
                    reason=f"Health Score: {100-prob:.1f}/100 | Network Exposure: {signals.get('buffer_ratio', 0.0):.2f} | Regional Stress: {signals['regional_stress']:.2f} | Peer Score: {signals['peer_score']:.0f} | Action: {action}",
                    ai_confidence=f"{prob/100:.2f}"
                )
                
                band_colors = {
                    "CRITICAL": "#ef4444",
                    "HIGH": "#f97316",
                    "MODERATE": "#eab308",
                    "LOW": "#22c55e"
                }
                color = band_colors.get(band, "#22c55e")
                
                st.markdown("### RiskNet Analysis")
                st.markdown(
                    f'''
                    <div style="background: rgba(255,255,255,0.6); backdrop-filter: blur(16px); 
                                border: 1px solid rgba(255,255,255,0.9); border-radius: 24px; 
                                padding: 24px; box-shadow: 0 12px 28px rgba(180, 140, 150, 0.1); margin-bottom: 24px;">
                        <h4 style="margin: 0; color: #636366; font-size: 0.95rem; text-transform: uppercase;">Risk Band</h4>
                        <div style="font-size: 2.2rem; font-weight: 800; color: {color}; margin: 8px 0;">{band}</div>
                        <p style="margin: 0; font-size: 1.1rem; color: #1c1c1e;"><b>Probability:</b> {prob:.1f}%</p>
                        <p style="margin: 8px 0 0 0; font-size: 1.05rem; color: #48484a;"><b>Recommended Action:</b> {action}</p>
                    </div>
                    ''', 
                    unsafe_allow_html=True
                )
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Repayment Consistency", f"{signals['repayment_consistency']:.2f}")
                col2.metric("Peer Score", f"{signals['peer_score']:.0f}")
                col3.metric("Regional Stress", f"{signals['regional_stress']:.2f}")

                col4, col5, col6 = st.columns(3)
                col4.metric("EMI Miss Rate", f"{signals['txn_miss_rate']*100:.1f}%")
                col5.metric("Buffer Ratio", f"{signals['buffer_ratio']:.2f}")
                col6.metric("Days Past Due", f"{signals.get('days_past_due', 0)}")
                
                try:
                    narr_res = requests.get(f"{API_BASE_URL}/narrative/{selected_borrower}")
                    narr_res.raise_for_status()
                    narr_data = narr_res.json()
                    narrative_text = narr_data.get("narrative", "")
                    
                    narrative_text = narrative_text.replace("**", "")
                    
                    st.markdown(
                        f"""
                        <div style="
                            background: rgba(255,255,255,0.65);
                            backdrop-filter: blur(16px);
                            -webkit-backdrop-filter: blur(16px);
                            border: 1px solid rgba(255,255,255,0.85);
                            border-radius: 24px;
                            padding: 28px 32px;
                            margin-top: 16px;
                            box-shadow: 0 16px 40px rgba(180,140,150,0.12);
                        ">
                            <div style="
                                display: flex;
                                align-items: center;
                                gap: 12px;
                                margin-bottom: 20px;
                                padding-bottom: 16px;
                                border-bottom: 1px solid rgba(28,28,30,0.08);
                            ">
                                <div style="
                                    width: 40px; height: 40px;
                                    background: linear-gradient(135deg, #ff5f2e, #e0287d);
                                    border-radius: 12px;
                                    display: flex; align-items: center;
                                    justify-content: center;
                                    font-size: 1.2rem;
                                ">🧠</div>
                                <div>
                                    <div style="font-weight:700; font-size:1.1rem; 
                                                color:#1c1c1e;">
                                        AI Risk Narrative
                                    </div>
                                    <div style="font-size:0.82rem; color:#636366;">
                                        Generated by Bandhan RiskNet Intelligence
                                    </div>
                                </div>
                                <div style="
                                    margin-left: auto;
                                    background: rgba(28,28,30,0.06);
                                    border-radius: 999px;
                                    padding: 6px 14px;
                                    font-size: 0.8rem;
                                    font-weight: 600;
                                    color: #48484a;
                                ">Model v1.0</div>
                            </div>
                            <div style="
                                font-size: 1rem;
                                line-height: 1.75;
                                color: #2c2c2e;
                                white-space: pre-wrap;
                            ">{narrative_text}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.error(f"Failed to fetch narrative: {str(e)}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                render_explainability(selected_borrower)

                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 🛠️ Zonal Recovery & Restructuring Gateway")
                st.markdown("Initiate regulatory loan restructure schemes and term updates directly on this account.")
                
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    if st.button("Offer Restructuring Scheme", key=f"rec_restruct_{selected_borrower}", use_container_width=True):
                        audit_log(
                            category="Recovery Operations",
                            action="Loan Restructuring Recommended",
                            borrower_id=selected_borrower,
                            reason="AI restructuring recommended based on client stock depletion and regional GNN stress baseline"
                        )
                        st.success("✅ Restructuring scheme recommendation recorded and logged.")
                        
                with col_g2:
                    if st.button("Approve Restructuring Scheme", key=f"app_restruct_{selected_borrower}", type="primary", use_container_width=True):
                        audit_log(
                            category="Recovery Operations",
                            action="Loan Restructuring Approved",
                            borrower_id=selected_borrower,
                            reason="Zonal Manager approved interest terms adjustment and timeline extension"
                        )
                        st.success("✅ Zonal Restructuring proposal approved! Compliance logs updated.")

            except Exception as e:
                st.error(f"Failed to connect to RiskNet backend. Please ensure you are running: `uvicorn main:app --reload --port 8000`. Error: {str(e)}")

def render_contagion_simulator(
    portfolio_df: pd.DataFrame, 
    detector, 
    borrowers_df: pd.DataFrame
) -> None:
    import networkx as nx
    import plotly.graph_objects as go
    import time
    import random
    
    st.markdown(
        """
        <div style="background: rgba(255,255,255,0.5);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.8);
            border-radius: 24px;
            padding: 24px 28px;
            margin-bottom: 24px;">
            <h3 style="margin:0 0 8px 0; color:#1c1c1e;">
                🛡️ Bandhan: Intervention Animation
            </h3>
            <p style="margin:0; color:#48484a;">
                Select a borrower and Apply Intervention. 
                See how targeted action reverses risk contagion 
                and stabilizes the surrounding network in real time.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    G_full = detector.get_networkx_graph()

    # Get a list of actual borrower nodes
    borrower_nodes = [n for n in G_full.nodes() if str(n).startswith("BORR_")]
    if not borrower_nodes:
        st.warning("No borrowers found in the graph.")
        return
    
    # Borrower selector
    col1, col2 = st.columns([2, 1])
    with col1:
        center_node = st.selectbox(
            "Select Target Account for Intervention",
            borrower_nodes,
            format_func=lambda x: f"{x} — {portfolio_df.loc[portfolio_df['borrower_id']==x, 'name'].values[0] if x in portfolio_df['borrower_id'].values else 'Unknown'}"
        )
    
    if not center_node:
        return

    # Extract the ego graph to build our clustered animation
    G = nx.ego_graph(G_full, center_node, radius=2)
    pos = nx.spring_layout(G, k=0.25, seed=42)

    # Assign artificial high risk to show the intervention effect prominently
    for node in G.nodes():
        G.nodes[node]['risk'] = random.uniform(0.75, 1.0)
            
    st.markdown("---")
    
    # Placeholders for dynamic rendering
    metric_placeholder = st.empty()
    graph_placeholder = st.empty()

    def get_node_color(risk_score):
        if risk_score >= 0.65: return "#e0287d"  # High Risk (Pink/Red)
        elif risk_score >= 0.35: return "#FF9933" # Moderate Risk (Orange/Yellow)
        else: return "#138808" # Low Risk (Green)

    def create_network_fig(graph, positions):
        edge_x, edge_y = [], []
        for edge in graph.edges():
            x0, y0 = positions[edge[0]]
            x1, y1 = positions[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='rgba(150, 150, 150, 0.3)'),
            hoverinfo='none', mode='lines'
        )

        node_x, node_y, node_colors, node_texts, node_sizes = [], [], [], [], []
        for node in graph.nodes():
            node_x.append(positions[node][0])
            node_y.append(positions[node][1])
            risk = graph.nodes[node].get('risk', 0.0)
            node_colors.append(get_node_color(risk))
            
            is_center = (node == center_node)
            node_sizes.append(36 if is_center else 24)
            prefix = "<b>🎯 TARGET (You)</b><br>" if is_center else ""
            
            # Format text cleanly based on node type
            node_name = str(node).replace("SCHEME::", "Scheme: ").replace("REGION::", "Region: ").replace("CATEGORY::", "Category: ")
            node_texts.append(f"{prefix}{node_name}<br>Risk: {risk:.2f}")

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers', hoverinfo='text',
            text=node_texts,
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(color="white", width=2.5)
            )
        )

        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            showlegend=False, hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=0),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            uirevision="constant", height=500
        )
        return fig

    # Initial Rendering
    initial_total_risk = sum(nx.get_node_attributes(G, 'risk').values())
    metric_placeholder.metric("Cluster Systemic Risk", f"{initial_total_risk:.2f}")
    graph_placeholder.plotly_chart(create_network_fig(G, pos), use_container_width=True, theme=None)

    st.markdown("<br>", unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1,2,1])
    with btn_col:
        clicked_intervention = st.button("Apply Intervention", type="primary", use_container_width=True)

    if clicked_intervention:
        hop_distances = nx.single_source_shortest_path_length(G, center_node)
        max_hops = max(hop_distances.values()) if hop_distances else 0
        
        frames_per_hop = 4
        healing_rate = 0.12
        total_frames = (max_hops + 2) * frames_per_hop
        
        for frame in range(total_frames):
            current_wave_radius = frame / frames_per_hop
            for node in G.nodes():
                distance = hop_distances.get(node, float('inf'))
                if distance <= current_wave_radius:
                    current_risk = G.nodes[node]['risk']
                    new_risk = max(0.1, current_risk - healing_rate)
                    G.nodes[node]['risk'] = new_risk

            current_total_risk = sum(nx.get_node_attributes(G, 'risk').values())
            delta_val = current_total_risk - initial_total_risk
            
            metric_placeholder.metric(
                "Cluster Systemic Risk", 
                f"{current_total_risk:.2f}", 
                f"{delta_val:.2f} Risk Eradicated",
                delta_color="inverse"
            )
            graph_placeholder.plotly_chart(create_network_fig(G, pos), use_container_width=True, theme=None)
            time.sleep(0.08)
            
        st.toast("Intervention successfully localized threat!", icon="✅")
        st.balloons()


def render_regional_heatmap(
    regional_df: pd.DataFrame,
    portfolio_df: pd.DataFrame
) -> None:

    st.markdown(
        """
        <div style="background: rgba(255,255,255,0.5);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.8);
            border-radius: 24px;
            padding: 24px 28px;
            margin-bottom: 24px;">
            <h3 style="margin:0 0 8px 0; color:#1c1c1e;">
                Regional Credit Stress Heatmap
            </h3>
            <p style="margin:0; color:#48484a;">
                NPA rate and economic stress index 
                across monitored regions. Darker = 
                higher stress.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Map toggle
    map_metric = st.radio(
        "Colour map by",
        ["NPA Rate", "Regional Stress Factor", 
         "Economic Stress Index"],
        horizontal=True,
        key="heatmap_metric"
    )

    metric_col = {
        "NPA Rate": "npa_rate",
        "Regional Stress Factor": "regional_stress_factor",
        "Economic Stress Index": "economic_stress_index"
    }[map_metric]

    # Merge portfolio counts into regional
    region_counts = portfolio_df.groupby(
        "region", as_index=False
    ).agg(
        borrower_count=("borrower_id", "count"),
        avg_risk=("risk_score", "mean"),
        high_risk_count=(
            "risk_score", 
            lambda x: (x >= 70).sum()
        )
    )
    
    map_df = regional_df.merge(
        region_counts, on="region", how="left"
    ).fillna(0)

    # Indian state name mapping
    # Our region names → Plotly India GeoJSON state names
    state_map = {
        "Jharkhand":   "Jharkhand",
        "West Bengal": "West Bengal",
        "Bihar":       "Bihar",
        "Odisha":      "Odisha",
        "Maharashtra": "Maharashtra",
        "Uttar Pradesh": "Uttar Pradesh",
        "Rajasthan":   "Rajasthan",
        "Madhya Pradesh": "Madhya Pradesh",
        "Gujarat":     "Gujarat",
        "Tamil Nadu":  "Tamil Nadu",
        "Karnataka":   "Karnataka",
        "Andhra Pradesh": "Andhra Pradesh",
        "Telangana":   "Telangana",
        "Kerala":      "Kerala",
        "Punjab":      "Punjab",
        "Haryana":     "Haryana",
        "Delhi":       "NCT of Delhi",
        "Assam":       "Assam",
        "Chhattisgarh": "Chhattisgarh",
        "Uttarakhand": "Uttarakhand",
        "Himachal Pradesh": "Himachal Pradesh",
        "Jammu and Kashmir": "Jammu & Kashmir",
        "Goa":         "Goa",
        "Tripura":     "Tripura",
        "Meghalaya":   "Meghalaya",
        "Manipur":     "Manipur",
        "Nagaland":    "Nagaland",
        "Sikkim":      "Sikkim"
    }
    
    map_df["state_name"] = map_df["region"].map(
        state_map
    ).fillna(map_df["region"])

    # Build choropleth using plotly
    import requests as req
    
    # Fetch India GeoJSON
    geojson_url = (
        "https://raw.githubusercontent.com/"
        "Subhash9325/GeoJson-Data-of-Indian-States/"
        "master/Indian_States"
    )
    
    try:
        geojson_resp = req.get(geojson_url, timeout=5)
        india_geojson = geojson_resp.json()
        
        fig = px.choropleth(
            map_df,
            geojson=india_geojson,
            locations="state_name",
            featureidkey="properties.NAME_1",
            color=metric_col,
            hover_name="region",
            hover_data={
                "npa_rate": ":.1f",
                "regional_stress_factor": ":.2f",
                "borrower_count": True,
                "avg_risk": ":.1f",
                "high_risk_count": True,
                "state_name": False,
            },
            color_continuous_scale=[
                [0.0, "#d4edda"],
                [0.3, "#ffeaa7"],
                [0.6, "#f97316"],
                [1.0, "#ef4444"],
            ],
            labels={
                "npa_rate": "NPA Rate (%)",
                "regional_stress_factor": "Stress Factor",
                "economic_stress_index": "Stress Index",
                "borrower_count": "Borrowers",
                "avg_risk": "Avg Risk Score",
                "high_risk_count": "High Risk Count",
            },
            title=f"India — {map_metric} by Region"
        )
        
        fig.update_geos(
            fitbounds="locations",
            visible=False,
            bgcolor="rgba(0,0,0,0)"
        )
        
        fig.update_layout(
            height=520,
            margin=dict(l=0, r=0, t=48, b=0),
            paper_bgcolor="rgba(255,255,255,0.18)",
            font=dict(color="#1c1c1e"),
            coloraxis_colorbar=dict(
                title=map_metric,
                thickness=14,
                len=0.6,
                bgcolor="rgba(255,255,255,0.6)",
                bordercolor="rgba(255,255,255,0.8)",
                borderwidth=1,
            ),
            geo=dict(
                bgcolor="rgba(0,0,0,0)"
            )
        )
        
        st.plotly_chart(
            fig, use_container_width=True, theme=None
        )
        
    except Exception:
        # Fallback — bar chart if GeoJSON fails
        st.info(
            "Map requires internet connection. "
            "Showing bar chart instead."
        )
        bar_fig = px.bar(
            map_df.sort_values(metric_col, ascending=False),
            x="region",
            y=metric_col,
            color=metric_col,
            color_continuous_scale=[
                [0.0, "#d4edda"],
                [0.5, "#f97316"],
                [1.0, "#ef4444"],
            ],
            text=metric_col,
            title=f"{map_metric} by Region"
        )
        bar_fig.update_traces(texttemplate="%{text:.2f}")
        bar_fig.update_layout(
            paper_bgcolor="rgba(255,255,255,0.18)",
            plot_bgcolor="rgba(255,255,255,0.10)",
            font=dict(color="#1c1c1e"),
            margin=dict(l=16, r=16, t=48, b=48),
            showlegend=False
        )
        st.plotly_chart(
            bar_fig, use_container_width=True, theme=None
        )

    cols = st.columns(len(map_df))
    # Regional stats cards below map
    st.markdown("### Regional Risk Breakdown")
    
    sorted_regions = map_df.sort_values(
        "npa_rate", ascending=False
    ).reset_index(drop=True)

    # Render in rows of 4 cards each
    cards_per_row = 4
    for row_start in range(
        0, len(sorted_regions), cards_per_row
    ):
        row_data = sorted_regions.iloc[
            row_start:row_start + cards_per_row
        ]
        cols = st.columns(cards_per_row)
        for i, (_, row) in enumerate(
            row_data.iterrows()
        ):
            stress = float(
                row["regional_stress_factor"]
            )
            if stress >= 0.7:
                color = "#ef4444"
                label = "High Stress"
                bg    = "rgba(239,68,68,0.06)"
            elif stress >= 0.5:
                color = "#f97316"
                label = "Moderate"
                bg    = "rgba(249,115,22,0.06)"
            else:
                color = "#22c55e"
                label = "Stable"
                bg    = "rgba(34,197,94,0.06)"

            cols[i].markdown(
                f"""
                <div style="
                    background: rgba(255,255,255,0.7);
                    border-radius: 20px;
                    padding: 20px 16px;
                    border-left: 4px solid {color};
                    border: 1px solid 
                        rgba(255,255,255,0.85);
                    border-left: 4px solid {color};
                    margin-bottom: 12px;
                    box-shadow: 0 8px 24px 
                        rgba(180,140,150,0.08);
                ">
                    <div style="
                        font-weight: 700;
                        font-size: 0.95rem;
                        color: #1c1c1e;
                        margin-bottom: 10px;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    ">{row['region']}</div>
                    <div style="
                        font-size: 1.8rem;
                        font-weight: 800;
                        color: {color};
                        line-height: 1;
                        margin-bottom: 4px;
                    ">{row['npa_rate']:.1f}%</div>
                    <div style="
                        font-size: 0.78rem;
                        color: #636366;
                        margin-bottom: 8px;
                    ">NPA Rate</div>
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        padding-top: 8px;
                        border-top: 1px solid 
                            rgba(28,28,30,0.06);
                    ">
                        <span style="
                            font-size: 0.78rem;
                            font-weight: 600;
                            color: {color};
                            background: {bg};
                            padding: 3px 8px;
                            border-radius: 999px;
                        ">{label}</span>
                        <span style="
                            font-size: 0.78rem;
                            color: #636366;
                        ">
                            {int(row.get(
                                'borrower_count', 0
                            ))} borrowers
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown(
            "<div style='margin-bottom:4px'></div>",
            unsafe_allow_html=True
        )

def render_field_visit_planner(portfolio_df: pd.DataFrame, detector) -> None:
    st.markdown(
        """
        <div style="background: rgba(255,255,255,0.5);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.8);
            border-radius: 24px;
            padding: 24px 28px;
            margin-bottom: 24px;">
            <h3 style="margin:0 0 8px 0; color:#1c1c1e;">
                🗺️ Field Visit Planner
            </h3>
            <p style="margin:0; color:#48484a;">
                Optimize your physical branch visits. Actionable routes dynamically generated from AI risk insights and geographic clustering.
            </p>
        </div>
        """, unsafe_allow_html=True
    )
    
    col_filters, col_main = st.columns([1, 2.5])
    
    with col_filters:
        st.markdown("#### Route Settings")
        min_risk = st.slider("Minimum Risk Level", 0, 100, 45, key="visit_min_risk")
        
        regions = ["All"] + sorted(portfolio_df["region"].dropna().unique().tolist())
        region_filter = st.selectbox("Select Region", regions, key="visit_region")
        
        schemes = ["All"] + sorted(portfolio_df["loan_scheme"].dropna().unique().tolist())
        scheme_filter = st.selectbox("Loan Scheme", schemes, key="visit_scheme")
        
        max_route_size = st.number_input("Max Borrowers per Route", min_value=2, max_value=10, value=3)
        sort_by = st.selectbox("Prioritize By", ["Total Risk", "Exposed Value", "Cluster Density"])
        
    with col_main:
        # 1. Filter borrowers
        target_df = portfolio_df[portfolio_df["risk_score"] >= min_risk].copy()
        if region_filter != "All":
            target_df = target_df[target_df["region"] == region_filter]
        if scheme_filter != "All":
            target_df = target_df[target_df["loan_scheme"] == scheme_filter]
            
        if target_df.empty:
            st.info("No borrowers match the current filter criteria.")
            return
            
        # 2. Grouping Logic: Geographic proximity (Region) + Risk Clusters
        routes = []
        for region, group in target_df.groupby("region"):
            # Sort by risk within region to group highest risk together
            group = group.sort_values("risk_score", ascending=False)
            
            # Chunk into routes
            for i in range(0, len(group), max_route_size):
                route_chunk = group.iloc[i : i + max_route_size]
                if len(route_chunk) > 0:
                    total_risk = route_chunk["risk_score"].sum()
                    avg_risk = route_chunk["risk_score"].mean()
                    total_exposure = route_chunk.get("outstanding_amount", pd.Series([0]*len(route_chunk))).sum()
                    
                    routes.append({
                        "route_name": f"Route {len(routes) + 1} — {region} Cluster",
                        "borrowers": route_chunk.to_dict("records"),
                        "total_risk": total_risk,
                        "avg_risk": avg_risk,
                        "total_exposure": total_exposure,
                        "density": len(route_chunk),
                        "region_name": region
                    })
                    
        # 3. Sorting
        if sort_by == "Total Risk":
            routes.sort(key=lambda x: x["total_risk"], reverse=True)
        elif sort_by == "Exposed Value":
             routes.sort(key=lambda x: x["total_exposure"], reverse=True)
        else:
             routes.sort(key=lambda x: x["density"], reverse=True)
             
        st.markdown(f"#### Generated Routes ({len(routes)} available)")
        
        # 4. Display Logic
        for r in routes[:10]: # Paginate/limit to top 10 for UI
            expanded = (r == routes[0]) # Auto-expand only the first one
            with st.expander(f"📍 {r['route_name']} (Total Risk: {r['total_risk']:.1f})", expanded=expanded):
                
                # Intelligence Layer Explanation
                explanation = f"AI Prioritization Reason: *This route efficiently targets {r['density']} high-risk borrowers clustered in geographic proximity within {r['region_name']}. The combined exposure is ₹{r['total_exposure']/1e5:.2f} Lakhs.*"
                st.markdown(f"<div style='background:rgba(23,66,41,0.05); padding:12px; border-radius:12px; margin-bottom:12px; border-left:4px solid #174229;'>{explanation}</div>", unsafe_allow_html=True)
                
                for b in r["borrowers"]:
                    if b["risk_score"] >= 70:
                        badge = "<span style='background:#fef2f2; color:#b91c1c; padding:2px 8px; border-radius:12px; border:1px solid #fecaca;'>🔴 CRITICAL</span>"
                    elif b["risk_score"] >= 50:
                        badge = "<span style='background:#fffbeb; color:#b45309; padding:2px 8px; border-radius:12px; border:1px solid #fde68a;'>🟠 HIGH</span>"
                    else:
                        badge = "<span style='background:#f0fdf4; color:#15803d; padding:2px 8px; border-radius:12px; border:1px solid #bbf7d0;'>🟡 MODERATE</span>"
                        
                    st.markdown(
                        f"""
                        <div style="padding: 12px; border-bottom: 1px solid rgba(0,0,0,0.1); display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <div>
                                <b>{b['name']}</b> ({b['borrower_id']})<br>
                                <span style="font-size: 0.85em; color: #666;">{b['loan_scheme']} · Score: {b['risk_score']} · Exposure: ₹{b.get('outstanding_amount', 0)/1e5:.1f} L</span>
                            </div>
                            <div style="font-weight: 600; font-size: 0.85em; padding-top: 4px;">
                                {badge}
                            </div>
                        </div>
                        """, unsafe_allow_html=True
                    )
                    
                    col_act1, col_act2 = st.columns(2)
                    with col_act1:
                        if st.button(f"🗓️ Schedule Visit ({b['borrower_id']})", key=f"sched_{r['route_name']}_{b['borrower_id']}", use_container_width=True):
                            audit_log(
                                category="Recovery Operations",
                                action="Branch Visit Scheduled",
                                borrower_id=b["borrower_id"],
                                reason=f"Branch recovery visit scheduled via route path: {r['route_name']}"
                            )
                            st.success(f"✅ Visit scheduled and logged for {b['name']}.")
                    with col_act2:
                        if st.button(f"✅ Mark Completed ({b['borrower_id']})", key=f"comp_{r['route_name']}_{b['borrower_id']}", use_container_width=True):
                            audit_log(
                                category="Recovery Operations",
                                action="Field Visit Completed",
                                borrower_id=b["borrower_id"],
                                reason=f"Direct agent visit completed at borrower premises"
                            )
                            st.success(f"✅ Field visit completion logged for {b['name']}.")
                    st.markdown("<div style='margin-bottom: 16px; border-bottom: 1px dashed rgba(0,0,0,0.06);'></div>", unsafe_allow_html=True)


def render_borrower_communication_center(portfolio_df: pd.DataFrame, transactions_df: pd.DataFrame) -> None:
    st.markdown(
        """
        <div style="background: rgba(255,255,255,0.5);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.8);
            border-radius: 24px;
            padding: 24px 28px;
            margin-bottom: 24px;">
            <h3 style="margin:0 0 8px 0; color:#1c1c1e;">
                📨 Borrower Communication Center
            </h3>
            <p style="margin:0; color:#48484a;">
                Manage direct warning alerts, payment notifications, restructuring offers, and recovery updates to bank borrowers.
            </p>
        </div>
        """, unsafe_allow_html=True
    )

    # Check configurations and display simulation mode banner
    email_ok = CommunicationService.is_email_configured()
    sms_ok = CommunicationService.is_sms_configured()
    if not email_ok or not sms_ok:
        missing = []
        if not email_ok: missing.append("Email (SMTP)")
        if not sms_ok: missing.append("SMS (Twilio/Fast2SMS)")
        st.info(
            f"ℹ️ **Simulation Mode Active**: Credentials not found for: {', '.join(missing)}. "
            "Sent messages will be generated, displayed, and logged locally but not transmitted. "
            "To enable live sending, configure credentials in your `.env` file."
        )

    # 1. Compute dynamic properties (Last EMI Date, Risk Band, Communication Status)
    # Get last successful EMI dates
    emi_txns = transactions_df[(transactions_df["transaction_type"] == "EMI_PAYMENT") & (transactions_df["amount"] > 0)]
    last_emi_dates = {}
    if not emi_txns.empty:
        last_emi_dates = emi_txns.groupby("borrower_id")["timestamp"].max().dt.strftime("%Y-%m-%d").to_dict()

    logs_df = get_communication_logs()
    contacted_ids = set()
    if not logs_df.empty:
        contacted_ids = set(logs_df["borrower_id"].dropna().unique())

    enriched_df = portfolio_df.copy()
    enriched_df["Last EMI Date"] = enriched_df["borrower_id"].map(last_emi_dates).fillna("No payment recorded")
    
    def get_risk_band(score):
        if score >= 70: return "Critical"
        elif score >= 50: return "High"
        elif score >= 35: return "Moderate"
        else: return "Low"
    enriched_df["Current Risk Band"] = enriched_df["risk_score"].apply(get_risk_band)
    
    enriched_df["Communication Status"] = enriched_df["borrower_id"].apply(
        lambda x: "Contacted" if x in contacted_ids else "Not Contacted"
    )

    # 2. Filters
    with st.expander("🔍 Search & Filter Borrowers", expanded=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            search_name = st.text_input("Search Name or ID", "", key="comm_search_name")
            risk_filter = st.selectbox("Risk Level", ["All", "Critical", "High", "Moderate", "Low"], key="comm_risk_filter")
        with f_col2:
            branch_filter = st.selectbox("Branch", ["All"] + sorted(enriched_df["branch"].dropna().unique().tolist()), key="comm_branch_filter")
            region_filter = st.selectbox("Region", ["All"] + sorted(enriched_df["region"].dropna().unique().tolist()), key="comm_region_filter")
        with f_col3:
            scheme_filter = st.selectbox("Loan Scheme", ["All"] + sorted(enriched_df["loan_scheme"].dropna().unique().tolist()), key="comm_scheme_filter")
            missed_filter = st.selectbox("Missed Payments (90d)", ["All", "None", "1 or more", "2 or more", "3 or more"], key="comm_missed_filter")
            
        f_col4, f_col5 = st.columns([1, 2])
        with f_col4:
            comm_filter = st.selectbox("Communication Status", ["All", "Contacted", "Not Contacted"], key="comm_status_filter")

    # Apply filters
    filtered_df = enriched_df.copy()
    if search_name:
        filtered_df = filtered_df[
            filtered_df["name"].str.contains(search_name, case=False, na=False) |
            filtered_df["borrower_id"].str.contains(search_name, case=False, na=False)
        ]
    if risk_filter != "All":
        filtered_df = filtered_df[filtered_df["Current Risk Band"] == risk_filter]
    if branch_filter != "All":
        filtered_df = filtered_df[filtered_df["branch"] == branch_filter]
    if region_filter != "All":
        filtered_df = filtered_df[filtered_df["region"] == region_filter]
    if scheme_filter != "All":
        filtered_df = filtered_df[filtered_df["loan_scheme"] == scheme_filter]
    if comm_filter != "All":
        filtered_df = filtered_df[filtered_df["Communication Status"] == comm_filter]
    if missed_filter != "All":
        if missed_filter == "None":
            filtered_df = filtered_df[filtered_df["missed_payments_90d"] == 0]
        elif missed_filter == "1 or more":
            filtered_df = filtered_df[filtered_df["missed_payments_90d"] >= 1]
        elif missed_filter == "2 or more":
            filtered_df = filtered_df[filtered_df["missed_payments_90d"] >= 2]
        elif missed_filter == "3 or more":
            filtered_df = filtered_df[filtered_df["missed_payments_90d"] >= 3]

    # Display borrower list table
    display_cols = {
        "borrower_id": "Borrower ID",
        "name": "Name",
        "email": "Email",
        "mobile_number": "Mobile Number",
        "loan_scheme": "Loan Scheme",
        "branch": "Branch",
        "region": "Region",
        "Current Risk Band": "Current Risk Band",
        "outstanding_amount": "Outstanding Amount",
        "Last EMI Date": "Last EMI Date",
        "days_past_due": "Days Past Due",
        "Communication Status": "Comm Status"
    }
    
    table_df = filtered_df[list(display_cols.keys())].rename(columns=display_cols)
    table_df["Outstanding Amount"] = table_df["Outstanding Amount"].apply(lambda x: f"₹{x:,.2f}")
    
    st.markdown(f"**Borrowers List ({len(table_df)} matching)**")
    render_glass_table(table_df, max_height=300)

    # 3. Communication setup panel
    st.markdown("<br>", unsafe_allow_html=True)
    panel_col1, panel_col2 = st.columns([1, 1.2])

    with panel_col1:
        st.markdown("#### ✉️ Recipient Selection")
        selection_mode = st.radio(
            "Selection Mode",
            ["Single Recipient", "Multiple Recipients", "Entire Filtered Group"],
            key="comm_mode_radio"
        )
        
        target_borrowers = []
        if selection_mode == "Single Recipient":
            b_list = filtered_df["borrower_id"].tolist()
            if b_list:
                sel_id = st.selectbox("Select Borrower", b_list, key="comm_single_sel")
                target_borrowers = filtered_df[filtered_df["borrower_id"] == sel_id].to_dict("records")
            else:
                st.info("No matching borrowers to select.")
        elif selection_mode == "Multiple Recipients":
            b_list = filtered_df["borrower_id"].tolist()
            if b_list:
                sel_ids = st.multiselect("Select Borrowers", b_list, key="comm_multi_sel")
                target_borrowers = filtered_df[filtered_df["borrower_id"].isin(sel_ids)].to_dict("records")
            else:
                st.info("No matching borrowers to select.")
        else:
            target_borrowers = filtered_df.to_dict("records")
            st.info(f"Targeting all {len(target_borrowers)} filtered borrowers.")

        st.markdown("#### ⚙️ Message Configuration")
        msg_type = st.selectbox(
            "Message Type",
            ["EMI Reminder", "Early Warning Notice", "Loan Restructuring Offer", "Branch Visit Notification", "Recovery Reminder", "Custom Message"],
            key="comm_msg_type_sel"
        )
        
        channel = st.selectbox(
            "Channel",
            ["Email", "SMS", "Both"],
            key="comm_channel_sel"
        )

    with panel_col2:
        st.markdown("#### 📝 Message Preview & Edit")
        
        # Generation Logic
        if not target_borrowers:
            st.warning("Please select recipients to preview the draft message.")
            draft_body = ""
            custom_body = ""
        else:
            # Preview first borrower
            preview_b = target_borrowers[0]
            
            custom_body = ""
            if msg_type == "Custom Message":
                custom_body = st.text_area(
                    "Enter Custom Message Body:",
                    "This is an update from Bandhan Bank regarding your outstanding loan.",
                    key="custom_body_text_area"
                )

            # Generate smart draft message using local reasoning engine
            draft_body = InHouseAIReasoningEngine.generate_message(
                name=preview_b["name"],
                loan_scheme=preview_b["loan_scheme"],
                outstanding_amount=preview_b["outstanding_amount"],
                health_score=preview_b["health_score"],
                risk_level=preview_b["Current Risk Band"],
                days_past_due=preview_b["days_past_due"],
                last_emi_date=preview_b["Last EMI Date"],
                branch=preview_b["branch"],
                message_type=msg_type,
                custom_body=custom_body
            )

        edited_draft = st.text_area(
            "Draft Message Preview (Editable):",
            draft_body,
            height=260,
            key="comm_edited_draft"
        )

        if len(target_borrowers) > 1:
            st.caption(
                f"ℹ️ **Bulk Template Active**: You are sending to {len(target_borrowers)} borrowers. "
                "The message text above represents the draft layout. Each borrower will receive "
                "a personalized message populated with their own details."
            )

        if target_borrowers:
            # Send Action
            if st.button("🚀 Send Communication", type="primary", use_container_width=True, key="comm_send_btn"):
                st.session_state.confirm_send_active = True

            if st.session_state.get("confirm_send_active"):
                st.markdown(
                    f"""
                    <div style="background: rgba(239, 68, 68, 0.08); border-left: 4px solid #ef4444; padding: 12px; border-radius: 8px; margin-top: 12px; margin-bottom: 12px;">
                        <h5 style="color:#ef4444; margin:0 0 6px 0; font-weight:bold;">⚠️ Confirm Transmission</h5>
                        <p style="color:#3a3a3c; margin:0; font-size:0.92rem;">
                            Transmit <b>{msg_type}</b> via <b>{channel}</b> to <b>{len(target_borrowers)} borrower(s)</b>? 
                            This action will be logged.
                        </p>
                    </div>
                    """, unsafe_allow_html=True
                )
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("✅ Confirm Send", key="comm_confirm_btn", use_container_width=True):
                        admin_name = st.session_state.get("admin_username", "Admin").title()
                        
                        sent_count = 0
                        simulated_count = 0
                        failed_count = 0
                        errors = []

                        with st.spinner(f"Transmitting messages to {len(target_borrowers)} recipients..."):
                            for b in target_borrowers:
                                # Re-generate text with correct recipient values
                                final_text = InHouseAIReasoningEngine.generate_message(
                                    name=b["name"],
                                    loan_scheme=b["loan_scheme"],
                                    outstanding_amount=b["outstanding_amount"],
                                    health_score=b["health_score"],
                                    risk_level=b["Current Risk Band"],
                                    days_past_due=b["days_past_due"],
                                    last_emi_date=b["Last EMI Date"],
                                    branch=b["branch"],
                                    message_type=msg_type,
                                    custom_body=custom_body if msg_type == "Custom Message" else ""
                                )

                                # Overwrite preview edits on the first recipient if selected recipient is single
                                if len(target_borrowers) == 1:
                                    final_text = edited_draft

                                email_res = {"status": "Skipped"}
                                sms_res = {"status": "Skipped"}

                                if channel in ["Email", "Both"]:
                                    email_res = CommunicationService.send_email(
                                        b["email"],
                                        f"Bandhan Bank Notification - {msg_type}",
                                        final_text
                                    )
                                if channel in ["SMS", "Both"]:
                                    sms_res = CommunicationService.send_sms(
                                        b["mobile_number"],
                                        final_text
                                    )

                                # Evaluate statuses
                                statuses = []
                                if channel in ["Email", "Both"]:
                                    statuses.append(f"Email:{email_res['status']}")
                                if channel in ["SMS", "Both"]:
                                    statuses.append(f"SMS:{sms_res['status']}")
                                
                                overall = " & ".join(statuses)

                                if "Failed" in overall:
                                    failed_count += 1
                                    if email_res.get("status") == "Failed":
                                        errors.append(f"{b['borrower_id']}: {email_res['message']}")
                                    if sms_res.get("status") == "Failed":
                                        errors.append(f"{b['borrower_id']}: {sms_res['message']}")
                                elif "Simulated" in overall:
                                    simulated_count += 1
                                else:
                                    sent_count += 1

                                # Save log
                                log_communication(
                                    admin_name=admin_name,
                                    borrower_id=b["borrower_id"],
                                    borrower_name=b["name"],
                                    channel=channel,
                                    message_type=msg_type,
                                    message_content=final_text,
                                    delivery_status=overall
                                )

                                # Log compliance audit trail events
                                if channel in ["Email", "Both"]:
                                    audit_log(
                                        category="Recovery Operations",
                                        action="Warning Email Sent" if msg_type == "Early Warning Notice" else "Recovery Email Sent",
                                        borrower_id=b["borrower_id"],
                                        new_value=email_res["status"],
                                        reason=f"Type: {msg_type} | Content: {final_text[:80]}..."
                                    )
                                if channel in ["SMS", "Both"]:
                                    audit_log(
                                        category="Recovery Operations",
                                        action="SMS Reminder Sent",
                                        borrower_id=b["borrower_id"],
                                        new_value=sms_res["status"],
                                        reason=f"Type: {msg_type} | Content: {final_text[:80]}..."
                                    )

                        if sent_count > 0:
                            st.success(f"✅ Successfully sent {sent_count} messages.")
                        if simulated_count > 0:
                            st.info(f"ℹ️ Simulated sending for {simulated_count} messages. Logs saved.")
                        if failed_count > 0:
                            st.error(f"❌ Failed to send {failed_count} messages. Details:\n" + "\n".join(errors))

                        st.session_state.confirm_send_active = False
                        st.rerun()

                with c_btn2:
                    if st.button("❌ Cancel", key="comm_cancel_btn", use_container_width=True):
                        st.session_state.confirm_send_active = False
                        st.rerun()

    # 4. History Logs Table
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    st.subheader("📋 Communication History Logs")
    
    logs_data = get_communication_logs()
    if logs_data.empty:
        st.info("No communication history recorded yet.")
    else:
        logs_display = logs_data[[
            "timestamp", "admin_name", "borrower_id", "borrower_name",
            "channel", "message_type", "delivery_status", "read_status"
        ]].rename(columns={
            "timestamp": "Date & Time",
            "admin_name": "Admin Name",
            "borrower_id": "Borrower ID",
            "borrower_name": "Borrower Name",
            "channel": "Channel",
            "message_type": "Message Type",
            "delivery_status": "Delivery Status",
            "read_status": "Read Status"
        })
        render_glass_table(logs_display, max_height=350)


def render_rm_copilot_tab(portfolio_df: pd.DataFrame, detector) -> None:
    admin_name = st.session_state.get("admin_username", "Officer").title()
    render_safe_html(
        f"""
        <div style="background: rgba(255,255,255,0.5); backdrop-filter: blur(16px); 
                    border: 1px solid rgba(255,255,255,0.8); border-radius: 24px; padding: 24px 28px; margin-bottom: 24px;">
            <h3 style="margin:0 0 4px 0; color:#1c1c1e;">Good Morning, {admin_name} 💼</h3>
            <p style="margin:0; color:#636366; font-size:0.95rem;">Your intelligent recovery workspace is active. Below is your portfolio action plan for today.</p>
        </div>
        """
    )
    
    stats = RMCopilotEngine.get_copilot_stats(portfolio_df, detector)
    priorities = RMCopilotEngine.get_ranked_priorities(portfolio_df, detector)
    briefing = RMCopilotEngine.get_daily_briefing(portfolio_df, detector)
    insights = RMCopilotEngine.get_smart_insights(portfolio_df, detector)
    workload = RMCopilotEngine.get_workload_optimization(priorities)
    opportunities = RMCopilotEngine.get_portfolio_opportunities(portfolio_df, detector)
    learning = RMCopilotEngine.get_learning_system_stats()
    
    st.markdown("#### Today's Portfolio Summary")
    sum_col1, sum_col2, sum_col3, sum_col4, sum_col5, sum_col6 = st.columns(6)
    
    def render_copilot_metric_card(label: str, value: str, theme: str) -> str:
        colors = {
            "red": ("rgba(239, 68, 68, 0.07)", "#b91c1c", "border: 1px solid rgba(239, 68, 68, 0.15)"),
            "orange": ("rgba(245, 158, 11, 0.07)", "#b45309", "border: 1px solid rgba(245, 158, 11, 0.15)"),
            "green": ("rgba(34, 197, 94, 0.07)", "#15803d", "border: 1px solid rgba(34, 197, 94, 0.15)"),
            "blue": ("rgba(59, 130, 246, 0.07)", "#1d4ed8", "border: 1px solid rgba(59, 130, 246, 0.15)"),
            "purple": ("rgba(139, 92, 246, 0.07)", "#6d28d9", "border: 1px solid rgba(139, 92, 246, 0.15)")
        }
        bg, txt, border = colors.get(theme, ("rgba(255,255,255,0.4)", "#1c1c1e", "border: 1px solid rgba(0,0,0,0.06)"))
        return f"""
        <div style="background:{bg}; {border}; border-radius:16px; padding:16px; text-align:center; min-height:100px; display:flex; flex-direction:column; justify-content:center; box-shadow:0 8px 16px rgba(0,0,0,0.015);">
            <span style="font-size:0.68rem; color:#636366; text-transform:uppercase; font-weight:700; letter-spacing:0.5px; margin-bottom:6px;">{label}</span>
            <span style="font-size:1.35rem; font-weight:800; color:{txt};">{value}</span>
        </div>
        """
        
    with sum_col1:
        render_safe_html(render_copilot_metric_card("Managed Borrowers", f"{stats['total_borrowers']}", "blue"))
    with sum_col2:
        render_safe_html(render_copilot_metric_card("High Priority", f"{stats['high_priority_count']}", "orange"))
    with sum_col3:
        render_safe_html(render_copilot_metric_card("Critical Accounts", f"{stats['critical_count']}", "red"))
    with sum_col4:
        render_safe_html(render_copilot_metric_card("At-Risk Portfolio", f"₹{stats['portfolio_at_risk']/1e5:.1f} L", "red"))
    with sum_col5:
        render_safe_html(render_copilot_metric_card("Recovery Target", f"₹{stats['recovery_opportunity']/1e5:.1f} L", "green"))
    with sum_col6:
        render_safe_html(render_copilot_metric_card("New AI Alerts", f"{stats['new_alerts_count']}", "purple"))
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    render_safe_html(
        f"""
        <div style="background: rgba(29, 78, 216, 0.05); border: 1px solid rgba(29, 78, 216, 0.15); border-left: 5px solid #1d4ed8; border-radius: 12px; padding: 18px 22px; margin-bottom: 24px;">
            <span style="font-size:0.75rem; text-transform:uppercase; color:#1d4ed8; font-weight:700; letter-spacing:1px; display:block; margin-bottom:6px;">🧠 Daily AI Briefing</span>
            <p style="margin:0; font-size:0.95rem; color:#1e293b; line-height:1.5;">{briefing}</p>
        </div>
        """
    )
    
    left_col, right_col = st.columns([1.5, 1])
    
    with left_col:
        st.markdown("### ⚡ Today's Priorities")
        st.markdown("Proactively ranked action items based on risk score, behavior dynamics, and network correlation.")
        
        if not priorities:
            st.success("🎉 Outstanding news! No prioritized warning alerts or critical accounts require action today.")
        else:
            for p in priorities:
                badge_color = "#ef4444" if p["workload_type"] == "Escalation" else "#f59e0b" if p["workload_type"] == "Physical Visit" else "#3b82f6"
                reasons_html = "".join(f"<div style='font-size:0.88rem; color:#1e293b; margin-bottom:4px;'>• {r}</div>" for r in p["reasons"])
                
                card_html = f"""
                <div style="background:rgba(255,255,255,0.7); border:1px solid rgba(0,0,0,0.06); border-radius:20px; padding:24px; margin-bottom:20px; box-shadow:0 12px 28px rgba(0,0,0,0.015);">
                    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(0,0,0,0.06); padding-bottom:12px; margin-bottom:16px;">
                        <div>
                            <span style="font-weight:700; color:#ff5f2e; font-size:0.85rem; text-transform:uppercase; letter-spacing:0.5px;">Priority #{p['rank']}</span>
                            <h4 style="margin:4px 0 0 0; color:#1c1c1e; font-size:1.2rem;">{p['name']} ({p['borrower_id']})</h4>
                            <span style="font-size:0.78rem; color:#636366;">Scheme: {p['loan_scheme']} | Region: {p['region']}</span>
                        </div>
                        <span style="background:{badge_color}12; color:{badge_color}; font-weight:700; font-size:0.78rem; padding:4px 10px; border-radius:12px; border:1px solid {badge_color}25;">
                            {p['workload_type']}
                        </span>
                    </div>
                    
                    <div style="margin-bottom:16px;">
                        <span style="font-size:0.75rem; color:#636366; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; display:block; margin-bottom:6px;">Risk Signal Drivers</span>
                        {reasons_html}
                    </div>
                    
                    <div style="background:rgba(34,197,94,0.04); border:1px solid rgba(34,197,94,0.12); border-radius:12px; padding:12px 16px; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-size:0.7rem; color:#15803d; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; display:block;">Recommended Intervention</span>
                            <span style="font-weight:700; color:#15803d; font-size:0.95rem;">{p['recommended_action']}</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-size:0.7rem; color:#636366; font-weight:700; text-transform:uppercase; display:block;">Recovery Prob</span>
                            <span style="font-weight:800; color:#22c55e; font-size:1.15rem;">{p['recovery_probability']}%</span>
                        </div>
                    </div>
                    
                    <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#636366; margin-bottom:20px; border-bottom:1px solid rgba(0,0,0,0.06); padding-bottom:12px;">
                        <span><b>Estimated Exposure:</b> ₹{p['exposure']/1e5:.2f} Lakhs</span>
                        <span><b>AI Confidence Score:</b> {p['confidence_score']}%</span>
                    </div>
                    
                    <!-- Explainability bar grid -->
                    <div style="margin-bottom:20px;">
                        <span style="font-size:0.75rem; color:#636366; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; display:block; margin-bottom:10px;">Explainability Risk Breakdown</span>
                        
                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                            <div>
                                <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#48484a; margin-bottom:3px;">
                                    <span>Behavioral Deterioration</span>
                                    <span style="font-weight:600;">{p['explainability']['behavior']}%</span>
                                </div>
                                <div style="height:6px; background:#e5e5ea; border-radius:3px; overflow:hidden;">
                                    <div style="height:100%; width:{p['explainability']['behavior']}%; background:#ef4444; border-radius:3px;"></div>
                                </div>
                            </div>
                            
                            <div>
                                <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#48484a; margin-bottom:3px;">
                                    <span>Regional Macro Stress</span>
                                    <span style="font-weight:600;">{p['explainability']['regional']}%</span>
                                </div>
                                <div style="height:6px; background:#e5e5ea; border-radius:3px; overflow:hidden;">
                                    <div style="height:100%; width:{p['explainability']['regional']}%; background:#f59e0b; border-radius:3px;"></div>
                                </div>
                            </div>
                            
                            <div>
                                <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#48484a; margin-bottom:3px;">
                                    <span>Network Exposure Stress</span>
                                    <span style="font-weight:600;">{p['explainability']['network']}%</span>
                                </div>
                                <div style="height:6px; background:#e5e5ea; border-radius:3px; overflow:hidden;">
                                    <div style="height:100%; width:{p['explainability']['network']}%; background:#3b82f6; border-radius:3px;"></div>
                                </div>
                            </div>
                            
                            <div>
                                <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#48484a; margin-bottom:3px;">
                                    <span>Peer Group Deviation</span>
                                    <span style="font-weight:600;">{p['explainability']['peer']}%</span>
                                </div>
                                <div style="height:6px; background:#e5e5ea; border-radius:3px; overflow:hidden;">
                                    <div style="height:100%; width:{p['explainability']['peer']}%; background:#8b5cf6; border-radius:3px;"></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                """
                render_safe_html(card_html)
                
                a_bid = p["borrower_id"]
                a_name = p["name"]
                
                act_col1, act_col2, act_col3 = st.columns(3)
                with act_col1:
                    if st.button("✉️ Send Reminder (Email/SMS)", key=f"cop_rem_{a_bid}", use_container_width=True):
                        from communication_engine import send_otp_email, send_otp_sms, CommunicationService
                        borrowers_list = pd.read_csv("borrowers.csv")
                        b_meta = borrowers_list[borrowers_list["borrower_id"] == a_bid]
                        if not b_meta.empty:
                            email = str(b_meta.iloc[0]["email"])
                            mobile = str(b_meta.iloc[0]["mobile_number"])
                            CommunicationService.send_email(email, "Bandhan Bank - Urgent Delinquency Review Notification", f"Dear {a_name},\n\nThis is a notification regarding outstanding dues on your Stand-up/MSME account. Contact branch immediately for restructuring options.\n\nBest regards,\nBandhan Bank Operations")
                            CommunicationService.send_sms(mobile, f"Bandhan Bank: Delinquency review alert. Contact your Relationship Manager immediately to avoid score drop.")
                            audit_log("Recovery Operations", "SMS Reminder Sent", borrower_id=a_bid, reason="Copilot RM interface automated SMS trigger")
                            audit_log("Recovery Operations", "Warning Email Sent", borrower_id=a_bid, reason="Copilot RM interface automated warning email trigger")
                            st.success(f"Receipt warnings successfully dispatched to {a_name}!")
                            
                with act_col2:
                    if st.button("🗓️ Schedule Field Visit", key=f"cop_visit_{a_bid}", use_container_width=True):
                        audit_log("Recovery Operations", "Branch Visit Scheduled", borrower_id=a_bid, reason="Direct outreach recovery visit scheduled via Copilot priorities panel")
                        st.success(f"Field outreach visit scheduled and logged for {a_name}.")
                        
                with act_col3:
                    st.info("Switch Explorer tab to view details.")

    with right_col:
        st.markdown("### 💡 Smart Recovery Insights")
        render_safe_html(
            f"""
            <div style="background:rgba(255,255,255,0.6); border:1px solid rgba(0,0,0,0.06); border-radius:18px; padding:20px; margin-bottom:24px;">
                <div style="margin-bottom:14px; border-bottom:1px solid rgba(0,0,0,0.04); padding-bottom:8px;">
                    <span style="font-size:0.75rem; color:#636366; font-weight:700; text-transform:uppercase;">Highest New Risk Region</span>
                    <div style="font-weight:700; font-size:1.05rem; color:#ef4444;">🌍 {insights['highest_risk_region']}</div>
                </div>
                
                <div style="margin-bottom:14px; border-bottom:1px solid rgba(0,0,0,0.04); padding-bottom:8px;">
                    <span style="font-size:0.75rem; color:#636366; font-weight:700; text-transform:uppercase;">Loan Scheme Under Highest Stress</span>
                    <div style="font-weight:700; font-size:1.05rem; color:#f59e0b;">🛡️ {insights['stressed_scheme']}</div>
                </div>
                
                <div style="margin-bottom:14px; border-bottom:1px solid rgba(0,0,0,0.04); padding-bottom:8px;">
                    <span style="font-size:0.75rem; color:#636366; font-weight:700; text-transform:uppercase;">Branch with Fastest Improving Recovery</span>
                    <div style="font-weight:700; font-size:1.05rem; color:#22c55e;">🏢 {insights['fastest_improving_branch']}</div>
                </div>
                
                <div style="margin-bottom:14px; border-bottom:1px solid rgba(0,0,0,0.04); padding-bottom:8px;">
                    <span style="font-size:0.75rem; color:#636366; font-weight:700; text-transform:uppercase;">Largest Active Delinquency Clusters</span>
                    <div style="font-weight:600; font-size:0.95rem; color:#48484a;">🕸️ {insights['largest_risk_clusters']}</div>
                </div>
                
                <div>
                    <span style="font-size:0.75rem; color:#636366; font-weight:700; text-transform:uppercase;">Highest Peer Group Health Deviation</span>
                    <div style="font-weight:600; font-size:0.95rem; color:#8b5cf6;">📈 {insights['highest_peer_deviation']}</div>
                </div>
            </div>
            """
        )
        
        st.markdown("### ⏳ Workload Optimization")
        render_safe_html(
            f"""
            <div style="background:rgba(255,255,255,0.6); border:1px solid rgba(0,0,0,0.06); border-radius:18px; padding:20px; margin-bottom:24px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:12px; border-bottom:1px solid rgba(0,0,0,0.04); padding-bottom:8px;">
                    <span style="color:#636366; font-size:0.85rem;">Digital outreach accounts</span>
                    <span style="font-weight:700; color:#3b82f6;">{workload['digital_count']}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:12px; border-bottom:1px solid rgba(0,0,0,0.04); padding-bottom:8px;">
                    <span style="color:#636366; font-size:0.85rem;">Physical field visit accounts</span>
                    <span style="font-weight:700; color:#f59e0b;">{workload['physical_count']}</span>
                </div>
                <div style="display:flex; justify-content:space-between; margin-bottom:16px;">
                    <span style="color:#636366; font-size:0.85rem;">Urgent zonal escalations</span>
                    <span style="font-weight:700; color:#ef4444;">{workload['escalation_count']}</span>
                </div>
                
                <div style="background:rgba(34,197,94,0.04); border:1px solid rgba(34,197,94,0.12); border-radius:12px; padding:14px; text-align:center;">
                    <span style="font-size:0.72rem; color:#15803d; font-weight:700; text-transform:uppercase; display:block; margin-bottom:4px;">Savings by Prioritization Plan</span>
                    <div style="font-size:1.25rem; font-weight:800; color:#15803d; margin-bottom:2px;">
                        ⌛ {workload['estimated_time_saved_hrs']:.1f} Hrs Saved | 🚗 {workload['estimated_travel_saved_km']:.0f} KM Travel Saved
                    </div>
                    <span style="font-size:0.75rem; color:#166534; display:block;">Projected recovery success: <b>+{workload['recovery_improvement_pct']}%</b></span>
                </div>
            </div>
            """
        )
        
        st.markdown("### 🎯 Portfolio Opportunities")
        opportunity_cards = "".join(f"<div style='font-size:0.88rem; line-height:1.45; color:#1c1c1e; margin-bottom:12px; padding:10px; background:rgba(255,255,255,0.4); border:1px solid rgba(0,0,0,0.03); border-radius:12px;'>{o}</div>" for o in opportunities)
        render_safe_html(
            f"""
            <div style="background:rgba(255,255,255,0.6); border:1px solid rgba(0,0,0,0.06); border-radius:18px; padding:20px; margin-bottom:24px;">
                {opportunity_cards}
            </div>
            """
        )
        
        st.markdown("### 🤖 Reinforcement Learning Progress")
        render_safe_html(
            f"""
            <div style="background:rgba(255,255,255,0.6); border:1px solid rgba(0,0,0,0.06); border-radius:18px; padding:20px; margin-bottom:24px;">
                <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#48484a; margin-bottom:4px;">
                    <span>Copilot Learning loop cycle</span>
                    <span style="font-weight:600;">{learning['learning_progress_pct']}%</span>
                </div>
                <div style="height:8px; background:#e5e5ea; border-radius:4px; overflow:hidden; margin-bottom:16px;">
                    <div style="height:100%; width:{learning['learning_progress_pct']}%; background:#8b5cf6; border-radius:4px;"></div>
                </div>
                
                <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#48484a; margin-bottom:4px;">
                    <span>Priority Recommendation Accuracy</span>
                    <span style="font-weight:600;">{learning['accuracy_rate']}%</span>
                </div>
                <div style="height:8px; background:#e5e5ea; border-radius:4px; overflow:hidden; margin-bottom:16px;">
                    <div style="height:100%; width:{learning['accuracy_rate']}%; background:#22c55e; border-radius:4px;"></div>
                </div>
                
                <div style="display:flex; justify-content:space-between; font-size:0.85rem; color:#48484a; margin-bottom:4px;">
                    <span>Overall Recovery Improvement Rate</span>
                    <span style="font-weight:600;">{learning['recovery_improvement_pct']}%</span>
                </div>
                <div style="height:8px; background:#e5e5ea; border-radius:4px; overflow:hidden;">
                    <div style="height:100%; width:{learning['recovery_improvement_pct']*4}%; background:#3b82f6; border-radius:4px;"></div>
                </div>
            </div>
            """
        )


def render_admin_dashboard() -> None:
    admin_name = st.session_state.get("admin_username", "Admin").title()

    portfolio_df = build_portfolio_df(
        borrowers_df, transactions_df, regional_df
    )
    summary = detector.portfolio_summary()
    clusters = detector.detect_stress_clusters()
    critical_alerts_count = len(portfolio_df[portfolio_df["risk_score"] >= 80])
    due_today_count = len(portfolio_df[portfolio_df["days_past_due"] > 0])
    field_visits_count = len(clusters)
    follow_ups_count = summary.get("high_risk_borrowers", 0)

    # Initialize admin navigation state
    if "admin_nav_page" not in st.session_state:
        st.session_state.admin_nav_page = "Action Center"
    current_page = st.session_state.admin_nav_page

    # Enterprise Dark Espresso Sidebar matching Bandhan Loan Recovery Mgmt reference
    sidebar_slot = st.sidebar.empty()
    with sidebar_slot.container():
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 12px; padding: 4px 0 20px 0; border-bottom: 1px solid #3E2B20; margin-bottom: 14px;">
                <div style="
                    width: 36px; height: 36px; min-width: 36px;
                    background: rgba(212, 163, 115, 0.2);
                    border: 1px solid rgba(212, 163, 115, 0.45);
                    border-radius: 8px;
                    display: flex; align-items: center; justify-content: center;
                    font-weight: 800; font-size: 1.2rem; color: #D4A373;
                ">B</div>
                <div>
                    <div style="font-size: 0.92rem; font-weight: 800; letter-spacing: 1.2px; color: #FFFFFF; line-height: 1.1;">BANDHAN</div>
                    <div style="font-size: 0.65rem; font-weight: 600; color: #A8988B; letter-spacing: 0.8px;">LOAN RECOVERY MGMT</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        nav_items = [
            ("📊", "Action Center"),
            ("📁", "Dashboard"),
            ("👤", "Borrowers"),
            ("💳", "Loan Accounts"),
            ("🛡️", "Recovery Cases"),
            ("🤖", "AI Risk Engine"),
            ("📈", "Analytics & Reports"),
            ("📄", "Documents"),
        ]

        for icon, label in nav_items:
            is_active = (current_page == label)
            btn_key = f"admin_nav_{label.lower().replace(' ', '_').replace('&', 'and')}"
            if st.button(
                f"{icon}  {label}",
                key=btn_key,
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                if st.session_state.admin_nav_page != label:
                    st.session_state.admin_nav_page = label
                    st.rerun()

        st.markdown(
            """
            <div style="border-top: 1px solid #3E2B20; margin-top: 18px; margin-bottom: 10px;"></div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "⚙️  Settings",
            key="admin_nav_settings",
            use_container_width=True,
            type="primary" if current_page == "Settings" else "secondary",
        ):
            if st.session_state.admin_nav_page != "Settings":
                st.session_state.admin_nav_page = "Settings"
                st.rerun()

        if st.button(
            "❓  Help & Support",
            key="admin_nav_help",
            use_container_width=True,
            type="primary" if current_page == "Help & Support" else "secondary",
        ):
            if st.session_state.admin_nav_page != "Help & Support":
                st.session_state.admin_nav_page = "Help & Support"
                st.rerun()

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sidebar-signout-container">', unsafe_allow_html=True)
        if st.button("Sign Out", key="sidebar_logout_btn", use_container_width=True):
            logout()
        st.markdown('</div>', unsafe_allow_html=True)

    # Top Breadcrumb and Profile Bar
    top_bc_col, top_profile_col = st.columns([5, 3])
    with top_bc_col:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 8px; font-size: 0.84rem; color: #8C7E72; font-weight: 600; padding: 2px 0 12px 0;">
                <span>Home</span>
                <span style="color: #C6B9A8;">›</span>
                <span style="color: #2C1E16;">{escape(current_page)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_profile_col:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: flex-end; gap: 10px; margin-bottom: 8px;">
                <div style="
                    background: #FFFFFF; border: 1px solid #DFD7CC; border-radius: 8px; padding: 6px 12px;
                    font-size: 0.8rem; font-weight: 600; color: #2C1E16; cursor: pointer; box-shadow: 0 1px 2px rgba(44,30,22,0.04);
                ">⟳ Sync</div>
                <div style="
                    background: #FFFFFF; border: 1px solid #DFD7CC; border-radius: 8px; padding: 6px 10px;
                    font-size: 0.85rem; cursor: pointer; position: relative; box-shadow: 0 1px 2px rgba(44,30,22,0.04);
                ">🔔<span style="position: absolute; top: 4px; right: 5px; width: 6px; height: 6px; background: #D97706; border-radius: 50%;"></span></div>
                <div style="
                    background: #FFFFFF; border: 1px solid #DFD7CC; border-radius: 999px; padding: 3px 12px 3px 6px;
                    display: flex; align-items: center; gap: 8px; box-shadow: 0 1px 2px rgba(44,30,22,0.04);
                ">
                    <div style="
                        width: 28px; height: 28px; border-radius: 50%; background: #6B3F23; color: #FFFFFF;
                        display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700;
                    ">{admin_name[:2].upper()}</div>
                    <div style="text-align: left; line-height: 1.15;">
                        <div style="font-size: 0.8rem; font-weight: 700; color: #2C1E16;">{escape(admin_name)}</div>
                        <div style="font-size: 0.65rem; color: #8C7E72;">Branch Manager</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Base filtered dataset
    risk_floor = 45
    filtered = portfolio_df[portfolio_df["risk_score"] >= risk_floor].copy()

    # ─────────────────────────────────────────────────────────────
    # PAGE 1: ACTION CENTER (Matching Image 2 Reference)
    # ─────────────────────────────────────────────────────────────
    if current_page == "Action Center":
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;">
                <div>
                    <h1 style="font-size: 1.95rem; font-weight: 800; color: #2C1E16; margin: 0 0 4px 0; letter-spacing: -0.5px;">Action Center</h1>
                    <p style="font-size: 0.88rem; color: #6E5F52; margin: 0;">Review tasks, alerts, and recovery activities requiring your attention.</p>
                </div>
                <div style="font-size: 0.78rem; color: #8C7E72;">
                    Last updated: <strong>Today, 10:42 AM</strong> &nbsp;
                    <span style="cursor: pointer; color: #6B3F23; font-weight: 600;">⟳ Refresh</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 4 Enterprise KPI Cards matching Image 2
        st.markdown(
            f"""
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;">
                <div style="background: #FFF0F0; border: 1px solid #FCD4D4; border-radius: 12px; padding: 16px 20px;">
                    <div style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px; color: #C53030; text-transform: uppercase;">CRITICAL ALERTS</div>
                    <div style="font-size: 2.1rem; font-weight: 800; color: #C53030; margin: 2px 0;">{critical_alerts_count}</div>
                    <div style="font-size: 0.75rem; color: #9B2C2C;">Immediate action needed</div>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E8E1D5; border-radius: 12px; padding: 16px 20px; box-shadow: 0 1px 3px rgba(44,30,22,0.04);">
                    <div style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px; color: #8C7E72; text-transform: uppercase;">DUE TODAY</div>
                    <div style="font-size: 2.1rem; font-weight: 800; color: #2C1E16; margin: 2px 0;">{due_today_count}</div>
                    <div style="font-size: 0.75rem; color: #6E5F52;">Tasks and follow-ups</div>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E8E1D5; border-radius: 12px; padding: 16px 20px; box-shadow: 0 1px 3px rgba(44,30,22,0.04);">
                    <div style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px; color: #8C7E72; text-transform: uppercase;">FIELD VISITS</div>
                    <div style="font-size: 2.1rem; font-weight: 800; color: #2C1E16; margin: 2px 0;">{field_visits_count}</div>
                    <div style="font-size: 0.75rem; color: #6E5F52;">Scheduled clusters</div>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E8E1D5; border-radius: 12px; padding: 16px 20px; box-shadow: 0 1px 3px rgba(44,30,22,0.04);">
                    <div style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px; color: #8C7E72; text-transform: uppercase;">FOLLOW-UPS</div>
                    <div style="font-size: 2.1rem; font-weight: 800; color: #2C1E16; margin: 2px 0;">{follow_ups_count}</div>
                    <div style="font-size: 0.75rem; color: #6E5F52;">Pending responses</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Quick Jump Toolbar (Matching horizontal pills in Image 2)
        q_cols = st.columns(6)
        with q_cols[0]:
            if st.button("📁 Portfolio Overview", key="ac_to_dash", use_container_width=True):
                st.session_state.admin_nav_page = "Dashboard"
                st.rerun()
        with q_cols[1]:
            if st.button("👤 Borrower Explorer", key="ac_to_borr", use_container_width=True):
                st.session_state.admin_nav_page = "Borrowers"
                st.rerun()
        with q_cols[2]:
            if st.button("💳 Loan Accounts", key="ac_to_loans", use_container_width=True):
                st.session_state.admin_nav_page = "Loan Accounts"
                st.rerun()
        with q_cols[3]:
            if st.button("🛡️ Bandhan-Recover AI", key="ac_to_recover", use_container_width=True):
                st.session_state.admin_nav_page = "Recovery Cases"
                st.rerun()
        with q_cols[4]:
            if st.button("🤖 RM Copilot AI", key="ac_to_copilot", use_container_width=True):
                st.session_state.admin_nav_page = "AI Risk Engine"
                st.rerun()
        with q_cols[5]:
            if st.button("📈 Context & Cohorts", key="ac_to_cohorts", use_container_width=True):
                st.session_state.admin_nav_page = "Analytics & Reports"
                st.rerun()

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("#### Portfolio Filters")
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        with filter_col1:
            risk_floor = st.slider("Min Risk Score", 0, 100, 45, 5, key="ac_risk_floor")
        with filter_col2:
            region_filter = st.selectbox("Region", ["All"] + sorted(portfolio_df["region"].unique().tolist()), key="ac_region")
        with filter_col3:
            scheme_filter = st.selectbox("Loan Scheme", ["All"] + sorted(portfolio_df["loan_scheme"].unique().tolist()), key="ac_scheme")
        with filter_col4:
            status_filter = st.selectbox("Status", ["All", "ACTIVE", "SUPPORT_REQUIRED", "RECOVERING", "WATCHLIST"], key="ac_status")
        
        # Apply filters
        ac_filtered = portfolio_df.copy()
        ac_filtered = ac_filtered[ac_filtered["risk_score"] >= risk_floor]
        if region_filter != "All":
            ac_filtered = ac_filtered[ac_filtered["region"] == region_filter]
        if scheme_filter != "All":
            ac_filtered = ac_filtered[ac_filtered["loan_scheme"] == scheme_filter]
        if status_filter != "All":
            ac_filtered = ac_filtered[ac_filtered["status"] == status_filter]
            
        st.subheader("Borrowers Requiring Attention")
        display_cols = ["borrower_id", "name", "loan_scheme", "region", "risk_score", "health_score", "risk_level", "status"]
        render_glass_table(
            ac_filtered[display_cols].sort_values(["risk_score", "health_score"], ascending=[False, True]).head(40),
            max_height=520,
        )

    # ─────────────────────────────────────────────────────────────
    # PAGE 2: DASHBOARD (Portfolio Overview & Analytics)
    # ─────────────────────────────────────────────────────────────
    elif current_page == "Dashboard":
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;">
                <div>
                    <h1 style="font-size: 1.95rem; font-weight: 800; color: #2C1E16; margin: 0 0 4px 0; letter-spacing: -0.5px;">Portfolio Analytics Dashboard</h1>
                    <p style="font-size: 0.88rem; color: #6E5F52; margin: 0;">Real-time portfolio overview, risk concentration, and loan scheme distribution.</p>
                </div>
                <div style="font-size: 0.78rem; color: #8C7E72;">
                    Portfolio Status: <strong style="color: #10B981;">Operational</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        d_filter_col1, d_filter_col2, d_filter_col3, d_filter_col4 = st.columns(4)
        with d_filter_col1:
            d_risk_floor = st.slider("Min Risk Score", 0, 100, 45, 5, key="dash_risk_floor")
        with d_filter_col2:
            d_region = st.selectbox("Region", ["All"] + sorted(portfolio_df["region"].unique().tolist()), key="dash_region")
        with d_filter_col3:
            d_scheme = st.selectbox("Loan Scheme", ["All"] + sorted(portfolio_df["loan_scheme"].unique().tolist()), key="dash_scheme")
        with d_filter_col4:
            d_status = st.selectbox("Status", ["All", "ACTIVE", "SUPPORT_REQUIRED", "RECOVERING", "WATCHLIST"], key="dash_status")

        d_filtered = portfolio_df.copy()
        d_filtered = d_filtered[d_filtered["risk_score"] >= d_risk_floor]
        if d_region != "All":
            d_filtered = d_filtered[d_filtered["region"] == d_region]
        if d_scheme != "All":
            d_filtered = d_filtered[d_filtered["loan_scheme"] == d_scheme]
        if d_status != "All":
            d_filtered = d_filtered[d_filtered["status"] == d_status]

        # Total At-Risk Exposure Banner
        try:
            import requests
            res = requests.get(f"{API_BASE_URL}/portfolio/summary", timeout=3)
            if res.status_code == 200:
                summary_data = res.json()
                counts = summary_data.get("band_counts", {})
                
                st.markdown(
                    f'''
                    <div style="background: #FFFFFF; border: 1px solid #E8E1D5; border-radius: 14px; 
                                padding: 20px 24px; box-shadow: 0 2px 8px rgba(44, 30, 22, 0.04); margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="font-size: 0.72rem; font-weight: 700; color: #8C7E72; letter-spacing: 0.8px; text-transform: uppercase;">Total At-Risk Exposure</div>
                                <div style="font-size: 2.3rem; font-weight: 800; color: #C53030; margin-top: 2px;">Rs {summary_data.get('at_risk_exposure', 0):,.2f}</div>
                            </div>
                            <div style="display: flex; gap: 24px; text-align: center;">
                                <div><div style="font-size: 0.72rem; color: #8C7E72; font-weight: 600;">CRITICAL</div><div style="font-size: 1.5rem; font-weight: 800; color: #C53030;">{counts.get("CRITICAL", 0)}</div></div>
                                <div><div style="font-size: 0.72rem; color: #8C7E72; font-weight: 600;">HIGH</div><div style="font-size: 1.5rem; font-weight: 800; color: #D97706;">{counts.get("HIGH", 0)}</div></div>
                                <div><div style="font-size: 0.72rem; color: #8C7E72; font-weight: 600;">MODERATE</div><div style="font-size: 1.5rem; font-weight: 800; color: #2563EB;">{counts.get("MODERATE", 0)}</div></div>
                                <div><div style="font-size: 0.72rem; color: #8C7E72; font-weight: 600;">LOW</div><div style="font-size: 1.5rem; font-weight: 800; color: #10B981;">{counts.get("LOW", 0)}</div></div>
                            </div>
                        </div>
                    </div>
                    ''', 
                    unsafe_allow_html=True
                )
            else:
                st.warning("Could not load backend portfolio summary.")
        except Exception as e:
            st.error(f"Failed to connect to RiskNet backend `uvicorn main:app --reload --port 8000`. Error: {str(e)}")

        dash_chart_col1, dash_chart_col2 = st.columns(2)
        with dash_chart_col1:
            st.subheader("Risk by Region")
            risk_by_region = (
                d_filtered.groupby("region", as_index=False)
                .agg(average_risk=("risk_score", "mean"), average_health=("health_score", "mean"))
                .sort_values("average_risk", ascending=False)
            )
            if not risk_by_region.empty:
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=risk_by_region["region"],
                    y=[100] * len(risk_by_region),
                    marker_color='rgba(200, 200, 205, 0.25)',
                    hoverinfo='skip',
                    showlegend=False
                ))
                fig.add_trace(go.Bar(
                    x=risk_by_region["region"],
                    y=risk_by_region["average_risk"],
                    marker=dict(
                        color=risk_by_region["average_risk"],
                        colorscale="YlOrRd",
                        colorbar=dict(title="Avg Risk", thickness=15)
                    ),
                    text=[f"{val:.1f}" for val in risk_by_region["average_risk"]],
                    textposition='outside',
                    showlegend=False,
                    name='Risk'
                ))
                fig.update_layout(
                    barmode='overlay',
                    bargap=0.4,
                    yaxis_title="Average Risk",
                    xaxis_title="Region",
                    yaxis=dict(showgrid=False, zeroline=False, range=[0, 110]),
                    xaxis=dict(showgrid=False),
                    margin=dict(l=16, r=16, t=32, b=44)
                )
                try:
                    fig.update_traces(marker_cornerradius="30%")
                except Exception:
                    pass
                avg_risk = risk_by_region["average_risk"].mean() if not risk_by_region["average_risk"].empty else 0
                if avg_risk > 0:
                    fig.add_hline(y=avg_risk, line_dash="dot", line_color="rgba(0,0,0,0.3)")
                st.plotly_chart(style_figure(fig), use_container_width=True, theme=None)

        with dash_chart_col2:
            st.subheader("Loan Scheme Mix")
            scheme_mix = d_filtered.groupby("loan_scheme", as_index=False).size()
            if not scheme_mix.empty:
                fig = px.pie(scheme_mix, names="loan_scheme", values="size", hole=0.45)
                fig.update_layout(
                    margin=dict(l=16, r=16, t=32, b=20),
                    paper_bgcolor="rgba(255,255,255,0.18)",
                    font=dict(color="#1c1c1e"),
                    legend=dict(
                        bgcolor="rgba(255,255,255,0.16)",
                        bordercolor="rgba(255,255,255,0.35)",
                        borderwidth=1,
                    ),
                )
                st.plotly_chart(fig, use_container_width=True, theme=None)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("AI Risk Band Distribution Table")
        display_cols = ["borrower_id", "name", "loan_scheme", "region", "risk_score", "health_score", "risk_level", "status"]
        render_glass_table(
            d_filtered[display_cols].sort_values(["risk_score", "health_score"], ascending=[False, True]).head(50),
            max_height=520,
        )

    # ─────────────────────────────────────────────────────────────
    # PAGE 3: BORROWERS (Borrower Explorer Drilldown)
    # ─────────────────────────────────────────────────────────────
    elif current_page == "Borrowers":
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;">
                <div>
                    <h1 style="font-size: 1.95rem; font-weight: 800; color: #2C1E16; margin: 0 0 4px 0; letter-spacing: -0.5px;">Borrower Explorer Drilldown</h1>
                    <p style="font-size: 0.88rem; color: #6E5F52; margin: 0;">Inspect borrower risk transparency, repayment histories, and local contagion network.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        borrower_options = filtered["borrower_id"].tolist() if not filtered.empty else portfolio_df["borrower_id"].tolist()
        selected_borrower = st.selectbox("Select borrower", borrower_options, key="drilldown_selected_borr")
        if f"admin_view_{selected_borrower}" not in st.session_state:
            st.session_state[f"admin_view_{selected_borrower}"] = True
            audit_log("Borrower Actions", "Borrower Viewed", borrower_id=selected_borrower, reason="Administrator reviewed borrower profile details in explorer portal")
            
        borrower_record = detector.analyze_borrower(selected_borrower).as_dict()
        borrower_profile = borrowers_df[borrowers_df["borrower_id"] == selected_borrower].iloc[0]
        borrower_state = repo.get_borrower(selected_borrower) or repo.ensure_borrower(selected_borrower, borrower_record["name"])

        top_left, top_right = st.columns([1.2, 1])
        with top_left:
            st.markdown(f"### {borrower_record['name']}")
            st.write(f"Borrower ID: `{selected_borrower}`")
            st.write(f"Scheme: `{borrower_record['loan_scheme']}`")
            st.write(f"Region: `{borrower_record['region']}`")
            st.write(f"Current Status: `{borrower_state.get('status', 'ACTIVE')}`")
            st.write(borrower_record["recommendation"])

            button_cols = st.columns(2)
            import requests as req

            if button_cols[0].button(
                "Mark Support Required", 
                use_container_width=True,
                key=f"btn_supp_{selected_borrower}"
            ):
                try:
                    repo.set_status(
                        selected_borrower,
                        "SUPPORT_REQUIRED",
                        "Dashboard intervention recommendation",
                        "dashboard"
                    )
                    
                    audit_log(
                        category="Administration",
                        action="Risk Status Changed",
                        borrower_id=selected_borrower,
                        previous_value=borrower_state.get('status', 'ACTIVE'),
                        new_value="SUPPORT_REQUIRED",
                        reason="Manual admin classification to SUPPORT_REQUIRED"
                    )

                    api_resp = req.post(
                        f"{API_BASE_URL}/update-status/{selected_borrower}",
                        json={"status": "SUPPORT_REQUIRED"},
                        timeout=5
                    )
                    if api_resp.status_code == 200:
                        st.success("✅ Borrower marked as Support Required and Supabase updated.")
                    else:
                        st.warning("Marked locally but Supabase update failed. Check backend.")
                except Exception as e:
                    st.error(f"Update failed: {e}")

            if button_cols[1].button(
                "Mark Recovering", 
                use_container_width=True,
                key=f"btn_recov_{selected_borrower}"
            ):
                try:
                    repo.set_status(
                        selected_borrower,
                        "RECOVERING",
                        "Borrower moved to recovery monitoring",
                        "dashboard"
                    )

                    audit_log(
                        category="Administration",
                        action="Risk Status Changed",
                        borrower_id=selected_borrower,
                        previous_value=borrower_state.get('status', 'ACTIVE'),
                        new_value="RECOVERING",
                        reason="Manual admin classification to RECOVERING"
                    )

                    api_resp = req.post(
                        f"{API_BASE_URL}/update-status/{selected_borrower}",
                        json={"status": "RECOVERING"},
                        timeout=5
                    )
                    if api_resp.status_code == 200:
                        st.success("✅ Borrower marked as Recovering and Supabase updated.")
                    else:
                        st.warning("Marked locally but Supabase update failed. Check backend.")
                except Exception as e:
                    st.error(f"Update failed: {e}")

        with top_right:
            metric_a, metric_b, metric_c = st.columns(3)
            metric_a.metric("Risk Score", borrower_record["risk_score"])
            metric_b.metric("Health Score", borrower_record["health_score"])
            metric_c.metric("Peer Score", borrower_record["peer_score"])
            st.markdown(render_segmented_health_bar(borrower_record["health_score"], "Borrower Health"), unsafe_allow_html=True)

        flag_cols = st.columns(2)
        with flag_cols[0]:
            st.markdown("#### Behavioral Flags")
            flags = borrower_record["behavioral_flags"] or ["no_major_behavioral_flags"]
            html = "".join([f'<div class="flag-pill">{f.replace("_", " ").title()}</div>' for f in flags])
            st.markdown(html, unsafe_allow_html=True)
        with flag_cols[1]:
            st.markdown("#### Contextual Flags")
            flags = borrower_record["contextual_flags"] or ["no_major_contextual_flags"]
            html = "".join([f'<div class="flag-pill">{f.replace("_", " ").title()}</div>' for f in flags])
            st.markdown(html, unsafe_allow_html=True)

        txns = transactions_df[transactions_df["borrower_id"] == selected_borrower].sort_values("timestamp")
        
        emi_txns = txns[txns["transaction_type"] == "EMI_PAYMENT"].copy()
        if not emi_txns.empty:
            import plotly.graph_objects as go
            max_amt = emi_txns["amount"].max() * 1.2 if not emi_txns["amount"].empty else 5000
            txn_chart = go.Figure()
            
            txn_chart.add_trace(go.Bar(
                x=emi_txns["timestamp"].astype(str),
                y=[max_amt] * len(emi_txns),
                marker_color='rgba(200, 200, 205, 0.25)',
                hoverinfo='skip',
                showlegend=False
            ))
            
            txn_chart.add_trace(go.Bar(
                x=emi_txns["timestamp"].astype(str),
                y=emi_txns["amount"],
                marker_color='#FF5F2E',
                text=emi_txns["amount"],
                texttemplate='Rs %{text:,.0f}',
                textposition='outside',
                showlegend=False,
                name='Paid'
            ))
            
            txn_chart.update_layout(
                title="Borrower EMI Payment History",
                barmode='overlay',
                bargap=0.45,
                yaxis_title="Amount Paid (Rs)",
                xaxis_title="Payment Date",
                yaxis=dict(showgrid=False, zeroline=False),
                xaxis=dict(showgrid=False)
            )
            
            try:
                txn_chart.update_traces(marker_cornerradius="30%")
            except Exception:
                pass
            
            avg_emi = emi_txns["amount"].mean() if not emi_txns["amount"].empty else 0
            if avg_emi > 0:
                txn_chart.add_hline(y=avg_emi, line_dash="dot", line_color="rgba(0,0,0,0.3)")
        else:
            txn_chart = px.line(
                txns,
                x="timestamp",
                y="balance_after",
                color="transaction_type",
                markers=True,
                title="Recent Borrower Cash-Flow Trail",
            )
        txn_chart.update_layout(margin=dict(l=16, r=16, t=56, b=64))
        st.plotly_chart(style_figure(txn_chart), use_container_width=True, theme=None)

        details = pd.DataFrame(
            [
                {"Metric": "Loan Amount", "Value": f"Rs {borrower_profile.loan_amount:,.0f}"},
                {"Metric": "Outstanding Amount", "Value": f"Rs {borrower_profile.outstanding_amount:,.0f}"},
                {"Metric": "EMI Amount", "Value": f"Rs {borrower_profile.emi_amount:,.0f}"},
                {"Metric": "Days Past Due", "Value": int(borrower_profile.days_past_due)},
                {"Metric": "Regional Stress Factor", "Value": borrower_record["regional_stress_factor"]},
            ]
        )
        render_glass_table(details)

        st.markdown("### Transaction Summary")
        admin_window_label = st.selectbox(
            "Transaction window",
            ["30 Days", "60 Days", "90 Days", "All Available"],
            index=1,
            key=f"admin_window_{selected_borrower}",
        )
        admin_window_days = {"30 Days": 30, "60 Days": 60, "90 Days": 90, "All Available": 10000}[admin_window_label]
        st.markdown(render_transaction_days_card(txns, admin_window_days), unsafe_allow_html=True)

        st.markdown("### Payment Schedule")
        admin_schedule_data = []
        for _, row in txns.sort_values("timestamp", ascending=False).iterrows():
            if pd.notnull(row["timestamp"]):
                date_str = row["timestamp"].strftime("%m/%d/%Y") if hasattr(row["timestamp"], "strftime") else str(row["timestamp"])
            else:
                date_str = ""
            admin_schedule_data.append({
                "Payment Date": date_str,
                "Name": borrower_record["name"],
                "Payment Amount": f"Rs {row['amount']:,.2f}" if pd.notna(row['amount']) else "-",
                "Type": str(row["transaction_type"]).replace("_", " ").title(),
                "Status": "Paid" if str(row["status"]).upper() in ["COMPLETED", "SUCCESS", "PAID"] else str(row["status"]).title(),
                "Balance Left": f"Rs {row['balance_after']:,.2f}" if pd.notna(row['balance_after']) else "-"
            })
        admin_schedule_df = pd.DataFrame(admin_schedule_data)
        if not admin_schedule_df.empty:
            render_glass_table(admin_schedule_df, max_height=520)
        else:
            st.info("No payment history available.")

        st.markdown("<br><div style='font-size: 1.75rem; font-weight: 700; color: #1c1c1e;'>Local Knowledge Graph</div>", unsafe_allow_html=True)
        st.markdown("This live ego-graph visualizes risk contagion within a 2-hop radius around the selected borrower.")
        render_borrower_knowledge_graph(selected_borrower, detector, filtered)

    # ─────────────────────────────────────────────────────────────
    # PAGE 4: LOAN ACCOUNTS (Matching Image 3 Reference)
    # ─────────────────────────────────────────────────────────────
    elif current_page == "Loan Accounts":
        total_loans_count = len(portfolio_df)
        active_loans_count = len(portfolio_df[portfolio_df["status"] == "ACTIVE"])
        overdue_loans_count = len(portfolio_df[portfolio_df["days_past_due"] > 0])
        total_outstanding_amt = portfolio_df["outstanding_amount"].sum()
        overdue_outstanding_amt = portfolio_df[portfolio_df["days_past_due"] > 0]["outstanding_amount"].sum()

        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;">
                <div>
                    <h1 style="font-size: 1.95rem; font-weight: 800; color: #2C1E16; margin: 0 0 4px 0; letter-spacing: -0.5px;">Loan Accounts</h1>
                    <p style="font-size: 0.88rem; color: #6E5F52; margin: 0;">Manage active loans, repayment schedules, and recovery assignments.</p>
                </div>
                <div style="font-size: 0.78rem; color: #8C7E72;">
                    Total Accounts: <strong>{total_loans_count:,}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 4 Summary KPI Cards matching Image 3
        st.markdown(
            f"""
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;">
                <div style="background: #FFFFFF; border: 1px solid #E8E1D5; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(44,30,22,0.04);">
                    <div style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px; color: #8C7E72; text-transform: uppercase;">TOTAL LOANS</div>
                    <div style="font-size: 2.1rem; font-weight: 800; color: #2C1E16; margin: 2px 0;">{total_loans_count:,}</div>
                    <div style="font-size: 0.75rem; color: #10B981; font-weight: 600;">+4.2% this month</div>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E8E1D5; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(44,30,22,0.04);">
                    <div style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px; color: #8C7E72; text-transform: uppercase;">ACTIVE LOANS</div>
                    <div style="font-size: 2.1rem; font-weight: 800; color: #2C1E16; margin: 2px 0;">{active_loans_count:,}</div>
                    <div style="font-size: 0.75rem; color: #6E5F52;">{(active_loans_count/total_loans_count*100):.1f}% of total</div>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E8E1D5; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(44,30,22,0.04);">
                    <div style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px; color: #C53030; text-transform: uppercase;">OVERDUE LOANS</div>
                    <div style="font-size: 2.1rem; font-weight: 800; color: #C53030; margin: 2px 0;">{overdue_loans_count:,}</div>
                    <div style="font-size: 0.75rem; color: #9B2C2C;">{(overdue_loans_count/total_loans_count*100):.1f}% of total</div>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E8E1D5; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(44,30,22,0.04);">
                    <div style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px; color: #8C7E72; text-transform: uppercase;">TOTAL OUTSTANDING</div>
                    <div style="font-size: 2.1rem; font-weight: 800; color: #2C1E16; margin: 2px 0;">₹{total_outstanding_amt/10000000:.1f} Cr</div>
                    <div style="font-size: 0.75rem; color: #6E5F52;">₹{overdue_outstanding_amt/10000000:.1f} Cr overdue</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Filter bar
        l_col1, l_col2, l_col3, l_col4 = st.columns([2, 1, 1, 1])
        with l_col1:
            loan_search = st.text_input("Search Loan ID / Borrower", placeholder="Search by Loan ID or Borrower Name...", label_visibility="collapsed", key="loans_search_input")
        with l_col2:
            loan_status_filter = st.selectbox("Status Filter", ["All", "ACTIVE", "SUPPORT_REQUIRED", "RECOVERING", "WATCHLIST"], label_visibility="collapsed", key="loans_status_select")
        with l_col3:
            loan_scheme_filter = st.selectbox("Scheme Filter", ["All"] + sorted(portfolio_df["loan_scheme"].unique().tolist()), label_visibility="collapsed", key="loans_scheme_select")
        with l_col4:
            loan_region_filter = st.selectbox("Region Filter", ["All"] + sorted(portfolio_df["region"].unique().tolist()), label_visibility="collapsed", key="loans_region_select")

        loan_df = portfolio_df.copy()
        if loan_search:
            q = loan_search.strip().lower()
            loan_df = loan_df[loan_df["borrower_id"].str.lower().str.contains(q) | loan_df["name"].str.lower().str.contains(q)]
        if loan_status_filter != "All":
            loan_df = loan_df[loan_df["status"] == loan_status_filter]
        if loan_scheme_filter != "All":
            loan_df = loan_df[loan_df["loan_scheme"] == loan_scheme_filter]
        if loan_region_filter != "All":
            loan_df = loan_df[loan_df["region"] == loan_region_filter]

        # Monthly Repayment Collections Graph matching Image 3
        st.subheader("Monthly Repayment Collections")
        emi_all = transactions_df[transactions_df["transaction_type"] == "EMI_PAYMENT"].copy()
        if not emi_all.empty and "timestamp" in emi_all.columns:
            emi_all["month_year"] = pd.to_datetime(emi_all["timestamp"]).dt.strftime("%b %Y")
            monthly_coll = emi_all.groupby("month_year", as_index=False)["amount"].sum().tail(12)
            if not monthly_coll.empty:
                import plotly.graph_objects as go
                coll_fig = go.Figure()
                coll_fig.add_trace(go.Bar(
                    x=monthly_coll["month_year"],
                    y=monthly_coll["amount"] * 1.15,
                    name="Target",
                    marker_color='#E8E1D5',
                    hoverinfo='y'
                ))
                coll_fig.add_trace(go.Bar(
                    x=monthly_coll["month_year"],
                    y=monthly_coll["amount"],
                    name="Collected",
                    marker_color='#6B3F23',
                    text=[f"₹{val/100000:.1f}L" for val in monthly_coll["amount"]],
                    textposition='outside'
                ))
                coll_fig.update_layout(
                    barmode='group',
                    bargap=0.3,
                    yaxis_title="Amount (₹)",
                    xaxis_title="Month",
                    yaxis=dict(showgrid=False, zeroline=False),
                    xaxis=dict(showgrid=False),
                    margin=dict(l=16, r=16, t=24, b=40)
                )
                try:
                    coll_fig.update_traces(marker_cornerradius="25%")
                except Exception:
                    pass
                st.plotly_chart(style_figure(coll_fig), use_container_width=True, theme=None)

        st.subheader("Loan Accounts List")
        display_loan_cols = ["borrower_id", "name", "loan_scheme", "region", "loan_amount", "outstanding_amount", "emi_amount", "days_past_due", "risk_level", "status"]
        render_glass_table(
            loan_df[display_loan_cols].sort_values("days_past_due", ascending=False).head(50),
            max_height=560,
        )

    # ─────────────────────────────────────────────────────────────
    # PAGE 5: RECOVERY CASES (Matching Image 4 Reference)
    # ─────────────────────────────────────────────────────────────
    elif current_page == "Recovery Cases":
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;">
                <div>
                    <h1 style="font-size: 1.95rem; font-weight: 800; color: #2C1E16; margin: 0 0 4px 0; letter-spacing: -0.5px;">Bandhan-Recover AI & Recovery Cases</h1>
                    <p style="font-size: 0.88rem; color: #6E5F52; margin: 0;">Monitor and manage active loan recovery cases, follow-ups, and recovery progress.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_satark_recover_tab(filtered, portfolio_df, detector, repo)

    # ─────────────────────────────────────────────────────────────
    # PAGE 6: AI RISK ENGINE (RM Copilot & Contagion Simulator)
    # ─────────────────────────────────────────────────────────────
    elif current_page == "AI Risk Engine":
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;">
                <div>
                    <h1 style="font-size: 1.95rem; font-weight: 800; color: #2C1E16; margin: 0 0 4px 0; letter-spacing: -0.5px;">AI Risk Engine & Contagion Simulator</h1>
                    <p style="font-size: 0.88rem; color: #6E5F52; margin: 0;">Predictive credit risk analytics, relationship manager intelligence, and systemic contagion modelling.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        copilot_subtab, contagion_subtab = st.tabs(["💼 RM Copilot AI", "🌐 Contagion Simulator"])
        with copilot_subtab:
            render_rm_copilot_tab(portfolio_df, detector)
        with contagion_subtab:
            render_contagion_simulator(portfolio_df, detector, borrowers_df)

    # ─────────────────────────────────────────────────────────────
    # PAGE 7: ANALYTICS & REPORTS (Matching Image 5 Reference)
    # ─────────────────────────────────────────────────────────────
    elif current_page == "Analytics & Reports":
        total_disbursed = portfolio_df["loan_amount"].sum()
        total_outstanding = portfolio_df["outstanding_amount"].sum()
        total_recovered = max(0, total_disbursed - total_outstanding)
        recovery_rate = (total_recovered / total_disbursed * 100) if total_disbursed > 0 else 0
        overdue_portfolio = portfolio_df[portfolio_df["days_past_due"] > 0]["outstanding_amount"].sum()

        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;">
                <div>
                    <h1 style="font-size: 1.95rem; font-weight: 800; color: #2C1E16; margin: 0 0 4px 0; letter-spacing: -0.5px;">Analytics & Reports</h1>
                    <p style="font-size: 0.88rem; color: #6E5F52; margin: 0;">Bandhan Bank • Kolkata Central Branch • Portfolio performance overview</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 4 Summary KPI Cards matching Image 5
        st.markdown(
            f"""
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;">
                <div style="background: #FFFFFF; border: 1px solid #E8E1D5; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(44,30,22,0.04);">
                    <div style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px; color: #8C7E72; text-transform: uppercase;">TOTAL DISBURSED</div>
                    <div style="font-size: 2.1rem; font-weight: 800; color: #2C1E16; margin: 2px 0;">₹{total_disbursed/10000000:.2f} Cr</div>
                    <div style="font-size: 0.75rem; color: #6E5F52;">FY 2025-26 active portfolio</div>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E8E1D5; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(44,30,22,0.04);">
                    <div style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px; color: #8C7E72; text-transform: uppercase;">TOTAL RECOVERED</div>
                    <div style="font-size: 2.1rem; font-weight: 800; color: #2C1E16; margin: 2px 0;">₹{total_recovered/10000000:.2f} Cr</div>
                    <div style="font-size: 0.75rem; color: #10B981; font-weight: 600;">{recovery_rate:.1f}% of disbursed</div>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E8E1D5; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(44,30,22,0.04);">
                    <div style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px; color: #8C7E72; text-transform: uppercase;">RECOVERY RATE</div>
                    <div style="font-size: 2.1rem; font-weight: 800; color: #2C1E16; margin: 2px 0;">{recovery_rate:.1f}%</div>
                    <div style="font-size: 0.75rem; color: #6E5F52;">Target: 75.0%</div>
                </div>
                <div style="background: #FFFFFF; border: 1px solid #E8E1D5; border-radius: 12px; padding: 18px 20px; box-shadow: 0 1px 3px rgba(44,30,22,0.04);">
                    <div style="font-size: 0.7rem; font-weight: 700; letter-spacing: 0.8px; color: #C53030; text-transform: uppercase;">OVERDUE PORTFOLIO</div>
                    <div style="font-size: 2.1rem; font-weight: 800; color: #C53030; margin: 2px 0;">₹{overdue_portfolio/10000000:.2f} Cr</div>
                    <div style="font-size: 0.75rem; color: #9B2C2C;">{((overdue_portfolio/total_outstanding*100) if total_outstanding > 0 else 0):.1f}% of outstanding</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_regional_heatmap(regional_df, portfolio_df)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Peer Benchmarking and Regional Context")
        peer_view = (
            filtered.groupby(["loan_scheme", "region"], as_index=False)
            .agg(average_risk=("risk_score", "mean"), average_health=("health_score", "mean"), borrowers=("borrower_id", "count"))
            .sort_values("average_risk", ascending=False)
        )
        render_glass_table(peer_view, max_height=420)

        st.markdown("<br>", unsafe_allow_html=True)
        regional_chart = px.scatter(
            regional_df,
            x="regional_stress_factor",
            y="peer_health_baseline",
            size="npa_rate",
            color="region",
            hover_name="region",
            title="Regional Stress vs Peer Baseline",
        )
        regional_chart.update_layout(margin=dict(l=16, r=16, t=56, b=64))
        st.plotly_chart(style_figure(regional_chart), use_container_width=True, theme=None)

    # ─────────────────────────────────────────────────────────────
    # PAGE 8: DOCUMENTS & OPERATIONS
    # ─────────────────────────────────────────────────────────────
    elif current_page == "Documents":
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;">
                <div>
                    <h1 style="font-size: 1.95rem; font-weight: 800; color: #2C1E16; margin: 0 0 4px 0; letter-spacing: -0.5px;">Operations, Documents & Audit Center</h1>
                    <p style="font-size: 0.88rem; color: #6E5F52; margin: 0;">Compliance audit trail, administrative security logs, borrower communication center, and field visits.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        doc_sub1, doc_sub2, doc_sub3, doc_sub4 = st.tabs(
            ["📋 Audit & Compliance", "🛡️ Admin Security", "📨 Borrower Communication Center", "🗺️ Field Visit Planner"]
        )
        with doc_sub1:
            render_audit_compliance_center()
        with doc_sub2:
            render_admin_security_section()
        with doc_sub3:
            render_borrower_communication_center(portfolio_df, transactions_df)
        with doc_sub4:
            render_field_visit_planner(portfolio_df, detector)

    # ─────────────────────────────────────────────────────────────
    # PAGE 9: SETTINGS
    # ─────────────────────────────────────────────────────────────
    elif current_page == "Settings":
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;">
                <div>
                    <h1 style="font-size: 1.95rem; font-weight: 800; color: #2C1E16; margin: 0 0 4px 0; letter-spacing: -0.5px;">Settings & System Configuration</h1>
                    <p style="font-size: 0.88rem; color: #6E5F52; margin: 0;">Manage backend connectivity, alert thresholds, and operational preferences.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="section-card" style="margin-bottom: 24px;">
                <h4 style="margin: 0 0 16px 0; color: #2C1E16;">System Environment</h4>
                <div style="font-size: 0.88rem; color: #6E5F52; line-height: 1.8;">
                    <div>• <strong>Backend API Service:</strong> <code>{API_BASE_URL}</code></div>
                    <div>• <strong>Current User Role:</strong> Branch Administrator ({escape(admin_name)})</div>
                    <div>• <strong>Audit Trail Mode:</strong> Mandatory Immutable Local CSV Logging</div>
                    <div>• <strong>Graph Engine:</strong> Live 2-Hop Network Contagion Model</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("settings_form"):
            st.markdown("##### Alert & Risk Parameters")
            st.slider("High Risk Floor", 50, 90, 75, 5)
            st.slider("Delinquency DPD Threshold", 1, 90, 30, 1)
            st.checkbox("Enable Real-Time Email Notices", value=True)
            st.checkbox("Enable Automated SMS Restructuring Prompts", value=True)
            if st.form_submit_button("Save Preferences", type="primary"):
                st.success("Preferences updated successfully.")

    # ─────────────────────────────────────────────────────────────
    # PAGE 10: HELP & SUPPORT
    # ─────────────────────────────────────────────────────────────
    elif current_page == "Help & Support":
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;">
                <div>
                    <h1 style="font-size: 1.95rem; font-weight: 800; color: #2C1E16; margin: 0 0 4px 0; letter-spacing: -0.5px;">Help & Operational Support</h1>
                    <p style="font-size: 0.88rem; color: #6E5F52; margin: 0;">Standard operating procedures, recovery escalation matrix, and technical assistance.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                <div class="section-card">
                    <h4 style="margin: 0 0 12px 0; color: #2C1E16;">Branch Manager SOPs</h4>
                    <p style="font-size: 0.85rem; color: #6E5F52; line-height: 1.6;">
                        1. Daily Review: Check <strong>Action Center</strong> every morning for Critical Alerts (Risk ≥ 80).<br>
                        2. Support Flagging: Mark accounts needing intervention as <code>SUPPORT_REQUIRED</code> to notify field officers.<br>
                        3. Restructuring: Review borrower-initiated requests in <strong>Bandhan-Recover AI</strong> and approve modified EMI tenures.
                    </p>
                </div>
                <div class="section-card">
                    <h4 style="margin: 0 0 12px 0; color: #2C1E16;">Emergency Escalations</h4>
                    <p style="font-size: 0.85rem; color: #6E5F52; line-height: 1.6;">
                        • <strong>Central Credit Desk:</strong> credit-desk@bandhanbank.co.in<br>
                        • <strong>Recovery Ops Helpdesk:</strong> +91 1800 200 4567<br>
                        • <strong>IT & System Support:</strong> support@bandhanbank.co.in
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )



def render_landing_page() -> None:
    # Top Navigation
    nav_left, nav_right = st.columns([3, 1.2])
    with nav_right:
        st.markdown("<br>", unsafe_allow_html=True)
        btn1, btn2 = st.columns(2)
        if btn1.button("Admin Log In", use_container_width=True):
            st.session_state.view = "admin_login"
            st.rerun()
        if btn2.button("Borrowers", use_container_width=True):
            st.session_state.view = "borrower_login"
            st.rerun()

    # 1. Hero Section
    landing_hero_html = """<div class="landing-hero">
<div class="landing-copy">
<h1>BANDHAN</h1>
<p class="subtext">
Bandhan is proud to present the inaugural risk intelligence protocol — 
a high-stakes behavioral analysis engine bringing together the most talented 
investigators across the region to foster financial inclusivity.
</p>
<div class="landing-metrics">
<div class="metric-box">
<h3>10k+</h3>
<p>Borrowers Monitored</p>
</div>
<div class="metric-box">
<h3>45+</h3>
<p>Regions Analyzed</p>
</div>
<div class="metric-box">
<h3>GNN</h3>
<p>Live Risk Engine</p>
</div>
</div>
</div>
<div class="landing-art" style="padding: 20px 0 20px 20px; display: flex; justify-content: center;">
<div style="width: 100%; max-width: 480px; background: linear-gradient(155deg, #2C1E16 0%, #1E140E 100%); border: 1px solid #4A3326; border-radius: 28px; padding: 32px 28px; box-shadow: 0 24px 60px rgba(44, 30, 22, 0.25); color: #FFFFFF; position: relative; overflow: hidden;">
<!-- Top Protocol Header -->
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 22px;">
<div style="display: flex; align-items: center; gap: 10px;">
<div style="width: 32px; height: 32px; border-radius: 8px; background: rgba(212,163,115,0.2); border: 1px solid rgba(212,163,115,0.4); display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1rem; color: #D4A373;">B</div>
<div>
<div style="font-size: 0.82rem; font-weight: 800; letter-spacing: 1px; color: #FFFFFF;">BANDHAN CBHM</div>
<div style="font-size: 0.65rem; color: #A8988B; letter-spacing: 0.5px;">CONTINUOUS HEALTH MODEL</div>
</div>
</div>
<div style="display: flex; align-items: center; gap: 6px; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 20px; padding: 4px 10px; font-size: 0.7rem; font-weight: 700; color: #34D399;">
<span style="width: 6px; height: 6px; border-radius: 50%; background: #10B981; display: inline-block;"></span> LIVE ENGINE
</div>
</div>
<!-- Metric Highlight Card -->
<div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 18px; padding: 20px 22px; margin-bottom: 20px;">
<div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 12px;">
<div>
<div style="font-size: 0.72rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; color: #D4A373;">Portfolio Health Index</div>
<div style="font-size: 2.35rem; font-weight: 800; line-height: 1.05; color: #FFFFFF; letter-spacing: -0.5px; margin-top: 4px;">88.4<span style="font-size: 1.05rem; color: #A8988B; font-weight: 500;"> / 100</span></div>
</div>
<div style="text-align: right;">
<div style="font-size: 0.7rem; color: #A8988B; margin-bottom: 2px;">Default Risk</div>
<span style="display: inline-block; background: rgba(16, 185, 129, 0.2); color: #6EE7B7; border: 1px solid rgba(16, 185, 129, 0.3); font-weight: 700; font-size: 0.72rem; padding: 3px 8px; border-radius: 6px;">Minimal (2.1%)</span>
</div>
</div>
<div style="width: 100%; height: 8px; background: rgba(255, 255, 255, 0.1); border-radius: 4px; overflow: hidden;">
<div style="width: 88%; height: 100%; background: linear-gradient(90deg, #D4A373 0%, #10B981 100%); border-radius: 4px;"></div>
</div>
</div>
<!-- 3 Feature Chips -->
<div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px;">
<div style="display: flex; align-items: center; justify-content: space-between; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 10px 14px;">
<div style="display: flex; align-items: center; gap: 10px;">
<span style="font-size: 1rem;">📈</span>
<span style="font-size: 0.8rem; font-weight: 600; color: #E8E1D5;">Early Stress Detection</span>
</div>
<span style="font-size: 0.72rem; font-weight: 700; color: #34D399;">Active · 0 Defaults</span>
</div>
<div style="display: flex; align-items: center; justify-content: space-between; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 10px 14px;">
<div style="display: flex; align-items: center; gap: 10px;">
<span style="font-size: 1rem;">👥</span>
<span style="font-size: 0.8rem; font-weight: 600; color: #E8E1D5;">MSME Peer Benchmarking</span>
</div>
<span style="font-size: 0.72rem; font-weight: 700; color: #D4A373;">+14% vs Cohort</span>
</div>
<div style="display: flex; align-items: center; justify-content: space-between; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 10px 14px;">
<div style="display: flex; align-items: center; gap: 10px;">
<span style="font-size: 1rem;">🗺️</span>
<span style="font-size: 0.8rem; font-weight: 600; color: #E8E1D5;">Regional NPA Stress Signals</span>
</div>
<span style="font-size: 0.72rem; font-weight: 700; color: #A8988B;">45+ Districts</span>
</div>
</div>
<!-- Footer Tag -->
<div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 14px; font-size: 0.72rem; color: #A8988B;">
<span>🛡️ Indian Bank PSU Architecture</span>
<span style="color: #D4A373; font-weight: 600;">RBI Compliant</span>
</div>
</div>
</div>
</div>"""
    if hasattr(st, "html"):
        st.html(landing_hero_html)
    else:
        st.markdown(landing_hero_html, unsafe_allow_html=True)
    
    # 3. About Section
    st.markdown('<div class="about-section">', unsafe_allow_html=True)
    a_left, a_right = st.columns([1, 1.2])
    with a_left:
        st.markdown(
            """
            <div class="about-mini-title">WHO WE ARE</div>
            <div class="about-header">ABOUT<br>BANDHAN</div>
            <p class="about-text">
                Bandhan builds world-class financial infrastructure and the 
                intelligent technology to manage it. From local schemes to 
                professional scouting, we bridge the gap between raw data 
                and real opportunity.
            </p>
            <br>
            """, unsafe_allow_html=True
        )
    with a_right:
        st.markdown(
            """
            <div class="staggered-grid">
                <div class="staggered-item" style="background: linear-gradient(135deg, #2C1E16 0%, #442E22 100%); color: #FFFFFF; margin-top: 20px; box-shadow: 0 10px 30px rgba(44,30,22,0.15);">
                    Intelligent Technology.
                </div>
                <div class="staggered-item" style="background: #FFFFFF; border: 1px solid #E8E1D5; color: #2C1E16; box-shadow: 0 6px 20px rgba(44,30,22,0.04);">
                    Real Opportunity.
                </div>
                <div class="staggered-item" style="background: #FFFFFF; border: 1px solid #E8E1D5; color: #2C1E16; margin-top: 20px; box-shadow: 0 6px 20px rgba(44,30,22,0.04);">
                    Graph Neural Networks
                </div>
                <div class="staggered-item" style="background: linear-gradient(135deg, #6B3F23 0%, #8D5430 100%); color: #FFFFFF; box-shadow: 0 10px 30px rgba(107,63,35,0.2);">
                    Financial Inclusion.
                </div>
            </div>
            """, unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. Mission Row
    st.markdown('<div class="mission-row">', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            """
            <div class="mission-card">
                <div class="mission-number">01</div>
                <h3>The Mission</h3>
                <p>Bandhan is proud to present intelligent risk monitoring, a high-stakes solution that reflects our core commitment to fostering competitive lending and creating unforgettable experiences for banks of every size.</p>
            </div>
            """, unsafe_allow_html=True
        )
    with m2:
        st.markdown(
            """
            <div class="mission-card">
                <div class="mission-number">02</div>
                <h3>The Engine</h3>
                <p>This is your chance to come play, compete, and own the spotlight. Whether you are a seasoned analyst or a newcomer looking to test your mettle, Bandhan delivers professionally organized matches paired with exciting algorithms.</p>
            </div>
            """, unsafe_allow_html=True
        )
    with m3:
        st.markdown(
            """
            <div class="mission-card">
                <div class="mission-number">03</div>
                <h3>The Community</h3>
                <p>Join a community that rewards your talent and become part of something bigger — where passion for fair financial access meets opportunity, competition, and shared growth on and off the ledger.</p>
            </div>
            """, unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)



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


def render_otp_verification_page() -> None:
    """Renders a production-grade 2FA OTP verification screen."""
    if "temp_login_type" not in st.session_state:
        st.session_state.view = "landing"
        st.rerun()

    login_type = st.session_state.temp_login_type
    username = st.session_state.temp_login_user
    email = st.session_state.temp_login_email
    mobile = st.session_state.temp_login_mobile
    otp = st.session_state.temp_login_otp
    otp_time = st.session_state.temp_login_otp_time
    attempts = st.session_state.temp_login_otp_attempts
    locked = st.session_state.temp_login_otp_locked
    sent_time = st.session_state.temp_login_otp_sent_time

    # Calculate countdown
    import time
    time_elapsed = int(time.time() - otp_time)
    time_remaining = max(0, 300 - time_elapsed) # 5 minutes validity
    
    resend_cooldown = max(0, 30 - int(time.time() - sent_time))

    st.markdown(
        """
        <style>
        .otp-shell {
            background: #FFFFFF !important;
            border-radius: 16px !important;
            padding: 36px 40px !important;
            border: 1px solid #E8E1D5 !important;
            box-shadow: 0 4px 20px rgba(44, 30, 22, 0.06) !important;
            max-width: 480px;
            margin: 60px auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="otp-shell">', unsafe_allow_html=True)
    
    st.markdown(
        f"""
        <div style="text-align: center; margin-bottom: 24px;">
            <div style="
                width: 40px; height: 40px; border-radius: 10px; background: rgba(212, 163, 115, 0.2);
                border: 1px solid rgba(212, 163, 115, 0.4); color: #6B3F23; font-size: 1.25rem;
                display: flex; align-items: center; justify-content: center; margin: 0 auto 14px auto;
            ">🛡️</div>
            <span style="font-size: 0.75rem; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #8C7E72; display: block; margin-bottom: 6px;">TWO-FACTOR AUTHENTICATION</span>
            <h3 style="font-size: 2rem; font-weight: 800; letter-spacing: -0.8px; color: #2C1E16; margin-bottom: 6px; line-height: 1.15;">Verify OTP</h3>
            <p style="font-size: 0.88rem; color: #6E5F52; margin-bottom: 0; line-height: 1.5;">
                Enter the secure 6-digit code sent to your registered device.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Simulated visual container
    st.info(
        f"🔑 **2FA Verification Code**:\n"
        f"- OTP Code: `{otp}`\n"
        f"- Registered Email: `{email}`\n"
        f"- Registered Mobile: `{mobile}`"
    )

    # Verification state warnings
    if locked or attempts >= 3:
        st.error("❌ Access Denied: OTP is locked due to 3 failed attempts. Please generate a new OTP by clicking Resend.")
    elif time_remaining <= 0:
        st.error("⏳ OTP Expired: The code is no longer valid. Please generate a new code.")
    else:
        # Show timer remaining
        mins = time_remaining // 60
        secs = time_remaining % 60
        st.markdown(
            f"""
            <div style="text-align:center; margin-bottom:16px;">
                <span style="font-weight:700; color:#6B3F23; font-size:1.05rem;">⏳ {mins}m {secs:02d}s remaining</span>
            </div>
            """, unsafe_allow_html=True
        )

    entered_otp = st.text_input("Enter OTP Code", max_chars=6, key="otp_entered_val", placeholder="123456")

    col_verify, col_resend = st.columns(2)
    
    with col_verify:
        verify_enabled = not locked and attempts < 3 and time_remaining > 0
        verify_btn = st.button("Verify OTP", type="primary", use_container_width=True, disabled=not verify_enabled)

    with col_resend:
        resend_label = "Resend OTP" if resend_cooldown == 0 else f"Resend ({resend_cooldown}s)"
        resend_btn = st.button(resend_label, use_container_width=True, disabled=resend_cooldown > 0)

    st.markdown("<div style='margin-bottom: 20px'></div>", unsafe_allow_html=True)
    if st.button("← Cancel & Back to Sign In", key="otp_back_btn", use_container_width=True):
        st.session_state.view = f"{login_type}_login"
        st.session_state.pop("temp_login_type", None)
        st.session_state.pop("temp_login_user", None)
        st.session_state.pop("temp_login_email", None)
        st.session_state.pop("temp_login_mobile", None)
        st.session_state.pop("temp_login_otp", None)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # Verification Logic
    if verify_btn and entered_otp:
        with st.spinner("Checking verification codes..."):
            time.sleep(0.6)
            
            if entered_otp == otp:
                st.success("✅ Code verified successfully. Authorizing...")
                time.sleep(0.4)
                
                if login_type == "admin":
                    ip, device = get_client_info()
                    log_admin_login_attempt(username, ip, device, "SUCCESS")
                    
                    st.session_state.admin_authenticated = True
                    st.session_state.admin_username = username
                    st.session_state.view = "admin"
                    
                    audit_log("Authentication", "OTP Verified", reason="2FA one-time password successfully verified")
                    audit_log("Authentication", "Admin Login", reason="Admin successfully logged in and authenticated via 2FA")
                else:
                    st.session_state.borrower_authenticated = True
                    st.session_state.borrower_id = username
                    st.session_state.view = "borrower"
                    
                    audit_log("Authentication", "OTP Verified", borrower_id=username, reason="2FA one-time password successfully verified")
                    audit_log("Authentication", "Borrower Login", borrower_id=username, reason="Borrower successfully logged in and authenticated via 2FA")
                    
                # Clear session logins
                st.session_state.pop("temp_login_type", None)
                st.session_state.pop("temp_login_user", None)
                st.session_state.pop("temp_login_email", None)
                st.session_state.pop("temp_login_mobile", None)
                st.session_state.pop("temp_login_otp", None)
                st.rerun()
            else:
                st.session_state.temp_login_otp_attempts += 1
                curr_attempts = st.session_state.temp_login_otp_attempts
                
                # Log failed verification attempt
                audit_log("Authentication", "Failed Login Attempt", borrower_id=(username if login_type == "borrower" else "N/A"), reason=f"Incorrect OTP entered: verification attempt {curr_attempts}/3 failed")

                if curr_attempts >= 3:
                    st.session_state.temp_login_otp_locked = True
                    if login_type == "admin":
                        ip, device = get_client_info()
                        log_admin_login_attempt(username, ip, device, "FAILED")
                    st.error("❌ Access Locked: Maximum verification attempts reached.")
                else:
                    st.error(f"❌ Invalid verification code. {3 - curr_attempts} attempt(s) remaining.")
                st.rerun()

    # Resend Logic
    if resend_btn:
        with st.spinner("Re-generating verification tokens..."):
            new_otp = generate_otp()
            st.session_state.temp_login_otp = new_otp
            st.session_state.temp_login_otp_time = time.time()
            st.session_state.temp_login_otp_attempts = 0
            st.session_state.temp_login_otp_locked = False
            st.session_state.temp_login_otp_sent_time = time.time()
            
            send_otp_email(email, new_otp)
            send_otp_sms(mobile, new_otp)
            
            audit_log("Authentication", "OTP Generated", borrower_id=(username if login_type == "borrower" else "N/A"), reason=f"Resend code requested by user, sent to registered contact details")

            st.success("✅ A new verification code was sent to your registered endpoints.")
            time.sleep(0.4)
            st.rerun()


def render_admin_security_section() -> None:
    """Renders the admin security history log dashboard section."""
    admin_name = st.session_state.get("admin_username", "Admin")
    
    st.markdown(
        """
        <div style="background: rgba(255,255,255,0.5);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.8);
            border-radius: 24px;
            padding: 24px 28px;
            margin-bottom: 24px;">
            <h3 style="margin:0 0 8px 0; color:#1c1c1e;">
                🛡️ Admin Security Portal
            </h3>
            <p style="margin:0; color:#48484a;">
                Audit access timestamps, active session details, and track consecutive failed access attempt counters.
            </p>
        </div>
        """, unsafe_allow_html=True
    )

    metrics = get_admin_security_metrics(admin_name)
    ip, device = get_client_info()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.6); border: 1px solid rgba(0,0,0,0.08); border-radius: 16px; padding: 20px; min-height: 140px;">
                <span style="font-size:0.75rem; text-transform:uppercase; color:#636366; font-weight:700; letter-spacing:1px;">Active Session IP</span>
                <div style="font-size: 1.5rem; font-weight: 800; color: #1c1c1e; margin-top: 8px;">{ip}</div>
                <p style="margin: 8px 0 0 0; font-size: 0.8rem; color: #636366;">Verified by 2FA login</p>
            </div>
            """, unsafe_allow_html=True
        )
        
    with col2:
        failed_count = metrics["failed_login_count"]
        color = "#ef4444" if failed_count > 0 else "#22c55e"
        status_txt = "Alert: Watchlist" if failed_count > 0 else "Secured"
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.6); border: 1px solid rgba(0,0,0,0.08); border-radius: 16px; padding: 20px; min-height: 140px;">
                <span style="font-size:0.75rem; text-transform:uppercase; color:#636366; font-weight:700; letter-spacing:1px;">Failed Login Counter</span>
                <div style="font-size: 1.5rem; font-weight: 800; color: {color}; margin-top: 8px;">{failed_count} Attempts</div>
                <p style="margin: 8px 0 0 0; font-size: 0.8rem; color: {color}; font-weight: 600;">{status_txt}</p>
            </div>
            """, unsafe_allow_html=True
        )
        
    with col3:
        st.markdown(
            f"""
            <div style="background: rgba(255,255,255,0.6); border: 1px solid rgba(0,0,0,0.08); border-radius: 16px; padding: 20px; min-height: 140px;">
                <span style="font-size:0.75rem; text-transform:uppercase; color:#636366; font-weight:700; letter-spacing:1px;">Last Successful Login</span>
                <div style="font-size: 1.15rem; font-weight: 700; color: #1c1c1e; margin-top: 12px; line-height: 1.3;">{metrics["last_successful_login"]}</div>
                <p style="margin: 6px 0 0 0; font-size: 0.8rem; color: #636366; text-overflow:ellipsis; overflow:hidden; white-space:nowrap;" title="{metrics['last_successful_device']}">Device: {metrics['last_successful_device']}</p>
            </div>
            """, unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📱 Current Connection Device Details")
    st.info(f"💻 **User-Agent Header**: {device}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 🕒 Audit History Logs")
    
    logs = metrics["logs"]
    if not logs:
        st.info("No login attempts logged for this account.")
    else:
        logs_df = pd.DataFrame(logs)
        logs_display = logs_df[[
            "timestamp", "ip_address", "device_info", "status"
        ]].rename(columns={
            "timestamp": "Timestamp",
            "ip_address": "IP Address",
            "device_info": "Device / User-Agent",
            "status": "Status"
        })
        render_glass_table(logs_display, max_height=350)


def render_login_page(mode: str = "admin") -> None:

    is_admin = mode == "admin"
    badge_label = "Admin portal" if is_admin else "Borrower portal"
    heading = "Manage your<br>portfolio." if is_admin else "Manage your<br>loans."
    subtext = (
        "Intelligent borrower monitoring, regional stress analysis, and contextual recovery intelligence."
        if is_admin
        else "View your repayment schedule, health score, and personalised recovery guidance."
    )
    eyebrow = "Admin access" if is_admin else "Borrower access"
    subtitle = (
        "Sign in to access the Bandhan dashboard."
        if is_admin
        else "Sign in with your Borrower ID to continue."
    )
    id_label = "Username" if is_admin else "Borrower ID"
    id_placeholder = "Enter admin username" if is_admin else "e.g. B00042"
    back_key = "admin_back" if is_admin else "borrower_back"
    form_key = "admin_login_form" if is_admin else "borrower_login_form"

    import base64
    import textwrap
    bg_img_data = ""
    try:
        with open("signin_optimized.jpg", "rb") as f:
            bg_img_data = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
    except Exception:
        pass

    st.markdown(
        """
        <style>
        div[data-testid="stForm"] {
            background: #FFFFFF !important;
            border-radius: 16px !important;
            padding: 36px 40px !important;
            border: 1px solid #E8E1D5 !important;
            box-shadow: 0 4px 20px rgba(44, 30, 22, 0.06) !important;
            margin-top: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.15, 1])

    with left_col:
        bg_style = f"background: linear-gradient(180deg, rgba(44, 30, 22, 0.88) 0%, rgba(30, 20, 14, 0.95) 100%), url('{bg_img_data}') center/cover no-repeat;" if bg_img_data else "background: #2C1E16;"
        left_hero_html = f"""<div style="{bg_style} border-radius: 20px; padding: 44px 40px; min-height: 600px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 16px 40px rgba(44,30,22,0.18); color: #FFFFFF; border: 1px solid #3E2B20;">
<div>
<div style="display: flex; align-items: center; gap: 14px; margin-bottom: 40px;">
<div style="width: 38px; height: 38px; background: rgba(212, 163, 115, 0.18); border: 1px solid rgba(212, 163, 115, 0.45); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.25rem; color: #D4A373;">B</div>
<div>
<div style="font-size: 0.95rem; font-weight: 800; letter-spacing: 1.5px; color: #FFFFFF; line-height: 1.1;">BANDHAN</div>
<div style="font-size: 0.68rem; font-weight: 600; letter-spacing: 1px; color: #B4A496; text-transform: uppercase;">LOAN MANAGEMENT · {escape(badge_label)}</div>
</div>
</div>
<h1 style="font-size: 2.85rem; font-weight: 800; line-height: 1.15; letter-spacing: -1px; color: #FFFFFF; margin: 0 0 16px 0;">Stronger<br>Recoveries.<br><span style="color: #D4A373;">Brighter Tomorrows.</span></h1>
<p style="font-size: 0.95rem; color: #C8BCB0; line-height: 1.6; max-width: 420px; margin-bottom: 36px;">A unified platform for smarter loan recovery management, powered by data and trust.</p>
<div style="display: flex; flex-direction: column; gap: 14px;">
<div style="display: flex; align-items: center; gap: 14px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px 16px;">
<div style="width: 34px; height: 34px; border-radius: 8px; background: rgba(212, 163, 115, 0.2); display: flex; align-items: center; justify-content: center; font-size: 1.1rem;">📊</div>
<div>
<div style="font-size: 0.9rem; font-weight: 700; color: #FFFFFF;">Data-Driven Insights</div>
<div style="font-size: 0.78rem; color: #A8988B;">Track performance and identify risks</div>
</div>
</div>
<div style="display: flex; align-items: center; gap: 14px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px 16px;">
<div style="width: 34px; height: 34px; border-radius: 8px; background: rgba(212, 163, 115, 0.2); display: flex; align-items: center; justify-content: center; font-size: 1.1rem;">👥</div>
<div>
<div style="font-size: 0.9rem; font-weight: 700; color: #FFFFFF;">Efficient Workflows</div>
<div style="font-size: 0.78rem; color: #A8988B;">Streamline recovery processes</div>
</div>
</div>
<div style="display: flex; align-items: center; gap: 14px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px 16px;">
<div style="width: 34px; height: 34px; border-radius: 8px; background: rgba(212, 163, 115, 0.2); display: flex; align-items: center; justify-content: center; font-size: 1.1rem;">🛡️</div>
<div>
<div style="font-size: 0.9rem; font-weight: 700; color: #FFFFFF;">Greater Financial Inclusion</div>
<div style="font-size: 0.78rem; color: #A8988B;">Support borrowers, build stronger communities</div>
</div>
</div>
</div>
</div>
<div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.12); padding-top: 24px; margin-top: 40px;">
<div style="font-size: 0.78rem; color: #A8988B; font-weight: 600; letter-spacing: 0.5px;">People &nbsp;|&nbsp; Process &nbsp;|&nbsp; Progress</div>
<div style="font-size: 0.78rem; color: #D4A373; font-style: italic;">&ldquo;Responsible lending. Sustainable futures.&rdquo;</div>
</div>
</div>"""
        if hasattr(st, "html"):
            st.html(left_hero_html)
        else:
            st.markdown(left_hero_html, unsafe_allow_html=True)

    with right_col:
        st.markdown(
            """
            <div style="display: flex; justify-content: flex-end; margin-bottom: 12px;">
                <span style="font-size: 0.82rem; color: #8C7E72; font-weight: 500;">Need help? ❓</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form(form_key, border=False):
            st.markdown(
                f"""
                <div style="margin-bottom: 24px;">
                    <div style="font-size: 0.75rem; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; color: #8C7E72; margin-bottom: 8px;">
                        WELCOME TO BANDHAN · {escape(eyebrow)}
                    </div>
                    <h2 style="font-size: 2.1rem; font-weight: 800; letter-spacing: -0.8px; color: #2C1E16; margin: 0 0 6px 0; line-height: 1.15;">
                        Sign in to your account
                    </h2>
                    <p style="font-size: 0.9rem; color: #6E5F52; margin: 0; line-height: 1.5;">
                        {escape(subtitle)}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(f"<p style='font-size:0.85rem;font-weight:600;color:#2C1E16;margin-bottom:6px;'>{id_label}</p>", unsafe_allow_html=True)
            identifier = st.text_input("", placeholder=id_placeholder, label_visibility="collapsed")

            st.markdown("<p style='font-size:0.85rem;font-weight:600;color:#2C1E16;margin-bottom:6px;'>Password</p>", unsafe_allow_html=True)
            password = st.text_input("", type="password", placeholder="Enter your password", label_visibility="collapsed")
            
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Sign In →", use_container_width=True, type="primary")

            st.markdown(
                """
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 18px; font-size: 0.85rem;">
                    <span style="color: #6B3F23; font-weight: 600; text-decoration: underline; cursor: pointer;">Demo accounts active</span>
                    <span style="color: #6B3F23; font-weight: 600; cursor: pointer;">Forgot password?</span>
                </div>
                <div style="height: 1px; background: #E8E1D5; margin: 24px 0 16px 0;"></div>
                <div style="text-align: center; font-size: 0.75rem; color: #8C7E72; letter-spacing: 0.4px;">
                    Secure Access &nbsp;|&nbsp; Trusted Operations &nbsp;|&nbsp; Stronger Communities
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button("← Back to website", key=back_key):
            st.session_state.view = "landing"
            st.rerun()

    if submitted:
        if is_admin:
            username = identifier
            # Check if admin logged in using email address
            if "@" in identifier:
                for u, e in ADMIN_EMAILS.items():
                    if e.lower() == identifier.lower():
                        username = u
                        break

            if ADMIN_CREDENTIALS.get(username) == password:
                # Success Step 2: Proceed to OTP Generation
                otp = generate_otp()
                email = ADMIN_EMAILS.get(username, f"{username}@bandhanbank.co.in")
                mobile = ADMIN_MOBILES.get(username, "+91 9999900000")
                
                import time
                st.session_state.temp_login_type = "admin"
                st.session_state.temp_login_user = username
                st.session_state.temp_login_email = email
                st.session_state.temp_login_mobile = mobile
                st.session_state.temp_login_otp = otp
                st.session_state.temp_login_otp_time = time.time()
                st.session_state.temp_login_otp_attempts = 0
                st.session_state.temp_login_otp_locked = False
                st.session_state.temp_login_otp_sent_time = time.time()

                send_otp_email(email, otp)
                send_otp_sms(mobile, otp)
                
                # Compliance audit log
                audit_log("Authentication", "OTP Generated", reason=f"Password verified. OTP code sent to registered contact details ({email} / {mobile})")

                st.session_state.view = "otp_verification"
                st.rerun()
            else:
                ip, device = get_client_info()
                log_admin_login_attempt(username, ip, device, "FAILED")
                audit_log("Authentication", "Failed Login Attempt", reason=f"Password verification failed for admin username '{username}'")
                st.error("Invalid admin credentials.")
        else:
            # Borrower credentials validation
            borrower_row = None
            if "@" in identifier:
                # Find matching email
                matching = borrowers_df[borrowers_df["email"].str.lower() == identifier.lower()]
                if not matching.empty:
                    borrower_row = matching.iloc[0]
            else:
                # Find matching borrower_id
                matching = borrowers_df[borrowers_df["borrower_id"] == identifier]
                if not matching.empty:
                    borrower_row = matching.iloc[0]

            if borrower_row is not None and password == borrower_row["borrower_id"]:
                borrower_id = borrower_row["borrower_id"]
                email = borrower_row.get("email", f"{borrower_id.lower()}@example.com")
                mobile = borrower_row.get("mobile_number", "+91 9999900000")

                otp = generate_otp()
                
                import time
                st.session_state.temp_login_type = "borrower"
                st.session_state.temp_login_user = borrower_id
                st.session_state.temp_login_email = email
                st.session_state.temp_login_mobile = mobile
                st.session_state.temp_login_otp = otp
                st.session_state.temp_login_otp_time = time.time()
                st.session_state.temp_login_otp_attempts = 0
                st.session_state.temp_login_otp_locked = False
                st.session_state.temp_login_otp_sent_time = time.time()

                send_otp_email(email, otp)
                send_otp_sms(mobile, otp)
                
                # Compliance audit log
                audit_log("Authentication", "OTP Generated", borrower_id=borrower_id, reason=f"Borrower password verified. OTP code dispatched to {email} / {mobile}")

                st.session_state.view = "otp_verification"
                st.rerun()
            else:
                audit_log("Authentication", "Failed Login Attempt", reason=f"Password verification failed for borrower identifier '{identifier}'")
                st.error("Invalid borrower ID, email, or password.")


def render_admin_login() -> None:
    render_login_page("admin")


def render_borrower_login() -> None:
    render_login_page("borrower")


if "view" not in st.session_state:
    st.session_state.view = "landing"

# Route Guarding: Protect dashboard views from unauthenticated access
if st.session_state.view == "admin":
    if st.session_state.get("admin_authenticated"):
        render_admin_dashboard()
        st.stop()
    else:
        st.session_state.view = "admin_login"
        st.rerun()

elif st.session_state.view == "borrower":
    if st.session_state.get("borrower_authenticated"):
        render_borrower_dashboard(st.session_state["borrower_id"])
        st.stop()
    else:
        st.session_state.view = "borrower_login"
        st.rerun()

elif st.session_state.view == "otp_verification":
    render_otp_verification_page()
    st.stop()

elif st.session_state.view == "admin_login":
    if st.session_state.get("admin_authenticated"):
        st.session_state.view = "admin"
        st.rerun()
    render_admin_login()
    st.stop()

elif st.session_state.view == "borrower_login":
    if st.session_state.get("borrower_authenticated"):
        st.session_state.view = "borrower"
        st.rerun()
    render_borrower_login()
    st.stop()

else:
    render_landing_page()
    st.stop()