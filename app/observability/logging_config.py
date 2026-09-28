"""Logging estruturado (JSON) com trace_id para o AIReport Gen-Experience.

Princípios de governança (Sprint 4):
    - Um evento JSON por linha, com timestamp, nível, trace_id e extras.
    - ``trace_id`` correlaciona a requisição HTTP com seus eventos internos.
    - NUNCA registrar conteúdo do usuário (pergunta, resposta, nome do
      paciente ou texto do relatório) — somente metadados.

Uso:
    from app.observability.logging_config import setup_logging
    setup_logging()   # idempotente; cria logs/app.log e logs/audit.log
"""
from __future__ import annotations

import json
import logging
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import PROJECT_ROOT

# Contextvar de trace_id (correlação de eventos da mesma requisição)
TRACE_ID_CTX: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

# Auditoria fica em arquivo próprio (governança)
AUDIT_LOGGER_NAME = "aireport.audit"
LOG_DIR = PROJECT_ROOT / "logs"

# Atributos padrão do LogRecord (não devem aparecer como extras no JSON)
_STANDARD_ATTRS = frozenset(logging.makeLogRecord({}).__dict__) | {"message", "asctime"}

_CONFIGURED = False


def new_trace_id() -> str:
    """Gera um trace_id curto e opaco (sem dados pessoais)."""
    return uuid.uuid4().hex[:12]


def get_trace_id() -> Optional[str]:
    """Retorna o trace_id do contexto atual (se houver)."""
    return TRACE_ID_CTX.get()


class JsonFormatter(logging.Formatter):
    """Serializa cada registro de log como uma linha JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = value

        if "trace_id" not in payload:
            trace_id = get_trace_id()
            if trace_id:
                payload["trace_id"] = trace_id

        if record.exc_info and record.exc_info[0] is not None:
            payload["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging(
    log_dir: Optional[Path] = None,
    level: int = logging.INFO,
    force: bool = False,
) -> Path:
    """Configura o logging JSON no logger raiz (idempotente).

    Cria ``<log_dir>/app.log`` (operações) e ``<log_dir>/audit.log``
    (eventos de governança). Retorna o diretório usado.
    """
    global _CONFIGURED

    target = Path(log_dir) if log_dir else LOG_DIR

    if _CONFIGURED and not force:
        return target

    root = logging.getLogger()
    for handler in list(root.handlers):
        if getattr(handler, "_aireport", False):
            root.removeHandler(handler)
            handler.close()

    audit_logger = logging.getLogger(AUDIT_LOGGER_NAME)
    for handler in list(audit_logger.handlers):
        if getattr(handler, "_aireport", False):
            audit_logger.removeHandler(handler)
            handler.close()

    target.mkdir(parents=True, exist_ok=True)
    formatter = JsonFormatter()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler._aireport = True  # marcador para remoção seletiva
    root.addHandler(stream_handler)

    file_handler = logging.FileHandler(target / "app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler._aireport = True
    root.addHandler(file_handler)

    root.setLevel(level)

    # Arquivo dedicado de auditoria (governança); não propaga para app.log
    audit_handler = logging.FileHandler(target / "audit.log", encoding="utf-8")
    audit_handler.setFormatter(formatter)
    audit_handler._aireport = True
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False

    _CONFIGURED = True
    return target
