"""Validação de saída do LLM (Sprint 4) — política de conteúdo.

Detecta afirmações proibidas pelos guardrails:
    - diagnóstico definitivo ("você tem diabetes")
    - prescrição/medicação ("tome o remédio...")
    - garantias absolutas de cura

Os padrões são escritos SEM acento para casar sobre texto normalizado.
Falso-positivo evitado: "você não tem..." não casa (o "não" interrompe o
padrão) e "você tem variantes" não casa (lista de doenças explícita).
"""
from __future__ import annotations

import re

from app.validation.text_utils import normalize

POLICY_PATTERNS: tuple[tuple[str, str], ...] = (
    (
        "diagnosis",
        r"\bvoce\s+(tem|possui|esta com)\s+(?:uma?\s+)?"
        r"(diabetes|cancer|hipertensao|alzheimer|parkinson|doenca|doencas|"
        r"infarto|avc|aids|hiv|artrite|asma|insuficiencia|tumor|cisto maligno)",
    ),
    (
        "medication",
        r"\b(tome|inicie|prescreva|comece a tomar|passou a tomar)\b"
        r"[^.\n]{0,40}\b(remedio|medicamento|medicacao|antibiotico|dose|comprimido)",
    ),
    (
        "guarantee",
        r"\bgarant\w*\s+[^.\n]{0,30}\b(curas?|nunca\s+vai|nunca\s+ter|impossivel)",
    ),
)


def check_output(answer: str) -> str | None:
    """Retorna o código da violação encontrada ou ``None`` se conforme."""
    normalized = normalize(answer or "")
    for code, pattern in POLICY_PATTERNS:
        if re.search(pattern, normalized):
            return code
    return None
