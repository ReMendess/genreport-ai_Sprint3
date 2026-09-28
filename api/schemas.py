"""Esquemas (contratos) da API REST.

Usados para validação de entrada/saída e para a documentação OpenAPI.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        description="Pergunta do usuário sobre o relatório genético.",
    )


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    refused: bool = False
    refusal_reason: str | None = None
    groundedness: float | None = None


class ReprocessResponse(BaseModel):
    status: str
    report_name: str
    fingerprint: str


# ---------------------------------------------------------------------------
# Avisos (disclaimers) mostrados pela UI existente (Streamlit).
# Texto estático da interface, entregado ao cliente móvil (React Native).
# ---------------------------------------------------------------------------
DISCLAIMERS: list[str] = [
    "Este assistente não substitui consulta médica. "
    "Sempre consulte um profissional de saúde.",
    "As informações apresentadas possuem caráter exclusivamente informativo "
    "e educacional. Não representam diagnóstico médico e não substituem "
    "consulta ou acompanhamento profissional especializado.",
]


class ConsentRequest(BaseModel):
    """Registro de consentimento LGPD (sem dados pessoais)."""

    granted: bool
    policy_version: str | None = None
