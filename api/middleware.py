"""Middleware de trace_id e log estruturado das requisições HTTP.

- Gera (ou reutiliza, se válido) o header ``X-Trace-ID``.
- Disponibiliza o id em ``request.state.trace_id`` e no contextvar.
- Registra ``http_request`` em JSON (método, rota, status, latência).
- NÃO registra corpo, parâmetros de consulta nem conteúdo do usuário.
"""
from __future__ import annotations

import logging
import re
import time

from app.observability.logging_config import TRACE_ID_CTX, new_trace_id
from app.observability.metrics import record_request

TRACE_HEADER = b"x-trace-id"
_TRACE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")

_logger = logging.getLogger("aireport.http")


def _client_trace_id(scope) -> str | None:
    """Lê o trace_id enviado pelo cliente, se for seguro/válido."""
    for name, value in scope.get("headers", []):
        if name == TRACE_HEADER:
            text = value.decode("latin-1", "ignore")
            if _TRACE_PATTERN.match(text):
                return text
    return None


class TraceContextMiddleware:
    """Middleware ASGI puro (propaga contexto aos endpoints síncronos)."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        trace_id = _client_trace_id(scope) or new_trace_id()
        scope.setdefault("state", {})["trace_id"] = trace_id
        token = TRACE_ID_CTX.set(trace_id)
        started = time.perf_counter()
        status_code = 500

        async def send_wrapper(message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                message.setdefault("headers", []).append(
                    (TRACE_HEADER, trace_id.encode("ascii", "ignore"))
                )
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - started) * 1000
            record_request(
                path=scope.get("path", ""),
                method=scope.get("method", ""),
                status=status_code,
                duration_ms=duration_ms,
            )
            _logger.info(
                "http_request",
                extra={
                    "trace_id": trace_id,
                    "method": scope.get("method", ""),
                    "path": scope.get("path", ""),
                    "status": status_code,
                    "duration_ms": round(duration_ms, 1),
                },
            )
            TRACE_ID_CTX.reset(token)
