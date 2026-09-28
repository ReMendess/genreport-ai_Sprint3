"""Política de governança e LGPD do AIReport Gen-Experience (Sprint 4).

Regras de tratamento de dados da solução:
    - Base legal: consentimento do titular (Lei 13.709/2018, arts. 8 e 11).
    - Retenção configurável: ``LOG_RETENTION_DAYS`` (padrão 30 dias).
    - Minimização: a solução NUNCA grava conteúdo do usuário em logs ou
      armazenamento próprio; o conteúdo só trafega para o LLM (Groq)
      durante a geração da resposta.
    - Direitos do titular (art. 18): acesso, correção e eliminação dos
      dados locais (PDF, logs, consentimento, histórico de conversa).

Variáveis de ambiente:
    LOG_RETENTION_DAYS  — retenção de ``*.log`` em dias (padrão 30)
    REQUIRE_CONSENT     — "true" exige consentimento antes do chat (padrão false)
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from app.config import PROJECT_ROOT

# Versão da política aceita no consentimento
POLICY_VERSION = "1.0-sprint4"

LOG_DIR = PROJECT_ROOT / "logs"
DEFAULT_LOG_RETENTION_DAYS = 30

# Inventário de dados (fonte para docs/politica_governanca_sprint4.md)
DATA_INVENTORY: list[dict] = [
    {
        "data": "Relatório genético (PDF)",
        "where": "data/raw/ (local; fora do git desde a Etapa 1)",
        "retention": "enquanto o usuário mantiver o arquivo",
        "legal_basis": "consentimento do titular",
    },
    {
        "data": "Índice vetorial do relatório",
        "where": "data/vectordb/ (local; fora do git)",
        "retention": "regenerável; apagado no reprocessamento",
        "legal_basis": "consentimento do titular",
    },
    {
        "data": "Logs operacionais",
        "where": "logs/app.log (fora do git)",
        "retention": f"{DEFAULT_LOG_RETENTION_DAYS} dias (LOG_RETENTION_DAYS)",
        "legal_basis": "legítimo interesse (operação/segurança)",
    },
    {
        "data": "Eventos de auditoria",
        "where": "logs/audit.log (fora do git)",
        "retention": f"{DEFAULT_LOG_RETENTION_DAYS} dias (LOG_RETENTION_DAYS)",
        "legal_basis": "legítimo interesse (governança)",
    },
    {
        "data": "Consentimento do titular",
        "where": "data/consent.json (fora do git)",
        "retention": "até revogação ou expurgo manual",
        "legal_basis": "obrigação de registro (art. 8º, LGPD)",
    },
    {
        "data": "Histórico de conversa",
        "where": "memória do processo (volátil)",
        "retention": "reinício do servidor ou reprocessamento",
        "legal_basis": "consentimento do titular",
    },
    {
        "data": "Pergunta/resposta enviadas ao LLM",
        "where": "API externa Groq (operador)",
        "retention": "conforme política da Groq",
        "legal_basis": "consentimento do titular",
    },
]


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def log_retention_days() -> int:
    """Retenção de logs em dias (``LOG_RETENTION_DAYS``; padrão 30)."""
    raw = os.getenv("LOG_RETENTION_DAYS", str(DEFAULT_LOG_RETENTION_DAYS))
    try:
        days = int(raw)
    except ValueError:
        days = DEFAULT_LOG_RETENTION_DAYS
    return max(days, 1)


def consent_required() -> bool:
    """Indica se o consentimento deve ser exigido antes do chat."""
    return _env_flag("REQUIRE_CONSENT")


def mask_name(name: str) -> str:
    """Mascara um nome pessoal (minimização): "Renan de oliveira" → "R*** d*** O***"."""
    if not name:
        return name
    return " ".join(token[0] + "***" for token in name.split() if token)


def purge_expired_logs(
    log_dir: Optional[Path] = None,
    retention_days: Optional[int] = None,
    now: Optional[datetime] = None,
) -> list[str]:
    """Remove ``*.log`` mais antigos que a retenção configurada.

    Arquivos em uso (PermissionError em Windows) são ignorados — o expurgo
    nunca bloqueia a operação. Retorna os nomes removidos.
    """
    directory = Path(log_dir) if log_dir else LOG_DIR
    days = retention_days if retention_days is not None else log_retention_days()
    if not directory.exists():
        return []

    reference = now or datetime.now(timezone.utc)
    cutoff = reference - timedelta(days=days)
    removed: list[str] = []

    for path in sorted(directory.glob("*.log")):
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                path.unlink()
                removed.append(path.name)
        except OSError:
            continue  # em uso — reavaliado na próxima janela

    return removed


if __name__ == "__main__":
    removed = purge_expired_logs()
    print(f"Expurgo de logs (retenção {log_retention_days()} dias): {len(removed)} arquivo(s)")
    for name in removed:
        print(f"  - {name}")
