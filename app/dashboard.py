"""Componentes do Dashboard do relatório genético.

Separa a apresentação visual da lógica de negócio. Consome os dados
estruturados de `app.report_parser` sem duplicar o processamento do PDF.
"""
from __future__ import annotations

import streamlit as st

from app.config import DASA_ACCENT, DASA_BLUE, DASA_BLUE_DARK, DASA_BLUE_LIGHT
from app.report_parser import ParsedReport

# Paleta de cores para classificação de risco (sem alarmismo)
RISK_COLORS = {
    "alto": "#B8860B",  # dourado/âmbar — atenção, não alarme
    "moderado": "#2E86AB",  # azul médio — acompanhamento
    "baixo": "#2E7D32",  # verde — sem alteração relevante
}

RISK_BADGE_COLORS = {
    "alto": "#FFF4E0",
    "moderado": "#E8F0FA",
    "baixo": "#E8F5E9",
}


def _risk_color(risk_level: str) -> str:
    return RISK_COLORS.get(risk_level.lower(), "#4A5F7A")


def _risk_badge_color(risk_level: str) -> str:
    return RISK_BADGE_COLORS.get(risk_level.lower(), "#F0F2F5")


def render_dashboard_header(report: ParsedReport) -> None:
    """Cabeçalho do dashboard com título, descrição e aviso informativo."""
    st.markdown(
        f"""
        <div class="dasa-hero">
            <div class="dasa-badge">Dasa · Genética Preventiva</div>
            <h1>AIReport Gen-Experience</h1>
            <p>
                Visão geral do seu relatório genético com os principais achados,
                classificações e composição ancestral — em linguagem clara e acessível.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="dasa-disclaimer">
            <strong>⚠️ Aviso importante:</strong> As informações apresentadas possuem
            caráter exclusivamente informativo e educacional. Não representam
            diagnóstico médico e não substituem consulta ou acompanhamento
            profissional especializado.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary_cards(report: ParsedReport) -> None:
    """Resumo geral com contagem de riscos e ancestralidade (se houver)."""
    st.markdown("## Resumo geral")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="dasa-summary-card" style="border-top: 4px solid {RISK_COLORS['alto']};">
                <div class="dasa-summary-value">{report.high_risk_count}</div>
                <div class="dasa-summary-label">Riscos aumentados</div>
                <div class="dasa-summary-hint">Predisposição genética elevada</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="dasa-summary-card" style="border-top: 4px solid {RISK_COLORS['moderado']};">
                <div class="dasa-summary-value">{report.moderate_risk_count}</div>
                <div class="dasa-summary-label">Riscos moderados</div>
                <div class="dasa-summary-hint">Acompanhamento preventivo</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="dasa-summary-card" style="border-top: 4px solid {RISK_COLORS['baixo']};">
                <div class="dasa-summary-value">{report.no_relevant_change_count}</div>
                <div class="dasa-summary-label">Sem alteração relevante</div>
                <div class="dasa-summary-hint">Resultado dentro do esperado</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if report.has_ancestry:
        st.markdown(
            """
            <div class="dasa-card" style="margin-top: 0.5rem;">
                <h3>🧬 Ancestralidade</h3>
                <p>O relatório inclui estimativa de composição genética ancestral.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_findings(report: ParsedReport) -> None:
    """Seção de principais achados com cards por condição."""
    st.markdown("## Principais achados")

    if not report.findings:
        st.info("Nenhum achado identificado no relatório.")
        return

    for finding in report.sorted_findings:
        color = _risk_color(finding.risk_level)
        badge_bg = _risk_badge_color(finding.risk_level)

        recommendations_html = ""
        if finding.recommendations:
            items = "".join(
                f"<li>{rec}</li>" for rec in finding.recommendations
            )
            recommendations_html = (
                f'<div class="dasa-finding-recs"><strong>Recomendações:</strong>'
                f"<ul>{items}</ul></div>"
            )

        st.markdown(
            f"""
            <div class="dasa-finding-card">
                <div class="dasa-finding-header">
                    <div>
                        <div class="dasa-finding-category">{finding.category}</div>
                        <div class="dasa-finding-title">{finding.condition}</div>
                    </div>
                    <span class="dasa-risk-badge" style="background:{badge_bg}; color:{color}; border:1px solid {color}33;">
                        {finding.risk_class}
                    </span>
                </div>
                <p class="dasa-finding-desc">{finding.description}</p>
                {recommendations_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_ancestry(report: ParsedReport) -> None:
    """Seção de ancestralidade — exibida apenas com dados reais do relatório."""
    if not report.has_ancestry:
        return

    st.markdown("## Ancestralidade")
    st.markdown(
        """
        <p style="color:#4A5F7A; margin-bottom: 1rem;">
            Composição genética estimada presente no relatório.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Barra horizontal empilhada com as proporções reais
    total = sum(item["percentage"] for item in report.ancestry)
    if total > 0:
        bar_html = '<div class="dasa-ancestry-bar">'
        palette = ["#003DA5", "#2E86AB", "#6C8EBF", "#9BB8D3", "#C5D5E8"]
        for i, item in enumerate(report.ancestry):
            width = item["percentage"] / total * 100
            color = palette[i % len(palette)]
            bar_html += (
                f'<div style="width:{width:.1f}%; background:{color};" '
                f'title="{item["origin"]}: {item["percentage"]:.0f}%"></div>'
            )
        bar_html += "</div>"
        st.markdown(bar_html, unsafe_allow_html=True)

    cols = st.columns(len(report.ancestry))
    for col, item in zip(cols, report.ancestry):
        with col:
            st.markdown(
                f"""
                <div class="dasa-ancestry-item">
                    <div class="dasa-ancestry-pct">{item['percentage']:.0f}%</div>
                    <div class="dasa-ancestry-origin">{item['origin']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_dashboard(report: ParsedReport) -> None:
    """Renderiza o dashboard completo como tela principal."""
    render_dashboard_header(report)
    render_summary_cards(report)
    render_findings(report)
    render_ancestry(report)