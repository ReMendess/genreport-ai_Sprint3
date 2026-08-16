"""Camada de simplificação de linguagem técnica (NLP).

Transforma explicações técnicas do relatório genético em linguagem
acessível para pessoas sem formação na área da saúde.

Reutiliza o LLM já existente no projeto (via ``app.rag_engine.get_llm``),
sem criar uma segunda integração independente.

Interface pública:
    simplify_text(text, context=None) -> str

Em caso de falha do LLM, retorna o texto original (fallback) sem
interromper a aplicação.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from app.prompt_engineering import build_simplify_prompt

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_llm():
    """Obtém o LLM reutilizando a abstração existente no rag_engine."""
    from app.rag_engine import get_llm

    return get_llm()


def simplify_text(text: str, context: str | None = None) -> str:
    """Simplifica um texto técnico para linguagem acessível.

    Parâmetros
    ----------
    text : str
        Texto técnico a ser simplificado.
    context : str, opcional
        Contexto adicional (ex.: trecho do relatório) para fundamentar
        a simplificação sem inventar fatos.

    Retorna
    -------
    str
        Texto simplificado. Em caso de falha do LLM, retorna o texto
        original (fallback) sem interromper a aplicação.
    """
    if not text or not text.strip():
        return text

    try:
        prompt = build_simplify_prompt(text, context)
        response = _get_llm().invoke(prompt)
        simplified = response.content.strip()

        # Se o LLM retornar vazio, usa o texto original
        if not simplified:
            logger.warning("LLM retornou resposta vazia na simplificação; usando texto original.")
            return text

        return simplified
    except Exception as exc:
        # Fallback: não interrompe a aplicação
        logger.warning("Falha ao simplificar texto (%s); usando texto original.", exc)
        return text