"""Verificação de saúde do pipeline (Etapa 6 — Sprint 4).

Uso:
    python scripts/monitor.py           # relatório humano (exit 0 = saudável)
    python scripts/monitor.py --json    # saída JSON (para automação/cron)

Checa: PDF presente, índice vetorial válido (cache), logs legíveis,
erros recentes de auditoria e consentimento. Não carrega o índice
nem chama a LLM (verificação leve).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.governance.consent import get_registry  # noqa: E402
from app.governance.policy import consent_required, log_retention_days  # noqa: E402
from app.observability.logging_config import LOG_DIR  # noqa: E402
from app.report_pipeline import ReportNotFoundError, file_fingerprint, resolve_report_pdf  # noqa: E402
from app.vector_store import is_cache_valid  # noqa: E402


def _recent_errors(path: Path, tail: int = 50) -> int:
    """Conta eventos com status error nas últimas N linhas do audit.log."""
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()[-tail:]
    except OSError:
        return 0
    return sum(1 for line in lines if '"status": "error"' in line)


def collect_health() -> dict:
    """Coleta a saúde da solução (função testável)."""
    checks: list[dict] = []

    # 1) Relatório PDF
    fingerprint = None
    try:
        pdf_path = resolve_report_pdf()
        fingerprint = file_fingerprint(pdf_path)
        checks.append(
            {
                "id": "report_pdf",
                "ok": True,
                "detail": f"{pdf_path.name} ({pdf_path.stat().st_size} bytes)",
            }
        )
    except ReportNotFoundError as exc:
        checks.append({"id": "report_pdf", "ok": False, "detail": type(exc).__name__})

    # 2) Índice vetorial (cache válido para o PDF atual)
    index_ok = bool(fingerprint) and is_cache_valid(fingerprint)
    checks.append(
        {
            "id": "index_cache",
            "ok": index_ok,
            "detail": "cache corresponde ao PDF" if index_ok else "reindex necessário",
        }
    )

    # 3) Logs
    app_log, audit_log = LOG_DIR / "app.log", LOG_DIR / "audit.log"
    logs_ok = app_log.exists() and audit_log.exists()
    checks.append(
        {
            "id": "logs",
            "ok": logs_ok,
            "detail": (
                f"app.log={app_log.stat().st_size if app_log.exists() else 0}B, "
                f"audit.log={audit_log.stat().st_size if audit_log.exists() else 0}B"
            ),
        }
    )

    healthy = all(check["ok"] for check in checks)
    return {
        "healthy": healthy,
        "checks": checks,
        "info": {
            "log_retention_days": log_retention_days(),
            "recent_audit_errors": _recent_errors(audit_log),
            "consent": {
                "required": consent_required(),
                "granted": get_registry().is_granted(),
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verificação de saúde (Etapa 6)")
    parser.add_argument("--json", action="store_true", help="saída JSON")
    args = parser.parse_args()

    health = collect_health()

    if args.json:
        print(json.dumps(health, ensure_ascii=False, indent=2))
        return 0 if health["healthy"] else 1

    print("AIReport Gen-Experience — verificação de saúde (Etapa 6)")
    for check in health["checks"]:
        mark = "OK  " if check["ok"] else "FALHA"
        print(f"[{mark}] {check['id']:<14} {check['detail']}")
    info = health["info"]
    print(
        f"[INFO] consentimento  required={info['consent']['required']}, "
        f"granted={info['consent']['granted']}"
    )
    print(f"[INFO] retenção       {info['log_retention_days']} dias")
    print(f"[INFO] erros recentes {info['recent_audit_errors']} (últimas 50 linhas)")
    print(f"SAUDÁVEL: {'sim' if health['healthy'] else 'não'}")
    return 0 if health["healthy"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
