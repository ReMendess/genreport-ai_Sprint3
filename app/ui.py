import streamlit as st

from app.config import DASA_ACCENT, DASA_BLUE, DASA_BLUE_DARK, DASA_BLUE_LIGHT


def inject_dasa_styles() -> None:
    st.markdown(
        f"""
        <style>
            .stApp {{
                background: linear-gradient(180deg, #ffffff 0%, {DASA_BLUE_LIGHT} 100%);
                font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
            }}

            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, {DASA_BLUE_DARK} 0%, {DASA_BLUE} 100%);
            }}

            [data-testid="stSidebar"] * {{
                color: #ffffff !important;
            }}

            [data-testid="stSidebar"] .stButton > button {{
                background: #ffffff;
                color: {DASA_BLUE} !important;
                border: none;
                font-weight: 600;
                border-radius: 8px;
                width: 100%;
            }}

            [data-testid="stSidebar"] .stButton > button:hover {{
                background: {DASA_BLUE_LIGHT};
                color: {DASA_BLUE_DARK} !important;
            }}

            .dasa-hero {{
                background: linear-gradient(135deg, {DASA_BLUE_DARK} 0%, {DASA_BLUE} 55%, {DASA_ACCENT} 100%);
                border-radius: 16px;
                padding: 2rem 2.5rem;
                color: white;
                margin-bottom: 1.5rem;
                box-shadow: 0 8px 24px rgba(0, 61, 165, 0.18);
            }}

            .dasa-hero h1 {{
                margin: 0;
                font-size: 2rem;
                font-weight: 700;
                letter-spacing: -0.02em;
            }}

            .dasa-hero p {{
                margin: 0.75rem 0 0 0;
                opacity: 0.92;
                font-size: 1.05rem;
                max-width: 720px;
            }}

            .dasa-badge {{
                display: inline-block;
                background: rgba(255,255,255,0.18);
                border: 1px solid rgba(255,255,255,0.35);
                border-radius: 999px;
                padding: 0.25rem 0.85rem;
                font-size: 0.8rem;
                font-weight: 600;
                margin-bottom: 0.75rem;
            }}

            .dasa-card {{
                background: #ffffff;
                border: 1px solid #d9e6f5;
                border-radius: 12px;
                padding: 1rem 1.25rem;
                margin-bottom: 1rem;
                box-shadow: 0 2px 8px rgba(0, 40, 85, 0.06);
            }}

            .dasa-card h3 {{
                color: {DASA_BLUE};
                margin: 0 0 0.35rem 0;
                font-size: 1rem;
            }}

            .dasa-card p {{
                margin: 0;
                color: #4a5f7a;
                font-size: 0.92rem;
            }}

            div[data-testid="stChatMessage"] {{
                background: #ffffff;
                border: 1px solid #e3edf8;
                border-radius: 12px;
                padding: 0.5rem 0.25rem;
            }}

            .stChatInputContainer {{
                border-color: {DASA_BLUE} !important;
            }}

            div[data-testid="stMetricValue"] {{
                color: {DASA_BLUE};
            }}

            /* ===== Dashboard ===== */
            .dasa-disclaimer {{
                background: #FFF8E7;
                border: 1px solid #F0D9A8;
                border-left: 5px solid #B8860B;
                border-radius: 10px;
                padding: 0.85rem 1.25rem;
                margin-bottom: 1.5rem;
                color: #6B5B2E;
                font-size: 0.92rem;
                line-height: 1.5;
            }}

            .dasa-summary-card {{
                background: #ffffff;
                border: 1px solid #d9e6f5;
                border-radius: 12px;
                padding: 1.25rem 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 2px 8px rgba(0, 40, 85, 0.06);
                text-align: center;
            }}

            .dasa-summary-value {{
                font-size: 2.4rem;
                font-weight: 800;
                color: {DASA_BLUE};
                line-height: 1.1;
            }}

            .dasa-summary-label {{
                font-size: 0.95rem;
                font-weight: 600;
                color: #1F3A5F;
                margin-top: 0.25rem;
            }}

            .dasa-summary-hint {{
                font-size: 0.78rem;
                color: #7A8CA6;
                margin-top: 0.15rem;
            }}

            .dasa-finding-card {{
                background: #ffffff;
                border: 1px solid #d9e6f5;
                border-radius: 12px;
                padding: 1.25rem 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 2px 8px rgba(0, 40, 85, 0.06);
            }}

            .dasa-finding-header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 1rem;
                margin-bottom: 0.5rem;
            }}

            .dasa-finding-category {{
                font-size: 0.75rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                color: {DASA_ACCENT};
                margin-bottom: 0.15rem;
            }}

            .dasa-finding-title {{
                font-size: 1.15rem;
                font-weight: 700;
                color: {DASA_BLUE_DARK};
            }}

            .dasa-risk-badge {{
                display: inline-block;
                border-radius: 999px;
                padding: 0.35rem 0.9rem;
                font-size: 0.78rem;
                font-weight: 700;
                white-space: nowrap;
                flex-shrink: 0;
            }}

            .dasa-finding-desc {{
                color: #4A5F7A;
                font-size: 0.92rem;
                line-height: 1.55;
                margin: 0 0 0.75rem 0;
            }}

            .dasa-finding-recs {{
                background: {DASA_BLUE_LIGHT};
                border-radius: 8px;
                padding: 0.75rem 1rem;
                font-size: 0.85rem;
                color: #1F3A5F;
            }}

            .dasa-finding-recs ul {{
                margin: 0.35rem 0 0 0;
                padding-left: 1.25rem;
            }}

            .dasa-finding-recs li {{
                margin-bottom: 0.2rem;
            }}

            /* ===== RiskCard ===== */
            .dasa-risk-card {{
                background: #ffffff;
                border: 1px solid #d9e6f5;
                border-radius: 12px;
                padding: 1.25rem 1.5rem;
                margin-bottom: 1.25rem;
                box-shadow: 0 2px 8px rgba(0, 40, 85, 0.06);
                transition: box-shadow 0.2s ease;
            }}

            .dasa-risk-card:hover {{
                box-shadow: 0 4px 16px rgba(0, 40, 85, 0.12);
            }}

            .dasa-risk-card-header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 1rem;
                margin-bottom: 0.6rem;
            }}

            .dasa-risk-card-title-block {{
                min-width: 0;
            }}

            .dasa-risk-card-category {{
                font-size: 0.72rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                color: {DASA_ACCENT};
                margin-bottom: 0.1rem;
            }}

            .dasa-risk-card-title {{
                font-size: 1.1rem;
                font-weight: 700;
                color: {DASA_BLUE_DARK};
                line-height: 1.3;
                word-wrap: break-word;
            }}

            .dasa-risk-card-short {{
                color: #4A5F7A;
                font-size: 0.9rem;
                line-height: 1.55;
                margin: 0 0 0.75rem 0;
            }}

            .dasa-risk-card-note {{
                background: #F7FAFD;
                border: 1px solid #E3EDF8;
                border-radius: 8px;
                padding: 0.6rem 0.85rem;
                font-size: 0.8rem;
                color: #4A5F7A;
                line-height: 1.5;
            }}

            .dasa-risk-card-summary {{
                background: {DASA_BLUE_LIGHT};
                border: 1px solid #C5D8F0;
                border-radius: 8px;
                padding: 0.75rem 1rem;
                margin-bottom: 0.75rem;
                font-size: 0.9rem;
                color: #1F3A5F;
                line-height: 1.55;
            }}

            .dasa-ancestry-bar {{
                display: flex;
                width: 100%;
                height: 28px;
                border-radius: 999px;
                overflow: hidden;
                margin-bottom: 1.25rem;
                box-shadow: inset 0 1px 3px rgba(0,0,0,0.08);
            }}

            .dasa-ancestry-item {{
                text-align: center;
                padding: 0.5rem 0.25rem;
            }}

            .dasa-ancestry-pct {{
                font-size: 1.3rem;
                font-weight: 800;
                color: {DASA_BLUE};
            }}

            .dasa-ancestry-origin {{
                font-size: 0.82rem;
                color: #4A5F7A;
                font-weight: 500;
            }}

            /* Navegação */
            .stRadio > div {{
                gap: 0.25rem;
            }}

            .stRadio label {{
                font-weight: 500;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="dasa-hero">
            <div class="dasa-badge">Dasa · Genética Preventiva</div>
            <h1>AIReport Gen-Experience</h1>
            <p>
                Interpretação inteligente de relatórios genéticos com IA generativa,
                busca semântica e arquitetura RAG — em linguagem clara e acessível.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_info_cards() -> None:
    col1, col2, col3 = st.columns(3)
    cards = [
        ("IA Generativa", "Respostas contextualizadas com base no seu relatório."),
        ("Busca Semântica", "Recupera trechos relevantes do documento automaticamente."),
        ("Prevenção", "Linguagem orientada a prevenção, sem diagnóstico médico."),
    ]
    for col, (title, desc) in zip((col1, col2, col3), cards):
        with col:
            st.markdown(
                f"""
                <div class="dasa-card">
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
