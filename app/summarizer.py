"""Módulo de resumo automático por card de risco genético.

Gera resumos curtos, claros e fundamentados exclusivamente nas
informações disponíveis no relatório.

Reutiliza:
    - LLM existente (via ``app.rag_engine.get_llm``)
    - NLP simplificador (via ``app.nlp_simplifier``)
    - Risk model/classifier (via ``app.risk_classifier``)

Estrutura de saída (para futura persistência):
    {
        "risk_name": "...",
        "summary": "...",
        "classification": "...",
        "source": "..."
    }

Cache:
    - ``lru_cache`` para evitar chamadas repetidas ao LLM dentro do
      mesmo processo (reruns do Streamlit).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

from app.prompt_engineering import build_summary_prompt
from app.risk_classifier import Risk, RiskCardData

logger = logging.getLogger(__name__)


@dataclass
class RiskSummary:
    """Resumo automático de um card de risco.

    Atributos
    ---------
    risk_name : str
        Nome da condição/risco.
    summary : str
        Texto do resumo em linguagem acessível.
    classification : str
        Classificação amigável (ex.: "Predisposição aumentada").
    source : str
        Trecho original do relatório que fundamenta o resumo.
    """

    risk_name: str
    summary: str
    classification: str
    source: str

    def to_dict(self) -> dict:
        """Converte o resumo em dicionário (para persistência futura)."""
        return {
            "risk_name": self.risk_name,
            "summary": self.summary,
            "classification": self.classification,
            "source": self.source,
        }


@lru_cache(maxsize=64)
def _cached_generate_summary(
    risk_name: str,
    classification: str,
    source_text: str,
    description: str,
    recommendations_tuple: tuple[str, ...],
) -> str:
    """Gera o resumo com cache (evita chamadas repetidas ao LLM).

    Parâmetros
    ----------
    risk_name : str
        Nome da condição/risco.
    classification : str
        Classificação amigável.
    source_text : str
        Texto original do relatório.
    description : str
        Descrição do achado.
    recommendations_tuple : tuple[str, ...]
        Recomendações presentes no relatório (como tupla para hash).
    """
    from app.rag_engine import get_llm

    recommendations = list(recommendations_tuple)
    prompt = build_summary_prompt(
        risk_name=risk_name,
        classification=classification,
        source_text=source_text,
        description=description,
        recommendations=recommendations,
    )
    response = get_llm().invoke(prompt)
    return response.content.strip()


def _fallback_summary(risk: Risk) -> str:
    """Resumo de fallback quando o LLM não está disponível."""
    return (
        f"O relatório indica {risk.display_level.lower()} para {risk.name}. "
        "Isso representa uma predisposição genética e não significa "
        "que você tenha a doença."
    )


def generate_risk_summary(
    risk: Risk,
    source_context: str | None = None,
) -> RiskSummary:
    """Gera um resumo automático para um card de risco.

    Parâmetros
    ----------
    risk : Risk
        Risco normalizado (com name, level, display_level, source_text).
    source_context : str, opcional
        Contexto adicional do relatório (para fundamentar sem inventar).

    Retorna
    -------
    RiskSummary
        Resumo com risk_name, summary, classification e source.

    Em caso de falha do LLM, retorna um resumo com fallback
    (mensagem adequada) sem interromper a aplicação.
    """
    # Fallback: se não há texto fonte, não podemos gerar resumo
    if not risk.source_text or not risk.source_text.strip():
        return RiskSummary(
            risk_name=risk.name,
            summary="Não há informação suficiente no relatório para gerar um resumo.",
            classification=risk.display_level,
            source=risk.source_text,
        )

    try:
        # Usa o contexto adicional se fornecido, senão o source_text
        context = source_context or risk.source_text

        # Gera o resumo com cache
        summary_text = _cached_generate_summary(
            risk_name=risk.name,
            classification=risk.display_level,
            source_text=context,
            description=risk.description,
            recommendations_tuple=tuple(risk.recommendations),
        )

        # Se o LLM retornar vazio, usa fallback
        if not summary_text:
            logger.warning("LLM retornou resumo vazio; usando fallback.")
            summary_text = _fallback_summary(risk)

        return RiskSummary(
            risk_name=risk.name,
            summary=summary_text,
            classification=risk.display_level,
            source=risk.source_text,
        )

    except Exception as exc:
        # Fallback: não interrompe a aplicação
        logger.warning("Falha ao gerar resumo (%s); usando fallback.", exc)
        return RiskSummary(
            risk_name=risk.name,
            summary=_fallback_summary(risk),
            classification=risk.display_level,
            source=risk.source_text,
        )


def generate_risk_summary_from_card(
    card: RiskCardData,
    source_context: str | None = None,
) -> RiskSummary:
    """Gera um resumo a partir de um RiskCardData (compatibilidade).

    Parâmetros
    ----------
    card : RiskCardData
        Dados normalizados do card.
    source_context : str, opcional
        Contexto adicional do relatório.
    """
    risk = Risk(
        name=card.condition,
        category=card.category,
        level=card.risk_level_id,
        display_level=card.risk_display,
        source_text=card.description or card.risk_display,
        description=card.description,
        recommendations=list(card.recommendations),
        ai_summary=card.ai_summary,
    )
    return generate_risk_summary(risk, source_context)