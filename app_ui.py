from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
LOGO_PATH = ROOT_DIR / "logo_vihca.png"
APP_VERSION = "v2.0.0"


def inject_global_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --vihca-navy: #071521;
            --vihca-panel: rgba(255,255,255,.88);
            --vihca-border: rgba(15, 23, 42, .10);
            --vihca-text: #0f172a;
            --vihca-muted: #64748b;
            --vihca-cyan: #0f9fb4;
            --vihca-blue: #1769aa;
            --vihca-success: #0f8a67;
        }

        .stApp {
            background:
              radial-gradient(circle at 8% 5%, rgba(15,159,180,.14), transparent 26rem),
              radial-gradient(circle at 95% 0%, rgba(23,105,170,.12), transparent 25rem),
              linear-gradient(180deg, #f8fbfd 0%, #eef5f8 100%);
            color: var(--vihca-text);
        }

        .block-container {
            max-width: 1120px;
            padding-top: 2.2rem;
            padding-bottom: 6rem !important;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #071521 0%, #0b2233 100%);
            border-right: 1px solid rgba(255,255,255,.06);
        }
        [data-testid="stSidebar"] * { color: #e7f2f6; }
        [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.12); }

        .vh-hero {
            position: relative;
            overflow: hidden;
            padding: 26px 28px;
            border: 1px solid rgba(15, 159, 180, .18);
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(7,21,33,.98), rgba(9,57,75,.94));
            box-shadow: 0 22px 55px rgba(7, 21, 33, .16);
            margin-bottom: 22px;
        }
        .vh-hero:after {
            content: "";
            position: absolute;
            width: 240px;
            height: 240px;
            border-radius: 50%;
            top: -120px;
            right: -60px;
            background: radial-gradient(circle, rgba(35,211,230,.32), rgba(35,211,230,0));
            pointer-events: none;
        }
        .vh-kicker {
            color: #71dbe8;
            font-size: 12px;
            letter-spacing: .16em;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 7px;
        }
        .vh-hero h1 {
            color: #ffffff;
            font-size: clamp(1.65rem, 3vw, 2.45rem);
            line-height: 1.08;
            margin: 0 0 10px 0;
            letter-spacing: -.03em;
        }
        .vh-hero p {
            color: #bed3db;
            font-size: 15px;
            max-width: 760px;
            margin: 0;
            line-height: 1.6;
        }

        .vh-section-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: #0f172a;
            margin: .3rem 0 .15rem 0;
        }
        .vh-section-subtitle {
            font-size: .88rem;
            color: #64748b;
            margin-bottom: .8rem;
        }

        .vh-stat-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0,1fr));
            gap: 12px;
            margin: 12px 0 20px 0;
        }
        .vh-stat {
            padding: 14px 16px;
            border: 1px solid var(--vihca-border);
            border-radius: 16px;
            background: rgba(255,255,255,.78);
            box-shadow: 0 8px 24px rgba(15,23,42,.04);
        }
        .vh-stat-label { color:#64748b; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.08em; }
        .vh-stat-value { color:#0f172a; font-size:17px; font-weight:800; margin-top:4px; }

        .vh-card {
            border: 1px solid var(--vihca-border);
            background: rgba(255,255,255,.86);
            border-radius: 20px;
            padding: 18px;
            box-shadow: 0 14px 36px rgba(15,23,42,.055);
        }
        .vh-card-title { font-size: 1rem; font-weight: 850; color:#0f172a; margin:0 0 6px; }
        .vh-card-copy { font-size:.88rem; line-height:1.55; color:#64748b; margin:0; }

        .vh-security-note {
            display:flex;
            gap:10px;
            align-items:flex-start;
            border:1px solid rgba(15,138,103,.18);
            background:rgba(15,138,103,.07);
            border-radius:14px;
            padding:12px 14px;
            color:#145a47;
            font-size:.84rem;
            margin:10px 0 16px 0;
        }

        .vh-code-card {
            text-align:center;
            padding:20px;
            border-radius:18px;
            border:1px solid rgba(15,159,180,.20);
            background:linear-gradient(135deg, rgba(15,159,180,.08), rgba(23,105,170,.07));
            margin:12px 0 16px 0;
        }
        .vh-code-label {font-size:11px;text-transform:uppercase;letter-spacing:.11em;color:#64748b;font-weight:800;}
        .vh-code-value {font-size:clamp(1rem,3vw,1.35rem);font-weight:900;letter-spacing:.04em;color:#083344;margin-top:6px;word-break:break-all;}

        .stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
            border-radius: 12px !important;
            min-height: 43px;
            font-weight: 750 !important;
            border: 1px solid rgba(15, 159, 180, .22) !important;
            transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease;
        }
        .stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 24px rgba(15, 159, 180, .12);
            border-color: rgba(15,159,180,.55) !important;
        }
        button[kind="primary"] {
            background: linear-gradient(135deg, #0f9fb4, #1769aa) !important;
            color: white !important;
            border: none !important;
        }

        [data-testid="stTextInput"] input,
        [data-testid="stSelectbox"] > div > div {
            border-radius: 11px !important;
        }

        [data-testid="stForm"] {
            border: 1px solid var(--vihca-border);
            border-radius: 20px;
            padding: 20px;
            background: rgba(255,255,255,.80);
            box-shadow: 0 12px 30px rgba(15,23,42,.04);
        }

        .vh-footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background: rgba(248,251,253,.88);
            border-top: 1px solid rgba(15,23,42,.08);
            padding: 8px 18px;
            text-align: center;
            font-size: 11px;
            color: #64748b;
            z-index: 999;
            backdrop-filter: blur(12px);
        }
        .vh-footer b { color:#0f172a; }

        @media (max-width: 700px) {
            .block-container { padding-top: 1.2rem; }
            .vh-hero { padding: 21px 19px; border-radius: 20px; }
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
            <div class="vh-kicker">{escape(kicker)}</div>
            <h1>{escape(title)}</h1>
            <p>{escape(subtitle)}</p>
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
            st.caption("🔒 Sesión protegida")


def footer(app_name: str = "Plataforma ERSI") -> None:
    year = datetime.now().year
    st.markdown(
        f'<div class="vh-footer">© {year} <b>Proyecto VIHCA</b> · {escape(app_name)} {APP_VERSION} · Uso autorizado</div>',
        unsafe_allow_html=True,
    )
