from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
LOGO_PATH = ROOT_DIR / "logo_vihca.png"
APP_VERSION = "v2.2.3"


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --vihca-navy: #071521;
            --vihca-navy-2: #0b2433;
            --vihca-panel: rgba(255,255,255,.94);
            --vihca-border: rgba(15, 23, 42, .11);
            --vihca-text: #0f172a;
            --vihca-muted: #526277;
            --vihca-cyan: #0f9fb4;
            --vihca-blue: #1769aa;
            --vihca-success: #0f8a67;
            --vihca-warning: #8a5a00;
            --vihca-danger: #b42318;
        }

        html, body, [class*="css"] { font-family: Inter, "Segoe UI", Arial, sans-serif; }

        .stApp {
            background:
              radial-gradient(circle at 7% 3%, rgba(15,159,180,.13), transparent 28rem),
              radial-gradient(circle at 96% 0%, rgba(23,105,170,.11), transparent 28rem),
              linear-gradient(180deg, #f8fbfd 0%, #edf5f8 100%);
            color: var(--vihca-text) !important;
        }

        .block-container {
            max-width: 1160px;
            padding-top: 2rem;
            padding-bottom: 6rem !important;
        }

        /* Fuerza contraste en el contenido principal aun si el navegador/tema estaba en modo oscuro. */
        [data-testid="stMainBlockContainer"] h1,
        [data-testid="stMainBlockContainer"] h2,
        [data-testid="stMainBlockContainer"] h3,
        [data-testid="stMainBlockContainer"] h4,
        [data-testid="stMainBlockContainer"] h5,
        [data-testid="stMainBlockContainer"] h6,
        [data-testid="stMainBlockContainer"] p,
        [data-testid="stMainBlockContainer"] label,
        [data-testid="stMainBlockContainer"] li {
            color: var(--vihca-text);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #071521 0%, #0b2233 100%);
            border-right: 1px solid rgba(255,255,255,.06);
        }
        [data-testid="stSidebar"] * { color: #e7f2f6 !important; }
        [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12); }
        [data-testid="stSidebarNav"] { display:none; }

        .vh-hero {
            position: relative;
            overflow: hidden;
            padding: 30px 32px;
            border: 1px solid rgba(15, 159, 180, .20);
            border-radius: 26px;
            background: linear-gradient(135deg, rgba(7,21,33,.99), rgba(8,62,78,.96));
            box-shadow: 0 24px 60px rgba(7, 21, 33, .17);
            margin-bottom: 24px;
        }
        .vh-hero:before {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(110deg, transparent 45%, rgba(255,255,255,.035) 46%, transparent 70%);
            pointer-events: none;
        }
        .vh-hero:after {
            content: "";
            position: absolute;
            width: 270px;
            height: 270px;
            border-radius: 50%;
            top: -135px;
            right: -55px;
            background: radial-gradient(circle, rgba(35,211,230,.36), rgba(35,211,230,0));
            pointer-events: none;
        }
        .vh-kicker {
            color: #83e6ef !important;
            font-size: 12px;
            letter-spacing: .17em;
            font-weight: 850;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .vh-hero h1, .vh-hero h1 * {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            font-size: clamp(1.7rem, 3vw, 2.55rem);
            line-height: 1.08;
            margin: 0 0 12px 0;
            letter-spacing: -.03em;
            text-shadow: 0 1px 1px rgba(0,0,0,.08);
        }
        .vh-hero p, .vh-hero p * {
            color: #d8e8ee !important;
            -webkit-text-fill-color: #d8e8ee !important;
            font-size: 15px;
            max-width: 900px;
            margin: 0;
            line-height: 1.65;
        }

        .vh-section-title {
            font-size: 1.08rem;
            font-weight: 850;
            color: #0f172a !important;
            margin: .45rem 0 .18rem 0;
        }
        .vh-section-subtitle {
            font-size: .9rem;
            color: #526277 !important;
            margin-bottom: .9rem;
        }

        .vh-stat-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0,1fr));
            gap: 12px;
            margin: 12px 0 22px 0;
        }
        .vh-stat {
            padding: 15px 17px;
            border: 1px solid var(--vihca-border);
            border-radius: 17px;
            background: rgba(255,255,255,.94);
            box-shadow: 0 9px 25px rgba(15,23,42,.045);
        }
        .vh-stat-label { color:#526277 !important; font-size:11px; font-weight:850; text-transform:uppercase; letter-spacing:.08em; }
        .vh-stat-value { color:#0f172a !important; font-size:18px; font-weight:850; margin-top:4px; word-break:break-word; }

        .vh-card {
            border: 1px solid var(--vihca-border);
            background: rgba(255,255,255,.94);
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 14px 38px rgba(15,23,42,.055);
        }
        .vh-card-title { font-size: 1rem; font-weight: 850; color:#0f172a !important; margin:0 0 6px; }
        .vh-card-copy { font-size:.89rem; line-height:1.58; color:#526277 !important; margin:0; }

        .vh-module-head {
            min-height: 185px;
            display:flex;
            flex-direction:column;
            justify-content:flex-start;
            padding: 3px 1px 8px 1px;
        }
        .vh-module-icon {
            display:inline-flex;
            align-items:center;
            justify-content:center;
            width:42px;
            height:42px;
            border-radius:13px;
            background:linear-gradient(135deg, rgba(15,159,180,.13), rgba(23,105,170,.10));
            border:1px solid rgba(15,159,180,.18);
            font-size:21px;
            margin-bottom:14px;
        }
        .vh-module-title {
            color:#0f172a !important;
            -webkit-text-fill-color:#0f172a !important;
            font-size:1.28rem;
            line-height:1.2;
            font-weight:900;
            letter-spacing:-.02em;
            margin-bottom:8px;
        }
        .vh-module-copy {
            color:#334155 !important;
            -webkit-text-fill-color:#334155 !important;
            font-size:.96rem;
            line-height:1.55;
            margin-bottom:10px;
        }
        .vh-module-meta {
            color:#64748b !important;
            -webkit-text-fill-color:#64748b !important;
            font-size:.82rem;
            line-height:1.5;
            margin-top:auto;
        }
        .vh-session-heading {
            color:#0f172a !important;
            -webkit-text-fill-color:#0f172a !important;
            font-size:1.28rem;
            font-weight:900;
            letter-spacing:-.02em;
            margin:24px 0 8px 0;
        }

        .vh-security-note {
            display:flex;
            gap:10px;
            align-items:flex-start;
            border:1px solid rgba(15,138,103,.20);
            background:rgba(15,138,103,.075);
            border-radius:15px;
            padding:13px 15px;
            color:#145a47 !important;
            font-size:.86rem;
            margin:10px 0 17px 0;
        }
        .vh-security-note span { color:#145a47 !important; }

        .vh-notice {
            display:flex;
            align-items:flex-start;
            gap:11px;
            border-radius:16px;
            padding:14px 16px;
            margin:10px 0 18px 0;
            font-size:.9rem;
            font-weight:650;
            line-height:1.5;
        }
        .vh-notice span { color:inherit !important; }
        .vh-notice-warning { background:#fff8dd; border:1px solid #ead18a; color:#674900 !important; }
        .vh-notice-info { background:#eaf5ff; border:1px solid #b8d9f4; color:#174b72 !important; }
        .vh-notice-success { background:#e9f8f2; border:1px solid #a9dfcb; color:#145a47 !important; }
        .vh-notice-danger { background:#fff0ef; border:1px solid #f1b9b4; color:#8e1b12 !important; }

        .vh-code-card {
            text-align:center;
            padding:21px;
            border-radius:19px;
            border:1px solid rgba(15,159,180,.22);
            background:linear-gradient(135deg, rgba(15,159,180,.09), rgba(23,105,170,.075));
            margin:12px 0 16px 0;
        }
        .vh-code-label {font-size:11px;text-transform:uppercase;letter-spacing:.11em;color:#526277 !important;font-weight:850;}
        .vh-code-value {font-size:clamp(1rem,3vw,1.38rem);font-weight:900;letter-spacing:.04em;color:#083344 !important;margin-top:6px;word-break:break-all;}

        /* Contenedores nativos */
        [data-testid="stVerticalBlockBorderWrapper"] > div {
            border-color: rgba(15,23,42,.11) !important;
        }
        [data-testid="stForm"] {
            border: 1px solid var(--vihca-border);
            border-radius: 20px;
            padding: 20px;
            background: rgba(255,255,255,.91);
            box-shadow: 0 12px 32px rgba(15,23,42,.045);
        }

        /* Inputs: no depender del tema oscuro del usuario */
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input,
        [data-testid="stTextArea"] textarea {
            background:#ffffff !important;
            color:#0f172a !important;
            border-radius:11px !important;
        }
        [data-baseweb="select"] > div {
            background:#ffffff !important;
            color:#0f172a !important;
            border-radius:11px !important;
        }
        [data-baseweb="select"] span { color:#0f172a !important; }

        /* Botones primarios y secundarios con texto siempre visible */
        .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
            border-radius: 13px !important;
            min-height: 44px;
            font-weight: 780 !important;
            transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
        }
        .stButton > button[kind="secondary"],
        .stDownloadButton > button[kind="secondary"],
        .stFormSubmitButton > button[kind="secondary"] {
            background: #ffffff !important;
            color: #0f172a !important;
            border: 1px solid rgba(15, 159, 180, .32) !important;
        }
        .stButton > button[kind="secondary"] p,
        .stDownloadButton > button[kind="secondary"] p,
        .stFormSubmitButton > button[kind="secondary"] p { color:#0f172a !important; }
        .stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 24px rgba(15, 159, 180, .13);
            border-color: rgba(15,159,180,.62) !important;
        }
        button[kind="primary"] {
            background: linear-gradient(135deg, #0f9fb4, #1769aa) !important;
            color: white !important;
            border: none !important;
        }
        button[kind="primary"] p, button[kind="primary"] span { color:white !important; }

        /* Alerts de Streamlit con contraste legible */
        [data-testid="stAlert"] { border-radius:15px !important; }
        [data-testid="stAlert"] p, [data-testid="stAlert"] div, [data-testid="stAlert"] span {
            color:#0f172a !important;
        }

        /* Dataframes y pestañas */
        [data-testid="stDataFrame"] { border-radius:16px; overflow:hidden; }
        button[data-baseweb="tab"] p { color:#334155 !important; font-weight:750 !important; }

        .vh-footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background: rgba(248,251,253,.92);
            border-top: 1px solid rgba(15,23,42,.08);
            padding: 8px 18px;
            text-align: center;
            font-size: 11px;
            color: #526277 !important;
            z-index: 999;
            backdrop-filter: blur(12px);
        }
        .vh-footer b { color:#0f172a !important; }

        @media (max-width: 700px) {
            .block-container { padding-top: 1.15rem; }
            .vh-hero { padding: 22px 20px; border-radius: 21px; }
            .vh-stat-grid { grid-template-columns: 1fr; }
            .vh-footer { font-size: 10px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="vh-hero">
            <div class="vh-kicker" style="color:#83e6ef !important;-webkit-text-fill-color:#83e6ef !important;">{escape(kicker)}</div>
            <h1 style="color:#ffffff !important;-webkit-text-fill-color:#ffffff !important;">{escape(title)}</h1>
            <p style="color:#d8e8ee !important;-webkit-text-fill-color:#d8e8ee !important;">{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str = "") -> None:
    st.markdown(f'<div class="vh-section-title">{escape(title)}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="vh-section-subtitle">{escape(subtitle)}</div>', unsafe_allow_html=True)


def stats(items: list[tuple[str, str]]) -> None:
    cards = "".join(
        f'<div class="vh-stat"><div class="vh-stat-label">{escape(label)}</div>'
        f'<div class="vh-stat-value">{escape(str(value))}</div></div>'
        for label, value in items
    )
    st.markdown(f'<div class="vh-stat-grid">{cards}</div>', unsafe_allow_html=True)


def code_card(code: str) -> None:
    st.markdown(
        f'<div class="vh-code-card"><div class="vh-code-label">Código ERSI generado</div>'
        f'<div class="vh-code-value">{escape(code)}</div></div>',
        unsafe_allow_html=True,
    )


def security_note(text: str) -> None:
    st.markdown(
        f'<div class="vh-security-note"><span>🛡️</span><span>{escape(text)}</span></div>',
        unsafe_allow_html=True,
    )


def notice(text: str, tone: str = "info", icon: str | None = None) -> None:
    tone = tone if tone in {"info", "warning", "success", "danger"} else "info"
    default_icons = {"info": "ℹ️", "warning": "⚠️", "success": "✓", "danger": "⛔"}
    st.markdown(
        f'<div class="vh-notice vh-notice-{tone}"><span>{escape(icon or default_icons[tone])}</span>'
        f'<span>{escape(text)}</span></div>',
        unsafe_allow_html=True,
    )


def render_brand() -> None:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=230)


def render_sidebar(user: dict | None = None) -> None:
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width="stretch")
        st.caption(f"Plataforma ERSI · {APP_VERSION}")
        st.divider()
        if user:
            st.markdown(f"**{escape(user.get('display_name') or user.get('username', 'Usuario'))}**")
            st.caption(f"🌎 {user.get('pais', 'Sin país asignado')}")
            role = str(user.get("role", "user")).strip().lower()
            role_label = {"admin": "Administrador", "coordinator": "Coordinador", "user": "Usuario"}.get(role, role.title())
            st.caption(f"👤 {role_label}")
            st.caption("🔒 Sesión protegida")


def footer(app_name: str = "Plataforma ERSI") -> None:
    year = datetime.now().year
    st.markdown(
        f'<div class="vh-footer">© {year} <b>Proyecto VIHCA</b> · {escape(app_name)} {APP_VERSION} · Uso autorizado</div>',
        unsafe_allow_html=True,
    )
