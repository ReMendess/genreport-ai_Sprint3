"""Registro de consentimento do titular (LGPD, art. 8º — Sprint 4).

Guarda APENAS: flag de consentimento, versão da política, timestamp e
origem. NUNCA dados pessoais (nome, documento, contato ou conteúdo do
relatório). Persiste em ``data/consent.json`` (ignorado pelo git).
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.config import PROJECT_ROOT
from app.governance.policy import POLICY_VERSION

DEFAULT_CONSENT_PATH = PROJECT_ROOT / "data" / "consent.json"
_LOCK = threading.Lock()

# Chaves permitidas no registro (inventário fechado — sem PII)
_CONSENT_KEYS = ("granted", "policy_version", "granted_at", "source")


class ConsentRegistry:
    """Registro de consentimento com persistência local (sem PII)."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self._path = Path(path) if path else DEFAULT_CONSENT_PATH
        self._state = self._empty()
        self._load()

    @staticmethod
    def _empty() -> dict:
        return {key: None if key != "granted" else False for key in _CONSENT_KEYS}

    def _load(self) -> None:
        try:
            if self._path.exists():
                data = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    for key in _CONSENT_KEYS:
                        if key in data:
                            self._state[key] = data[key]
        except (OSError, ValueError):
            self._state = self._empty()

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(
                json.dumps(self._state, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass  # persistência best-effort

    def record(
        self,
        granted: bool,
        policy_version: str | None = None,
        source: str = "api",
    ) -> dict:
        """Registra (ou revoga) o consentimento e persiste o estado."""
        with _LOCK:
            if granted:
                self._state = {
                    "granted": True,
                    "policy_version": policy_version or POLICY_VERSION,
                    "granted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "source": source,
                }
            else:
                self._state = self._empty()
            self._save()
            return dict(self._state)

    def is_granted(self) -> bool:
        return bool(self._state.get("granted"))

    def status(self) -> dict:
        return dict(self._state)

    def clear(self) -> None:
        with _LOCK:
            self._state = self._empty()
            self._save()


_registry = ConsentRegistry()


def get_registry() -> ConsentRegistry:
    """Registro singleton usado pela API."""
    return _registry
