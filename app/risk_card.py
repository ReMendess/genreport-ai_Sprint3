"""Componente visual reutilizável para representar riscos genéticos.

O ``RiskCard`` recebe dados normalizados (via ``RiskCardData``) e renderiza
um card visual:

    - Nome do risco/condição
    - Categoria
    - Classificação do risco (badge normalizado)
    - Descrição curta em linguagem simples
    - Indicador visual de classificação (ícone + cor semântica)
    - Expander com detalhes, recomendações e espaço reservado para
      resumo automático (IA) futuro

A lógica de normalização/classificação fica em ``app.risk_classifier``,
fora da camada Streamlit — este módulo apenas apresenta os dados.
"""
from __future__ import annotations

import streamlit as st

from app.risk_classifier import (
    RISK_COLORS,
    RiskCardData,
    risk_badge_color,
    risk_icon,
    risk_short_description,
)
from app.summarizer import RiskSummary


def render_risk_card(
    data: RiskCardData,
    *,
    key: str | None = None,
    summary: RiskSummary | None = None,
) -> None:
    """Renderiza um card visual para um risco genético.

    Parâmetros
    ----------
    data : RiskCardData
        Dados normalizados prontos para exibição.
    key : str, opcional
        Chave única para o expander (útil quando o card é usado dentro
        de um ``st.columns`` ou em loops).
    summary : RiskSummary, opcional
        Resumo automático gerado para o card (se disponível).
    """
    color = RISK_COLORS.get(data.risk_level_id, "#7A8CA6")
    badge_bg = risk_badge_color(data.risk_level_id)
    icon = risk_icon(data.risk_level_id)
    short_desc = risk_short_description(data.risk_level_id)

    expander_key = key or f"risk_{data.condition}_{data.risk_level_id}"

    # Resumo automático (se disponível)
    summary_html = ""
    if summary is not None and summary.summary:
        summary_html = f"""
            <div class="dasa-risk-card-summary">
                <strong>Resumo:</strong> {summary.summary}
            </div>
        """

    # HTML principal do card (sem o expander)
    st.html(
        f"""
        <div class="dasa-risk-card" style="border-left: 5px solid {color};">
            <div class="dasa-risk-card-header">
                <div class="dasa-risk-card-title-block">
                    <div class="dasa-risk-card-category">{data.category}</div>
                    <div class="dasa-risk-card-title">{data.condition}</div>
                </div>
                <span class="dasa-risk-badge"
                      style="background:{badge_bg}; color:{color}; border:1px solid {color}33;">
                    {icon} {data.risk_display}
                </span>
            </div>

            {summary_html}

            <p class="dasa-risk-card-short">{short_desc}</p>

            <div class="dasa-risk-card-note">
                <strong>Predisposição ≠ diagnóstico:</strong>
                este achado indica uma <em>predisposição genética</em>, não
                um diagnóstico. A presença de uma variante não significa que
                a condição vai se manifestar.
            </div>
        </div>
        """
    )

    # Expander com detalhes completos
    with st.expander(f"Ver mais sobre {data.condition}", expanded=False, key=expander_key):
        if data.description:
            st.markdown(
                f"**Descrição:**  \n{data.description}",
                unsafe_allow_html=False,
            )
        else:
            st.caption("Sem descrição detalhada disponível no relatório.")

        if data.recommendations:
            st.markdown("**Recomendações de prevenção:**")
            for rec in data.recommendations:
                st.markdown(f"- {rec}")

        # Fonte original do relatório (explicabilidade)
        if summary is not None and summary.source:
            st.markdown("---")
            st.markdown(f"**Fonte do relatório:**  \n{summary.source}")

        # Resumo automático (também no expander para referência)
        if summary is not None and summary.summary:
            st.markdown("---")
            st.markdown(f"**Resumo automático:**  \n{summary.summary}")
        elif data.ai_summary is not None:
            st.markdown("---")
            st.markdown(f"**Resumo automático:**  \n{data.ai_summary}")
        else:
            st.markdown("---")
            st.caption(
                "💡 *O resumo automático gerado por IA estará disponível "
                "em uma próxima versão.*"
            )


def render_risk_cards_grid(
    cards: list[RiskCardData],
    *,
    columns: int = 1,
) -> None:
    """Renderiza uma grade de RiskCards de forma responsiva.

    Parâmetros
    ----------
    cards : list[RiskCardData]
        Cards normalizados a exibir.
    columns : int
        Número de colunas por linha (padrão: 1 para leitura confortável).
    """
    if not cards:
        st.info("Nenhum risco identificado no relatório.")
        return

    for i in range(0, len(cards), columns):
        row_cards = cards[i : i + columns]
        cols = st.columns(columns)

        for col, card in zip(cols, row_cards):
            with col:
                render_risk_card(card, key=f"grid_{i}_{card.condition}")


# ---------------------------------------------------------------------------
# Compatibilidade: função de ordenação usando o classificador central
# ---------------------------------------------------------------------------
def sort_cards_by_severity(cards: list[RiskCardData]) -> list[RiskCardData]:
    """Ordena os cards do mais relevante (aumentada) ao menos relevante."""
    from app.risk_classifier import RISK_ORDER

    return sorted(
        cards,
        key=lambda c: (RISK_ORDER.get(c.risk_level_id, 99), c.condition.lower()),
    )