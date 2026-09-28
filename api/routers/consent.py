"""Endpoints de consentimento LGPD (Sprint 4).

Expõe o status e registra o consentimento do titular (art. 8º da LGPD)
sem armazenar qualquer dado pessoal — apenas flag, versão e timestamp.
"""
from __future__ import annotations

from fastapi import APIRouter, Request

from api.schemas import ConsentRequest
from app.governance.consent import get_registry
from app.governance.policy import POLICY_VERSION, consent_required
from app.observability.audit import log_audit

router = APIRouter(tags=["consent"])


def _status_body(state: dict) -> dict:
    return {
        "required": consent_required(),
        "granted": bool(state.get("granted")),
        "policy_version": state.get("policy_version"),
        "current_policy_version": POLICY_VERSION,
        "granted_at": state.get("granted_at"),
    }


@router.get("/consent")
def get_consent() -> dict:
    """Status atual do consentimento (LGPD)."""
    return _status_body(get_registry().status())


@router.post("/consent")
def set_consent(payload: ConsentRequest, request: Request) -> dict:
    """Registra (granted=true) ou revoga (granted=false) o consentimento."""
    state = get_registry().record(
        granted=payload.granted,
        policy_version=payload.policy_version,
        source="api",
    )
    trace_id = getattr(request.state, "trace_id", None)
    # Auditoria: somente metadados (sem dados do titular)
    log_audit(
        "consent_update",
        trace_id=trace_id,
        granted=bool(payload.granted),
        policy_version=state.get("policy_version"),
    )
    return _status_body(state)
