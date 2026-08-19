"""Componentes do Dashboard do relatório genético.

Separa a apresentação visual da lógica de negócio. Consome os dados
estruturados de `app.report_parser` sem duplicar o processamento do PDF.
"""
from __future__ import annotations

import streamlit as st

from app.report_parser import ParsedReport
from app.risk_card import render_risk_card, sort_cards_by_severity
from app.risk_classifier import RISK_COLORS, RiskCardData


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
    from app.risk_classifier import RiskLevel

    st.markdown("## Resumo geral")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""
            <div class="dasa-summary-card" style="border-top: 4px solid {RISK_COLORS[RiskLevel.INCREASED.value]};">
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
            <div class="dasa-summary-card" style="border-top: 4px solid {RISK_COLORS[RiskLevel.MODERATE.value]};">
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
            <div class="dasa-summary-card" style="border-top: 4px solid {RISK_COLORS[RiskLevel.NORMAL.value]};">
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

    # Converte achados em dados normalizados e renderiza com RiskCard
    cards = [RiskCardData.from_finding(f) for f in report.findings]
    cards = sort_cards_by_severity(cards)

    # Gera resumos automáticos (com cache para evitar chamadas repetidas ao LLM)
    from app.summarizer import generate_risk_summary_from_card

    import re

    for card in cards:
        summary = generate_risk_summary_from_card(card)
        safe_condition = re.sub(r"[^a-zA-Z0-9_-]", "_", card.condition)[:50]
        render_risk_card(card, key=f"finding_{safe_condition}", summary=summary)


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