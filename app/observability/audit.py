"""Eventos de auditoria da governança (Sprint 4).

Grava eventos operacionais em JSON em ``logs/audit.log``.

REGRAS DE PRIVACIDADE (não negociáveis):
    - NUNCA gravar conteúdo do usuário: pergunta, resposta, fontes, nome do
      paciente ou texto do relatório.
    - Somente metadados: tamanhos, contagens, modelo, latência, status, ids.
"""
from __future__ import annotations

import hashlib
import logging

from app.observability.logging_config import AUDIT_LOGGER_NAME

# Campos que NUNCA podem aparecer em auditoria (proteção ativa contra vazamento)
FORBIDDEN_FIELDS = {"question", "answer", "sources", "patient", "content", "text"}


def log_audit(event: str, *, trace_id: str | None = None, **fields) -> dict:
    """Registra um evento de auditoria (somente metadados).

    Levanta ``ValueError`` se algum campo proibido (conteúdo do usuário)
    for passado — proteção ativa contra vazamento em logs.
    """
    forbidden = FORBIDDEN_FIELDS.intersection(fields)
    if forbidden:
        raise ValueError(f"Campos proibidos em auditoria: {sorted(forbidden)}")

    payload: dict = {}
    if trace_id:
        payload["trace_id"] = trace_id
    payload.update({key: value for key, value in fields.items() if value is not None})

    logging.getLogger(AUDIT_LOGGER_NAME).info(event, extra=payload)
    return {"event": event, **payload}


def fingerprint_hash(fingerprint: str) -> str:
    """Hash curto de um fingerprint — evita gravar caminhos em log."""
    digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
    return f"sha256:{digest[:12]}"


def audit_chat_turn(
    *,
    trace_id: str | None,
    status: str,
    question_chars: int,
    answer_chars: int,
    n_sources: int,
    duration_ms: float,
    model: str,
    conversation_turns: int | None = None,
    error_type: str | None = None,
    refused: bool | None = None,
    refusal_reason: str | None = None,
    groundedness: float | None = None,
) -> dict:
    """Auditoria de um turno do chat (somente metadados, sem conteúdo)."""
    return log_audit(
        "chat_turn",
        trace_id=trace_id,
        status=status,
        error_type=error_type,
        question_chars=question_chars,
        answer_chars=answer_chars,
        n_sources=n_sources,
        duration_ms=round(duration_ms, 1),
        model=model,
        conversation_turns=conversation_turns,
        refused=refused,
        refusal_reason=refusal_reason,
        groundedness=groundedness,
    )


def audit_report_access(
    *,
    trace_id: str | None,
    status: str,
    findings: int,
    risk_cards: int,
    has_ancestry: bool,
    duration_ms: float,
    error_type: str | None = None,
) -> dict:
    """Auditoria de acesso ao relatório (somente contagens)."""
    return log_audit(
        "report_access",
        trace_id=trace_id,
        status=status,
        error_type=error_type,
        findings=findings,
        risk_cards=risk_cards,
        has_ancestry=has_ancestry,
        duration_ms=round(duration_ms, 1),
    )


def audit_reprocess(
    *,
    trace_id: str | None,
    status: str,
    report_name: str | None,
    fingerprint: str | None,
    duration_ms: float,
    error_type: str | None = None,
) -> dict:
    """Auditoria do reprocessamento (fingerprint apenas como hash)."""
    return log_audit(
        "reprocess",
        trace_id=trace_id,
        status=status,
        error_type=error_type,
        report_name=report_name,
        fingerprint=fingerprint_hash(fingerprint) if fingerprint else None,
        duration_ms=round(duration_ms, 1),
    )
