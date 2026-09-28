"""Métricas operacionais em memória (Etapa 6 — Sprint 4).

Thread-safe, sem dependências externas. Registra APENAS agregados
(contadores, latências, decisões) — nunca conteúdo do usuário.

Uso:
    from app.observability.metrics import record_request, record_chat, snapshot
"""
from __future__ import annotations

import threading
from collections import deque
from datetime import datetime, timezone
from typing import Optional

# Amostras de latência por rota (janela para p95)
_MAX_SAMPLES = 200

_lock = threading.Lock()
_started_at = datetime.now(timezone.utc)

_http_counts: dict[str, int] = {}  # status -> contagem
_http_errors = {"client": 0, "server": 0}
_http_paths: dict[str, dict] = {}
_chat = {
    "turns": 0,
    "refusals": 0,
    "refusals_by_reason": {},
    "groundedness_sum": 0.0,
    "groundedness_n": 0,
    "duration_sum_ms": 0.0,
}


def _path_stats(path: str) -> dict:
    if path not in _http_paths:
        _http_paths[path] = {
            "count": 0,
            "sum_ms": 0.0,
            "min_ms": None,
            "max_ms": 0.0,
            "samples": deque(maxlen=_MAX_SAMPLES),
        }
    return _http_paths[path]


def record_request(path: str, method: str, status: int, duration_ms: float) -> None:
    """Registra uma requisição HTTP concluída (agregados somente)."""
    with _lock:
        key = str(status)
        _http_counts[key] = _http_counts.get(key, 0) + 1
        if status >= 500:
            _http_errors["server"] += 1
        elif status >= 400:
            _http_errors["client"] += 1

        stats = _path_stats(path)
        stats["count"] += 1
        stats["sum_ms"] += duration_ms
        stats["max_ms"] = max(stats["max_ms"], duration_ms)
        stats["min_ms"] = (
            duration_ms if stats["min_ms"] is None else min(stats["min_ms"], duration_ms)
        )
        stats["samples"].append(duration_ms)


def record_chat(
    *,
    status: str,
    refused: bool,
    refusal_reason: Optional[str],
    groundedness: Optional[float],
    duration_ms: float,
) -> None:
    """Registra um turno de chat (decisão de validação + latência)."""
    with _lock:
        _chat["turns"] += 1
        _chat["duration_sum_ms"] += duration_ms
        if refused:
            _chat["refusals"] += 1
            reason = refusal_reason or "unknown"
            _chat["refusals_by_reason"][reason] = _chat["refusals_by_reason"].get(reason, 0) + 1
        if groundedness is not None:
            _chat["groundedness_sum"] += groundedness
            _chat["groundedness_n"] += 1


def _percentile(samples: list[float], fraction: float) -> Optional[float]:
    if not samples:
        return None
    ordered = sorted(samples)
    index = max(0, int(round(fraction * len(ordered))) - 1)
    return round(ordered[index], 1)


def snapshot() -> dict:
    """Retorna um dicionário JSON-friendly com todas as métricas."""
    with _lock:
        by_path = {}
        for path, stats in _http_paths.items():
            count = stats["count"]
            samples = list(stats["samples"])
            by_path[path] = {
                "count": count,
                "avg_ms": round(stats["sum_ms"] / count, 1) if count else 0.0,
                "min_ms": round(stats["min_ms"], 1) if stats["min_ms"] is not None else None,
                "max_ms": round(stats["max_ms"], 1),
                "p95_ms": _percentile(samples, 0.95),
            }

        turns = _chat["turns"]
        grounded_n = _chat["groundedness_n"]
        return {
            "started_at": _started_at.isoformat(timespec="seconds"),
            "uptime_seconds": round(
                (datetime.now(timezone.utc) - _started_at).total_seconds(), 1
            ),
            "http": {
                "requests_total": sum(_http_counts.values()),
                "errors_client_total": _http_errors["client"],
                "errors_server_total": _http_errors["server"],
                "by_status": {k: v for k, v in sorted(_http_counts.items())},
                "by_path": by_path,
            },
            "chat": {
                "turns_total": turns,
                "refusals_total": _chat["refusals"],
                "refusals_by_reason": dict(_chat["refusals_by_reason"]),
                "groundedness_avg": (
                    round(_chat["groundedness_sum"] / grounded_n, 3) if grounded_n else None
                ),
                "avg_duration_ms": (
                    round(_chat["duration_sum_ms"] / turns, 1) if turns else None
                ),
            },
        }


def reset() -> None:
    """Zera todas as métricas (uso em testes)."""
    global _started_at
    with _lock:
        _http_counts.clear()
        _http_errors["client"] = 0
        _http_errors["server"] = 0
        _http_paths.clear()
        for key in list(_chat.keys()):
            if key == "turns":
                _chat[key] = 0
            elif key == "refusals":
                _chat[key] = 0
            elif key == "refusals_by_reason":
                _chat[key] = {}
            elif key == "groundedness_n":
                _chat[key] = 0
            elif key == "groundedness_sum":
                _chat[key] = 0.0
            elif key == "duration_sum_ms":
                _chat[key] = 0.0
        _started_at = datetime.now(timezone.utc)
