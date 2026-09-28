"""Validação de entrada do chat (Sprint 4).

Protege contra: perguntas vazias, excesso de tamanho e tentativas de
injeção de prompt (contornar as regras do assistente).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.validation.text_utils import normalize

MAX_QUESTION_CHARS = 2000

# Padrões de injeção (texto normalizado: minúsculas e sem acento)
INJECTION_PATTERNS: tuple[str, ...] = (
    r"ignore\s+(?:\w+\s+){0,4}instruc",
    r"ignore\s+previous",
    r"ignore\s+all\s+(rules|instructions)",
    r"esquec\w*\s+tudo",
    r"voce\s+e\s+agora",
    r"you\s+are\s+now",
    r"mostre\s+(o\s+|este\s+|esse\s+)?(system\s+)?prompt",
    r"reveal\s+(your\s+)?system\s*prompt",
    r"jailbreak",
    r"\bmodo\s+dan\b|\bdan\s+modo\b",
    r"sem\s+restric",
    r"sem\s+censura",
    r"responda\s+sem\s+filtro",
    r"modo\s+desenvolvedor|developer\s+mode",
    r"nova\s+persona|mude\s+sua\s+persona|finja\s+que",
    r"bypass",
)

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


@dataclass
class InputCheck:
    """Resultado da validação de entrada."""

    ok: bool
    reason: str | None = None  # empty | too_long | prompt_injection
    clean: str = ""


def sanitize_input(question: str) -> InputCheck:
    """Valida e normaliza a pergunta do usuário (sem alterar o sentido)."""
    clean = _CONTROL_CHARS.sub("", question or "").strip()

    if not clean:
        return InputCheck(ok=False, reason="empty", clean="")

    if len(clean) > MAX_QUESTION_CHARS:
        return InputCheck(ok=False, reason="too_long", clean="")

    normalized = normalize(clean)
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, normalized):
            return InputCheck(ok=False, reason="prompt_injection", clean="")

    return InputCheck(ok=True, clean=clean)
