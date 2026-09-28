"""Fundamentação das respostas no relatório (groundedness) — Sprint 4.

Verifica se a pergunta/resposta se apoia nos trechos recuperados:

    - ``context_relevance``: a pergunta tem relação com o contexto? Recusa
      (``relevant=False``) quando claramente fora do tema ou inexistente
      no relatório — exige 2+ termos de conteúdo e NENHUM presente.
    - ``groundedness_score``: fração de termos de conteúdo da resposta
      presentes no contexto (correspondência por prefixo de 4 caracteres,
      tolerante a flexão de gênero/número).
    - ``missing_numbers``: números (2+ dígitos) da resposta ausentes no
      contexto — possível alucinação de dado numérico.
"""
from __future__ import annotations

import re

from app.validation.text_utils import content_tokens, normalize

# Prefixo de token precisa começar uma palavra: evita falso positivo tipo
# token "morangos" (prefixo "mora") casando dentro de "demorar" no histórico.
_PREFIX_ANCHOR = r"(?<![a-z0-9])"


def _starts_word(haystack: str, prefix: str) -> bool:
    return re.search(_PREFIX_ANCHOR + re.escape(prefix), haystack) is not None

# Pontuação mínima considerada "fundamentada" no trecho consultado
MIN_GROUNDEDNESS = 0.30


def context_relevance(
    question: str,
    context: str,
    conversation_context: str | None = None,
) -> dict:
    """Avalia se o contexto (relatório + conversa) aborda a pergunta."""
    tokens = content_tokens(question)
    if not tokens:
        return {"relevant": True, "matched": 0, "tokens": 0}

    # Remove a própria pergunta do histórico: o chamador adiciona a pergunta
    # ao contexto ANTES de chamar o RAG — sem isso, toda pergunta "se casa"
    # consigo mesma e o gate de off-topic nunca dispara.
    conversation = normalize(conversation_context or "")
    norm_question = normalize(question)
    if norm_question:
        conversation = conversation.replace(norm_question, " ")

    haystack = f"{normalize(context)} {conversation}"
    matched = sum(1 for token in tokens if _starts_word(haystack, token[:4]))

    # Recusa apenas com pluralidade de termos e NENHUM correspondente
    # (1 termo isolado pode ser palavra de contexto — deixa o LLM responder
    #  com o guardrail "se faltar informação, diga").
    relevant = not (matched == 0 and len(tokens) >= 2)
    return {"relevant": relevant, "matched": matched, "tokens": len(tokens)}


def groundedness_score(answer: str, context: str) -> float:
    """Fração (0..1) de termos de conteúdo da resposta presentes no contexto."""
    tokens = content_tokens(answer)
    if not tokens:
        return 1.0

    haystack = normalize(context)
    matched = sum(1 for token in tokens if token[:4] in haystack)
    return matched / len(tokens)


def missing_numbers(answer: str, context: str) -> list[str]:
    """Números (2+ dígitos) da resposta que não aparecem no contexto."""
    answer_numbers = {
        n for n in re.findall(r"\d+", normalize(answer)) if len(n) >= 2
    }
    if not answer_numbers:
        return []

    context_numbers = set(re.findall(r"\d+", normalize(context)))
    return sorted(answer_numbers - context_numbers)
