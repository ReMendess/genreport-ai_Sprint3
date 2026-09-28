"""Endpoints operacionais da API (Etapa 6 — Sprint 4).

- ``GET /api/v1/status`` — saúde detalhada (PDF, índice, consentimento,
  logs) com estado ``ok`` | ``degraded`` | ``error``.
- ``GET /api/v1/metrics`` — métricas em memória (HTTP, latências, chat).

Nunca expõe caminhos completos ou dados do titular (fingerprint via hash).
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request

from app.config import EMBED_MODEL
from app.governance.consent import get_registry
from app.governance.policy import consent_required, log_retention_days
from app.observability import metrics
from app.observability.logging_config import LOG_DIR
from app.report_pipeline import ReportNotFoundError, file_fingerprint, resolve_report_pdf
from app.vector_store import CHROMA_DB_FILE, HASH_FILE, is_cache_valid

router = APIRouter(tags=["ops"])


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="seconds")


def _short_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _log_size(name: str) -> int:
    path = LOG_DIR / name
    try:
        return path.stat().st_size if path.exists() else 0
    except OSError:
        return 0


def build_status() -> dict:
    """Monta o status operacional (função pura — testável sem servidor)."""
    snap = metrics.snapshot()
    state = {
        "service": "AIReport Gen-Experience API",
        "started_at": snap["started_at"],
        "uptime_seconds": snap["uptime_seconds"],
        "report": {"found": False},
        "index": {"valid": False},
        "consent": {
            "required": consent_required(),
            "granted": get_registry().is_granted(),
        },
        "logging": {
            "retention_days": log_retention_days(),
            "app_log_bytes": _log_size("app.log"),
            "audit_log_bytes": _log_size("audit.log"),
        },
    }

    try:
        pdf_path = resolve_report_pdf()
        fingerprint = file_fingerprint(pdf_path)
        stat = pdf_path.stat()
        state["report"] = {
            "found": True,
            "name": pdf_path.name,
            "size_bytes": stat.st_size,
            "modified_at": _iso(stat.st_mtime),
            "fingerprint": _short_hash(fingerprint),
        }
    except ReportNotFoundError:
        state["status"] = "error"
        state["report"] = {"found": False, "error": "ReportNotFoundError"}
        state["index"] = {"valid": False, "reason": "sem_relatorio"}
        return state

    index_valid = is_cache_valid(fingerprint)
    index_files = [
        name
        for name in (CHROMA_DB_FILE.name, HASH_FILE.name)
        if (HASH_FILE.parent / name).exists()
    ]
    try:
        index_modified = _iso(CHROMA_DB_FILE.stat().st_mtime) if CHROMA_DB_FILE.exists() else None
    except OSError:
        index_modified = None

    state["index"] = {
        "valid": index_valid,
        "files": index_files,
        "modified_at": index_modified,
        "embedding_model": EMBED_MODEL,
    }
    state["status"] = "ok" if index_valid else "degraded"
    return state


@router.get("/status")
def get_status(request: Request) -> dict:
    """Saúde operacional da solução (PDF + índice + governança)."""
    state = build_status()
    state["service"] = f"{state['service']} {request.app.version}"
    return state


@router.get("/metrics")
def get_metrics() -> dict:
    """Métricas em memória (HTTP, latências p95, chat, recusas)."""
    return metrics.snapshot()
