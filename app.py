import base64
import hashlib
import json
import os
import sqlite3
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st
from dotenv import load_dotenv

def get_base64_of_bin_file(bin_file):
    if not os.path.exists(bin_file): return ""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

from Utils.Agents import (
    Cardiologist,
    Endocrinologist,
    Immunologist,
    MultidisciplinaryTeam,
    Neurologist,
    Psychologist,
    Pulmonologist,
)

load_dotenv(dotenv_path="apikey.env")

st.set_page_config(
    page_title="PulseLens AI | Clinical Intelligence",
    page_icon="🏥",
    layout="wide",
)

# --- Constants & Paths ---

USERS_DIR = "data"
DB_PATH = os.path.join(USERS_DIR, "mediagent.db")

AGENT_CLASSES = {
    "Cardiologist": Cardiologist,
    "Psychologist": Psychologist,
    "Pulmonologist": Pulmonologist,
    "Neurologist": Neurologist,
    "Endocrinologist": Endocrinologist,
    "Immunologist": Immunologist,
}

AGENT_ICONS = {
    "Cardiologist": "❤️",
    "Psychologist": "🧠",
    "Pulmonologist": "🫁",
    "Neurologist": "⚡",
    "Endocrinologist": "🔬",
    "Immunologist": "🛡️",
}

URGENCY_COLORS = {
    "low": "urgency-low",
    "moderate": "urgency-moderate",
    "high": "urgency-high",
    "critical": "urgency-critical",
    "unknown": "urgency-unknown",
}

SPECIALIST_KEYWORDS = {
    "Cardiologist": [
        "chest pain",
        "palpit",
        "arrhythm",
        "ecg",
        "heart",
        "cardiac",
        "blood pressure",
        "hypertension",
    ],
    "Psychologist": [
        "anxiety",
        "panic",
        "stress",
        "insomnia",
        "depression",
        "mood",
        "trauma",
        "behavior",
    ],
    "Pulmonologist": [
        "cough",
        "shortness of breath",
        "breath",
        "asthma",
        "copd",
        "wheez",
        "respiratory",
        "lung",
    ],
    "Neurologist": [
        "headache",
        "migraine",
        "seizure",
        "memory",
        "neuropathy",
        "dizziness",
        "tremor",
        "neurolog",
    ],
    "Endocrinologist": [
        "diabetes",
        "thyroid",
        "hormone",
        "pcos",
        "metabolic",
        "insulin",
        "glucose",
        "endocrine",
    ],
    "Immunologist": [
        "autoimmune",
        "allergy",
        "inflammation",
        "rash",
        "arthritis",
        "lupus",
        "immune",
        "swelling",
    ],
}


# --- Styling ---

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600;700&display=swap');

:root {
    --bg: #0a0b10;
    --bg-deep: #050608;
    --surface: rgba(25, 27, 38, 0.6);
    --surface-strong: rgba(30, 32, 45, 0.9);
    --line: rgba(255, 255, 255, 0.1);
    --line-strong: rgba(255, 255, 255, 0.2);
    --text-main: #f1f5f9;
    --text-soft: #94a3b8;
    --accent: #38bdf8;
    --accent-2: #818cf8;
    --accent-deep: #0ea5e9;
    --glow: rgba(56, 189, 248, 0.24);
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: var(--text-main);
}

.stApp {
    background:
        radial-gradient(950px 440px at -8% -10%, rgba(56, 189, 248, 0.12) 0%, transparent 60%),
        radial-gradient(800px 380px at 108% -2%, rgba(129, 140, 248, 0.12) 0%, transparent 58%),
        repeating-linear-gradient(
            90deg,
            rgba(255, 255, 255, 0.02) 0,
            rgba(255, 255, 255, 0.02) 1px,
            transparent 1px,
            transparent 56px
        ),
        linear-gradient(180deg, var(--bg) 0%, var(--bg-deep) 100%);
}

.block-container {
    max-width: 100%;
    padding: 1.2rem 2.4rem 2.5rem 2.4rem;
}

.stApp,
.stApp p,
.stApp label,
.stApp span,
.stApp li,
.stApp div,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stCaptionContainer"] {
    color: var(--text-main) !important;
}

.main-title {
    font-family: 'DM Serif Display', serif;
    font-size: 3.2rem;
    color: #ffffff;
    margin-bottom: 0;
    line-height: 1.03;
    letter-spacing: 0.012em;
    text-shadow: 0 8px 25px rgba(56, 189, 248, 0.2);
    margin-top: 1.5rem;
}

@supports (-webkit-background-clip: text) {
    .main-title {
        color: transparent;
        background: linear-gradient(90deg, #ffffff 0%, #bae6fd 44%, #7dd3fc 100%);
        -webkit-background-clip: text;
        background-clip: text;
    }
}

.main-subtitle {
    font-size: 1.03rem;
    color: var(--text-soft) !important;
    margin-top: 0.15rem;
    margin-bottom: 1.8rem;
    font-weight: 500;
}

.section-label {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.73rem;
    font-weight: 800;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: var(--text-soft) !important;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: 0.33rem 0.72rem;
    margin-bottom: 0.55rem;
}

.auth-shell {
    min-height: calc(100vh - 72px);
    margin-top: 0.02rem;
    display: flex;
    align-items: stretch;
}

.auth-hero {
    min-height: 75vh;
    background: #191b26;
    background: linear-gradient(145deg, #1b1d28 0%, #15161f 100%);
    border-radius: 0;
    padding: 1.5rem 2rem;
    box-shadow: none;
    color: #ffffff !important;
    position: relative;
    overflow: hidden;
    height: 100%;
}

.docbook-brand {
    font-size: 2rem;
    font-weight: 500;
    letter-spacing: -0.02em;
    color: #ffffff;
    margin-bottom: 2rem;
    position: relative;
    z-index: 10;
}

.docbook-brand sup {
    font-size: 0.6em;
    top: -0.5em;
    font-weight: 400;
}

.bg-clipboard {
    position: absolute;
    left: -15%;
    bottom: -25%;
    width: 65%;
    opacity: 0.85;
    transform: rotate(-10deg);
    z-index: 1;
}

.avatar-card {
    position: absolute;
    display: flex;
    flex-direction: column;
    align-items: center;
    z-index: 5;
    animation: float 6s ease-in-out infinite;
}

@keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-12px); }
    100% { transform: translateY(0px); }
}

.avatar-card img {
    width: 90px;
    height: 90px;
    border-radius: 50%;
    object-fit: cover;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4);
    margin-bottom: -30px;
    z-index: 2;
    position: relative;
}

.avatar-info {
    background: rgba(38, 40, 48, 0.4);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    padding: 35px 20px 15px 20px;
    border-radius: 12px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.05);
    width: max-content;
    min-width: 170px;
}

.avatar-info strong {
    display: block;
    font-size: 1.3rem;
    font-weight: 400;
    color: #ffffff;
    margin-bottom: 4px;
}

.avatar-info span {
    font-size: 0.85rem;
    color: rgba(255,255,255,0.4);
}

.avatar-urologist {
    top: 25%;
    left: 15%;
    animation-delay: 0s;
}

.avatar-ophthalmologist {
    top: 15%;
    right: 15%;
    animation-delay: -2s;
}

.avatar-psychiatrist {
    bottom: 12%;
    right: 25%;
    animation-delay: -4s;
}

.heart-icon {
    position: absolute;
    top: 0px;
    right: 20px;
    background: rgba(30, 31, 41, 0.6);
    backdrop-filter: blur(8px);
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    font-size: 14px;
    z-index: 10;
    border: 1px solid rgba(255,255,255,0.1);
}

.auth-panel {
    min-height: 75vh;
    background: #ffffff;
    border: none;
    border-radius: 0;
    padding: 1rem 3rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.auth-panel-top {
    margin-bottom: 2rem;
}

.auth-tabs-note {
    margin: 1.5rem 0 2rem 0;
    font-size: 1rem;
    color: #121212;
}

.auth-tabs-note a {
    color: #4b9bdf;
    text-decoration: none;
}

.auth-panel-title {
    margin: 0;
    color: #121213;
    font-size: 2.2rem;
    font-weight: 500;
    margin-bottom: 2.5rem;
}

.auth-panel-subtitle {
    display: none;
}

.auth-login-divider {
    display: none;
}

.auth-social-label {
    font-size: 1.1rem;
    color: #121213;
    margin-bottom: 0.5rem;
    font-weight: 500;
}

.auth-social-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.8rem;
    margin-bottom: 1.1rem;
}

.social-card {
    background: #23222a;
    color: #ffffff;
    border-radius: 12px;
    padding: 0.9rem;
    text-align: center;
    font-size: 1.1rem;
    font-weight: 400;
    box-shadow: none;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.social-card.light {
    background: #23222a;
}

.support-label {
    font-size: 1rem;
    color: #121213;
    margin-top: 3rem;
    margin-bottom: 0.8rem;
}

.support-pill {
    background: #f8f8f9;
    border: none;
    border-radius: 12px;
    padding: 0.85rem 0.9rem;
    text-align: center;
    color: #121213;
    font-size: 1.1rem;
}

.glass-panel {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 1.15rem 1.2rem;
    box-shadow: 0 20px 34px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}

.option-card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.95rem 1rem;
    min-height: 160px;
    box-shadow: 0 12px 26px rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}

.option-title {
    font-size: 1.06rem;
    font-weight: 700;
    color: var(--text-main);
    margin-bottom: 0.35rem;
}

.option-copy {
    color: var(--text-soft);
    font-size: 0.92rem;
    line-height: 1.5;
}

.history-meta {
    font-size: 0.85rem;
    color: #4f7490;
}

.agent-badge {
    display: inline-block;
    padding: 0.28rem 0.78rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 0.3rem;
    margin-bottom: 0.3rem;
    border: 1px solid transparent;
    box-shadow: 0 5px 14px rgba(40, 126, 176, 0.12);
}

.urgency-low { background: #e6faef; color: #1f7a45; border-color: #b8e8cb; }
.urgency-moderate { background: #fff8df; color: #8a6b12; border-color: #f2e1a1; }
.urgency-high { background: #ffeceb; color: #9c2f2f; border-color: #f4b8b5; }
.urgency-critical { background: #c52929; color: #fff4f4; border-color: #a41f1f; }
.urgency-unknown { background: #edf5fa; color: #4a6a82; border-color: #d2e3ef; }

.diagnosis-card {
    background: linear-gradient(155deg, rgba(255, 255, 255, 0.96) 0%, rgba(245, 251, 255, 0.96) 100%);
    border: 1px solid #c9e2f4;
    border-left: 5px solid var(--accent);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 16px 28px rgba(22, 100, 145, 0.09), inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.diagnosis-number {
    font-family: 'DM Serif Display', serif;
    font-size: 1.9rem;
    color: var(--accent-deep);
    line-height: 1;
}

.diagnosis-title {
    font-weight: 600;
    font-size: 1.06rem;
    color: var(--text-main);
}

.step-item {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.56rem 0;
    border-bottom: 1px dashed #d2e6f5;
    font-size: 0.9rem;
    color: #315e7e;
}

.pubmed-ref {
    font-size: 0.8rem;
    color: var(--accent-deep);
    background: linear-gradient(180deg, #eaf7ff 0%, #dff3ff 100%);
    border: 1px solid #bddff5;
    border-radius: 8px;
    padding: 0.34rem 0.66rem;
    margin-bottom: 0.35rem;
}

.suggestion-card {
    background: linear-gradient(145deg, #f8fdff 0%, #eaf7ff 100%);
    border: 1px solid #b8daf0;
    border-radius: 12px;
    padding: 0.85rem 0.95rem;
    margin: 0.35rem 0 0.85rem 0;
    box-shadow: 0 8px 18px rgba(28, 110, 160, 0.1);
}

.suggestion-title {
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #2f6285;
    margin-bottom: 0.28rem;
}

.suggestion-list {
    font-size: 0.9rem;
    color: #1f5578;
    line-height: 1.45;
}

[data-testid="stFormSubmitButton"] {
    display: none !important;
}

div[data-testid="stExpander"] {
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(247, 252, 255, 0.92) 100%);
    border: 1px solid #c9e2f2;
    border-radius: 12px;
    margin-bottom: 0.62rem;
    box-shadow: 0 8px 22px rgba(27, 115, 164, 0.08);
}

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
div[data-testid="stFileUploader"] section {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 12px !important;
    color: #f1f5f9 !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.1) !important;
    font-size: 1.1rem !important;
}

div[data-testid="stForm"] {
    background: transparent;
    padding: 0;
    margin: 0;
    border: none;
}

div[data-testid="stForm"] > div {
    gap: 1.5rem;
}

div[data-testid="stTextInput"] input:focus,
div[data-testid="stTextArea"] textarea:focus {
    border: none !important;
    box-shadow: 0 0 0 1px #d4d4d8 !important;
}

[data-testid="stTextInput"] label,
[data-testid="stTextArea"] label,
[data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label,
[data-testid="stRadio"] label,
[data-testid="stCheckbox"] label {
    color: #121213 !important;
    font-weight: 500 !important;
}

[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: #b0b0b0 !important;
    opacity: 1 !important;
}

@media (max-width: 920px) {
    .block-container {
        padding: 1rem 1rem 2rem 1rem;
    }

    .main-title {
        font-size: 2.4rem;
    }

    .auth-headline {
        font-size: 1.7rem;
    }

    .auth-hero,
    .auth-panel {
        border-radius: 18px;
        min-height: unset;
        padding: 1.2rem;
    }

    .auth-copy {
        max-width: none;
    }

    .auth-social-row,
    .hero-card-row {
        grid-template-columns: 1fr;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


# --- Data Layer ---


def ensure_storage() -> None:
    os.makedirs(USERS_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checkups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                patient_name TEXT,
                selected_agents_json TEXT NOT NULL,
                input_report TEXT NOT NULL,
                result_json TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.commit()


def get_user_row(username: str):
    ensure_storage()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
            (username.strip().lower(),),
        ).fetchone()
    return row


def get_user_id(username: str):
    row = get_user_row(username)
    return row["id"] if row else None


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(username: str, password: str) -> tuple[bool, str]:
    username = username.strip().lower()

    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if get_user_row(username):
        return False, "Username already exists."

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username, hash_password(password), datetime.utcnow().isoformat()),
        )
        conn.commit()
    return True, "Account created successfully."


def authenticate_user(username: str, password: str) -> bool:
    username = username.strip().lower()
    row = get_user_row(username)
    if not row:
        return False
    return row["password_hash"] == hash_password(password)


def load_user_checkups(username: str) -> list:
    user_id = get_user_id(username)
    if user_id is None:
        return []

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT created_at, patient_name, selected_agents_json, input_report, result_json
            FROM checkups
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            """,
            (user_id,),
        ).fetchall()

    checkups = []
    for row in rows:
        try:
            selected_agents = json.loads(row["selected_agents_json"])
        except (json.JSONDecodeError, TypeError):
            selected_agents = []

        try:
            result = json.loads(row["result_json"])
        except (json.JSONDecodeError, TypeError):
            result = {}

        checkups.append(
            {
                "created_at": row["created_at"],
                "patient_name": row["patient_name"] or "Unknown",
                "selected_agents": selected_agents,
                "input_report": row["input_report"] or "",
                "result": result,
            }
        )
    return checkups


def save_user_checkup(username: str, record: dict) -> None:
    user_id = get_user_id(username)
    if user_id is None:
        return

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO checkups (user_id, created_at, patient_name, selected_agents_json, input_report, result_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                record.get("created_at", datetime.utcnow().isoformat()),
                record.get("patient_name", "Unknown"),
                json.dumps(record.get("selected_agents", [])),
                record.get("input_report", ""),
                json.dumps(record.get("result", {})),
            ),
        )
        conn.commit()


# --- App State ---


def init_session_state() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "app_view" not in st.session_state:
        st.session_state.app_view = "dashboard"
    if "agent_selections_initialized" not in st.session_state:
        for name in AGENT_ICONS:
            st.session_state[f"agent_{name}"] = True
        st.session_state.agent_selections_initialized = True


# --- Diagnostic Helpers ---


def suggest_specialists(report_text: str) -> tuple[list, dict]:
    text = (report_text or "").lower()
    if not text.strip():
        return [], {}

    scores = {name: 0 for name in SPECIALIST_KEYWORDS}
    matched_terms = {name: [] for name in SPECIALIST_KEYWORDS}

    for specialist, keywords in SPECIALIST_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                scores[specialist] += 1
                matched_terms[specialist].append(keyword)

    suggested = [name for name, score in scores.items() if score > 0]
    suggested.sort(key=lambda name: scores[name], reverse=True)

    if not suggested:
        suggested = ["Cardiologist", "Neurologist", "Endocrinologist"]

    suggested = suggested[:4]
    reasons = {name: sorted(set(matched_terms[name]))[:4] for name in suggested}
    return suggested, reasons


def render_header() -> None:
    st.markdown('<p class="main-title">PulseLens AI</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="main-subtitle">AI-Powered Multidisciplinary Medical Diagnostics</p>',
        unsafe_allow_html=True,
    )


# --- Auth UI ---


def render_auth_page() -> None:
    auth_mode = "Login"
    try:
        query_value = st.query_params.get("auth", "login")
        if isinstance(query_value, list):
            query_value = query_value[0]
        if str(query_value).lower() in {"signup", "sign-up", "register"}:
            auth_mode = "Sign Up"
    except Exception:
        query_value = st.experimental_get_query_params().get("auth", ["login"])
        if query_value and str(query_value[0]).lower() in {"signup", "sign-up", "register"}:
            auth_mode = "Sign Up"

    st.session_state.auth_mode = auth_mode


    left, right = st.columns([1.3, 1], gap="small")

    with left:
        urologist_b64 = get_base64_of_bin_file("assets/urologist.png")
        ophthalmologist_b64 = get_base64_of_bin_file("assets/ophthalmologist.png")
        psychiatrist_b64 = get_base64_of_bin_file("assets/psychiatrist.png")
        clipboard_b64 = get_base64_of_bin_file("assets/clipboard.png")

        st.markdown(
            f"""
<style>
.block-container {{
    max-width: 1000px !important;
    margin: 5vh auto !important;
    padding: 0 !important;
    background: rgba(22, 24, 33, 0.6) !important;
    backdrop-filter: blur(25px);
    -webkit-backdrop-filter: blur(25px);
    border-radius: 20px;
    box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1), 0 30px 60px rgba(0, 0, 0, 0.5);
    overflow: hidden !important;
}}
[data-testid="stHeader"] {{
    display: none !important;
}}
.auth-hero {{
    height: auto;
    min-height: 80vh;
    border-radius: 0;
    margin: 0;
    background: transparent !important;
}}
[data-testid="column"]:nth-of-type(2) {{
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 0 4rem !important;
    height: auto;
    min-height: 80vh;
    background: rgba(255, 255, 255, 0.96) !important;
}}
[data-testid="column"]:nth-of-type(1) {{
    padding: 0 !important;
}}
</style>
<div class="auth-hero">
<div class="docbook-brand">DocBook<sup>+</sup></div>

<img class="bg-clipboard" src="data:image/png;base64,{clipboard_b64}">

<div class="avatar-card avatar-urologist">
<img src="data:image/png;base64,{urologist_b64}">
<div class="avatar-info">
<strong>Urologist</strong>
<span>experience of 25 years</span>
</div>
</div>

<div class="avatar-card avatar-ophthalmologist">
<div class="heart-icon">🤍</div>
<img src="data:image/png;base64,{ophthalmologist_b64}">
<div class="avatar-info">
<strong>Ophthalmologist</strong>
<span>experience of 9 years</span>
</div>
</div>

<div class="avatar-card avatar-psychiatrist">
<img src="data:image/png;base64,{psychiatrist_b64}">
<div class="avatar-info">
<strong>Psychiatrist</strong>
<span>experience of 39 years</span>
</div>
</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with right:
        st.markdown('<div class="auth-panel-top">', unsafe_allow_html=True)
        if auth_mode == "Login":
            st.markdown('<p class="auth-panel-title">Welcome!</p>', unsafe_allow_html=True)
        else:
            st.markdown('<p class="auth-panel-title">Welcome!</p>', unsafe_allow_html=True)

        if auth_mode == "Login":
            with st.form("login_form", clear_on_submit=False):
                st.markdown('<div class="auth-social-label">Login</div>', unsafe_allow_html=True)
                login_username = st.text_input("", placeholder="Enter your login", label_visibility="collapsed")
                st.markdown('<div class="auth-social-label" style="margin-top:10px">Password</div>', unsafe_allow_html=True)
                login_password = st.text_input("", type="password", placeholder="Enter your password", label_visibility="collapsed")
                
                st.markdown(
                    '<div class="auth-tabs-note">I don\'t have an account yet, <a href="?auth=signup">registration</a></div>',
                    unsafe_allow_html=True,
                )
                login_submit = st.form_submit_button("Submit")

            if login_submit:
                if authenticate_user(login_username, login_password):
                    st.session_state.authenticated = True
                    st.session_state.username = login_username.strip().lower()
                    st.session_state.app_view = "dashboard"
                    st.success("Login successful.")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")


        else:
            with st.form("signup_form", clear_on_submit=False):
                st.markdown('<div class="auth-social-label">Login</div>', unsafe_allow_html=True)
                signup_username = st.text_input("", placeholder="Enter your login", label_visibility="collapsed")
                st.markdown('<div class="auth-social-label" style="margin-top:10px">Password</div>', unsafe_allow_html=True)
                signup_password = st.text_input("", type="password", placeholder="Enter your password", label_visibility="collapsed")
                st.markdown(
                    '<div class="auth-tabs-note">Already have an account? <a href="?auth=login">login</a></div>',
                    unsafe_allow_html=True,
                )
                signup_submit = st.form_submit_button("Submit")

            if signup_submit:
                ok, message = register_user(signup_username, signup_password)
                if ok:
                    st.success(message + " You can now login.")
                    st.query_params["auth"] = "login"
                    st.rerun()
                else:
                    st.error(message)

        st.markdown('<div class="support-label">For all questions:</div>', unsafe_allow_html=True)
        st.markdown('<div class="support-pill">📞 +1 408 123-4567</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)




# --- App Shell After Login ---


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"### 👩‍⚕️ {st.session_state.username}")
        st.caption("Authenticated session")
        st.divider()

        if st.button("🏠 Dashboard"):
            st.session_state.app_view = "dashboard"
            st.rerun()
        if st.button("🩺 New Checkup"):
            st.session_state.app_view = "new_checkup"
            st.rerun()
        if st.button("📂 Previous Checkups"):
            st.session_state.app_view = "history"
            st.rerun()

        st.divider()
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.username = ""
            st.session_state.app_view = "dashboard"
            st.rerun()


def render_dashboard() -> None:
    render_header()
    st.markdown('<p class="section-label">Workspace</p>', unsafe_allow_html=True)

    checkups = load_user_checkups(st.session_state.username)
    stat1, stat2 = st.columns(2)
    with stat1:
        st.metric("Previous Checkups", len(checkups))
    with stat2:
        st.metric("Account", st.session_state.username)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            """
<div class="option-card">
    <div class="option-title">Start New Checkup</div>
    <div class="option-copy">
        Run a fresh multidisciplinary analysis from patient details or uploaded report.
    </div>
</div>
""",
            unsafe_allow_html=True,
        )
        if st.button("Begin New Checkup"):
            st.session_state.app_view = "new_checkup"
            st.rerun()

    with col2:
        st.markdown(
            """
<div class="option-card">
    <div class="option-title">Open Previous Checkups</div>
    <div class="option-copy">
        Review historical diagnoses, urgency levels, and recommended follow-up steps.
    </div>
</div>
""",
            unsafe_allow_html=True,
        )
        if st.button("View Checkup History"):
            st.session_state.app_view = "history"
            st.rerun()


# --- New Checkup Flow ---


def render_new_checkup() -> None:
    render_header()
    st.markdown('<p class="section-label">New Checkup</p>', unsafe_allow_html=True)

    col_left, col_right = st.columns([1.15, 0.85], gap="large")

    with col_left:
        st.markdown('<p class="section-label">Patient Information</p>', unsafe_allow_html=True)
        input_mode = st.radio(
            "Input method",
            ["Fill Form", "Upload Report File"],
            horizontal=True,
            label_visibility="collapsed",
        )

        medical_report = None
        patient_name = "Unknown"

        if input_mode == "Fill Form":
            c1, c2, c3 = st.columns(3)
            with c1:
                patient_name = st.text_input("Patient Name", placeholder="e.g. David Wilson")
            with c2:
                patient_age = st.text_input("Age", placeholder="e.g. 45")
            with c3:
                patient_gender = st.selectbox("Gender", ["Male", "Female", "Other"])

            c4, c5 = st.columns(2)
            with c4:
                patient_id = st.text_input("Patient ID", placeholder="e.g. 100235")
            with c5:
                report_date = st.text_input("Date of Report", placeholder="e.g. 2025-01-03")

            chief_complaint = st.text_area("Chief Complaint", placeholder="Describe the main symptoms...", height=80)
            medical_history = st.text_area(
                "Medical History",
                placeholder="Family history, personal history, lifestyle, medications...",
                height=80,
            )
            lab_results = st.text_area("Lab & Diagnostic Results", placeholder="MRI, blood tests, ECG findings...", height=80)
            physical_exam = st.text_area(
                "Physical Examination Findings", placeholder="Vital signs, neurological exam...", height=60
            )

            if patient_name:
                medical_report = f"""Medical Case Report
Patient ID: {patient_id}
Name: {patient_name}
Age: {patient_age}
Gender: {patient_gender}
Date of Report: {report_date}

Chief Complaint:
{chief_complaint}

Medical History:
{medical_history}

Recent Lab and Diagnostic Results:
{lab_results}

Physical Examination Findings:
{physical_exam}
"""

        else:
            uploaded_file = st.file_uploader("Upload .txt or .pdf report", type=["txt", "pdf"])
            if uploaded_file:
                patient_name = uploaded_file.name
                if uploaded_file.type == "text/plain":
                    medical_report = uploaded_file.read().decode("utf-8")
                else:
                    try:
                        import pdfplumber

                        with pdfplumber.open(uploaded_file) as pdf:
                            medical_report = "\n".join(page.extract_text() or "" for page in pdf.pages)
                    except ImportError:
                        st.warning("PDF support requires pdfplumber. Run: pip install pdfplumber")

            st.markdown(
                '<p class="section-label" style="margin-top:1rem">Or load a sample report</p>',
                unsafe_allow_html=True,
            )
            sample_files = []
            reports_dir = "Medical Reports"
            if os.path.exists(reports_dir):
                sample_files = [name for name in os.listdir(reports_dir) if name.endswith(".txt")]

            if sample_files:
                selected_sample = st.selectbox("Sample Reports", ["— select —"] + sample_files)
                if selected_sample != "— select —":
                    patient_name = selected_sample
                    with open(os.path.join(reports_dir, selected_sample), "r", encoding="utf-8") as file:
                        medical_report = file.read()
                    st.success(f"Loaded: {selected_sample}")

        if medical_report:
            with st.expander("Preview Report", expanded=False):
                st.text(medical_report[:1200] + ("..." if len(medical_report) > 1200 else ""))

    with col_right:
        st.markdown('<p class="section-label">Select Specialists</p>', unsafe_allow_html=True)

        suggested_agents, suggestion_reasons = suggest_specialists(medical_report)

        if medical_report:
            suggested_text = " | ".join([f"{AGENT_ICONS[name]} {name}" for name in suggested_agents])
            st.markdown(
                f"""
                <div class="suggestion-card">
                    <div class="suggestion-title">AI Triage Suggestion</div>
                    <div class="suggestion-list">{suggested_text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("Use Suggested Specialists"):
                for name in AGENT_ICONS:
                    st.session_state[f"agent_{name}"] = name in suggested_agents
                st.rerun()

            with st.expander("Why these specialists?", expanded=False):
                for name in suggested_agents:
                    matches = suggestion_reasons.get(name, [])
                    if matches:
                        st.markdown(f"• **{name}**: matched terms -> {', '.join(matches)}")
                    else:
                        st.markdown(f"• **{name}**: broad baseline recommendation")

        selected_agents = []
        for agent_name, icon in AGENT_ICONS.items():
            checked = st.checkbox(f"{icon} {agent_name}", key=f"agent_{agent_name}")
            if checked:
                selected_agents.append(agent_name)

        st.markdown("<br>", unsafe_allow_html=True)
        run_button = st.button("🔍 Run Diagnostic Analysis", disabled=(not medical_report or not selected_agents))

        if not medical_report:
            st.caption("⬅ Fill in patient details or upload a report to begin.")
        elif not selected_agents:
            st.caption("Select at least one specialist.")

    if run_button and medical_report and selected_agents:
        st.divider()
        st.markdown('<p class="section-label">Specialist Analysis</p>', unsafe_allow_html=True)

        agents_to_run = {name: AGENT_CLASSES[name](medical_report) for name in selected_agents}

        status_cols = st.columns(len(agents_to_run))
        status_placeholders = {}
        for i, name in enumerate(agents_to_run):
            with status_cols[i]:
                status_placeholders[name] = st.empty()
                status_placeholders[name].markdown(f"**{AGENT_ICONS[name]} {name}**  \n🔄 Running...")

        responses = {}

        def get_response(agent_name, agent):
            return agent_name, agent.run()

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(get_response, name, agent): name for name, agent in agents_to_run.items()}
            for future in as_completed(futures):
                agent_name, response = future.result()
                responses[agent_name] = response
                icon = AGENT_ICONS[agent_name]
                if response:
                    status_placeholders[agent_name].markdown(f"**{icon} {agent_name}**  \n✅ Done")
                else:
                    status_placeholders[agent_name].markdown(f"**{icon} {agent_name}**  \n❌ Failed")

        valid_responses = {k: v for k, v in responses.items() if v is not None}

        if not valid_responses:
            st.error("All agents failed. Check your API key and quota.")
            return

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<p class="section-label">Specialist Reports</p>', unsafe_allow_html=True)

        for agent_name, report in valid_responses.items():
            icon = AGENT_ICONS[agent_name]
            urgency = report.get("urgency", "unknown").lower()

            with st.expander(f"{icon} {agent_name}  —  urgency: {urgency.upper()}", expanded=False):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Possible Conditions**")
                    for condition in report.get("possible_conditions", []):
                        st.markdown(f"• {condition}")
                    st.markdown("**Reasoning**")
                    st.write(report.get("reasoning", "—"))
                with col_b:
                    st.markdown("**Recommended Tests**")
                    for test in report.get("recommended_tests", []):
                        st.markdown(f"• {test}")
                    refs = report.get("pubmed_references", [])
                    if refs:
                        st.markdown("**PubMed References**")
                        for ref in refs:
                            st.markdown(f'<div class="pubmed-ref">📄 {ref}</div>', unsafe_allow_html=True)

        st.divider()
        st.markdown('<p class="section-label">Final Multidisciplinary Diagnosis</p>', unsafe_allow_html=True)

        with st.spinner("Synthesizing final diagnosis..."):
            team_agent = MultidisciplinaryTeam(specialist_reports=valid_responses)
            final = team_agent.run()

        if final is None:
            st.error("MultidisciplinaryTeam synthesis failed.")
            return

        overall_urgency = final.get("overall_urgency", "unknown").lower()
        urgency_class = URGENCY_COLORS.get(overall_urgency, "urgency-unknown")

        st.markdown(
            f'Overall Urgency: <span class="agent-badge {urgency_class}">{overall_urgency.upper()}</span>',
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        diagnoses = final.get("diagnoses", [])
        for i, diag in enumerate(diagnoses, 1):
            st.markdown(
                f"""
                <div class="diagnosis-card">
                    <div style="display:flex; align-items:center; gap:1rem; margin-bottom:0.4rem">
                        <span class="diagnosis-number">{i}</span>
                        <span class="diagnosis-title">{diag.get('condition', '—')}</span>
                    </div>
                    <div style="font-size:0.9rem; color:#475569">{diag.get('reasoning', '—')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        next_steps = final.get("recommended_next_steps", [])
        if next_steps:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<p class="section-label">Recommended Next Steps</p>', unsafe_allow_html=True)
            for i, step in enumerate(next_steps, 1):
                st.markdown(
                    f"""
                    <div class="step-item">
                        <span style="font-weight:600; color:#3b82f6; min-width:1.2rem">{i}.</span>
                        <span>{step}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        os.makedirs("results", exist_ok=True)
        output = {"specialist_reports": valid_responses, "final_diagnosis": final}
        with open("results/final_diagnosis.json", "w", encoding="utf-8") as file:
            json.dump(output, file, indent=2)

        # Save to per-user history
        record = {
            "created_at": datetime.utcnow().isoformat(),
            "patient_name": patient_name or "Unknown",
            "selected_agents": selected_agents,
            "input_report": medical_report,
            "result": output,
        }
        save_user_checkup(st.session_state.username, record)

        st.success("Checkup completed and saved to your history.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="⬇ Download Full Report (JSON)",
            data=json.dumps(output, indent=2),
            file_name="diagnosis_report.json",
            mime="application/json",
        )

        st.caption("⚠️ For research and educational purposes only. Not intended for clinical use.")


# --- History Page ---


def render_history() -> None:
    render_header()
    st.markdown('<p class="section-label">Previous Checkups</p>', unsafe_allow_html=True)

    checkups = load_user_checkups(st.session_state.username)
    if not checkups:
        st.info("No previous checkups found. Start a new one from Dashboard.")
        return

    for idx, checkup in enumerate(checkups, 1):
        created_at = checkup.get("created_at", "")
        try:
            dt = datetime.fromisoformat(created_at)
            timestamp = dt.strftime("%Y-%m-%d %H:%M UTC")
        except ValueError:
            timestamp = created_at or "Unknown time"

        patient = checkup.get("patient_name", "Unknown")
        final_diag = checkup.get("result", {}).get("final_diagnosis", {})
        urgency = final_diag.get("overall_urgency", "unknown").lower()
        urgency_class = URGENCY_COLORS.get(urgency, "urgency-unknown")

        with st.expander(f"Checkup #{idx} — {patient} — {timestamp}", expanded=False):
            st.markdown(
                f'Overall Urgency: <span class="agent-badge {urgency_class}">{urgency.upper()}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='history-meta'>Specialists: {', '.join(checkup.get('selected_agents', []))}</div>",
                unsafe_allow_html=True,
            )

            diagnoses = final_diag.get("diagnoses", [])
            if diagnoses:
                st.markdown("**Diagnoses**")
                for item in diagnoses:
                    st.markdown(f"• **{item.get('condition', '—')}**: {item.get('reasoning', '—')}")

            with st.expander("View Source Report", expanded=False):
                st.text(checkup.get("input_report", "No report text available."))

            st.download_button(
                label="Download This Checkup JSON",
                data=json.dumps(checkup.get("result", {}), indent=2),
                file_name=f"checkup_{idx}.json",
                mime="application/json",
                key=f"download_{idx}",
            )


# --- Main ---


def main() -> None:
    ensure_storage()
    init_session_state()

    if not st.session_state.authenticated:
        render_auth_page()
        return

    render_sidebar()

    if st.session_state.app_view == "dashboard":
        render_dashboard()
    elif st.session_state.app_view == "history":
        render_history()
    else:
        render_new_checkup()


if __name__ == "__main__":
    main()
