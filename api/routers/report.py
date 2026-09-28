"""Endpoints de relatório e reprocessamento.

Expõe os dados estruturados do relatório (para o frontend futuro) e o
reprocessamento do pipeline existente. Registra auditoria de metadados
(sem conteúdo do usuário).
"""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Request

from api.dependencies import release_vector_store, reset_conversation
from api.schemas import DISCLAIMERS, ReprocessResponse
from app.observability.audit import audit_reprocess, audit_report_access
from app.report_parser import load_parsed_report
from app.report_pipeline import ReportNotFoundError, prepare_vector_store
from app.risk_card import sort_cards_by_severity
from app.risk_classifier import RiskCardData
from app.vector_store import clear_vector_cache

router = APIRouter(tags=["report"])


def _trace_id(request: Request) -> str | None:
    """trace_id atribuído pelo TraceContextMiddleware."""
    return getattr(request.state, "trace_id", None)


@router.get("/report")
def get_report(request: Request) -> dict:
    """Dados estruturados do relatório (sem o PDF bruto)."""
    trace_id = _trace_id(request)
    started = time.perf_counter()
    status = "ok"
    error_type = None
    findings_count = 0
    cards_count = 0
    has_ancestry = False

    try:
        try:
            report = load_parsed_report()
        except ReportNotFoundError as exc:
            status, error_type = "error", "HTTP_404"
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            status, error_type = "error", "HTTP_500"
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao ler o relatório: {type(exc).__name__}",
            ) from exc

        cards = [RiskCardData.from_finding(f) for f in report.findings]
        cards = sort_cards_by_severity(cards)
        findings_count = len(report.findings)
        cards_count = len(cards)
        has_ancestry = report.has_ancestry

        return {
            "report": {
                "patient": {
                    "name": report.patient_name,
                    "age": report.age,
                    "exam_date": report.exam_date,
                },
                "summary": {
                    "increased": report.high_risk_count,
                    "moderate": report.moderate_risk_count,
                    "no_relevant_change": report.no_relevant_change_count,
                    "total": len(report.findings),
                },
                "findings": [f.to_dict() for f in report.findings],
                "risk_cards": [card.to_dict() for card in cards],
                "ancestry": report.ancestry,
                "has_ancestry": report.has_ancestry,
            },
            "disclaimers": DISCLAIMERS,
        }
    finally:
        # Auditoria: somente contagens (nunca dados do paciente)
        audit_report_access(
            trace_id=trace_id,
            status=status,
            error_type=error_type,
            findings=findings_count,
            risk_cards=cards_count,
            has_ancestry=has_ancestry,
            duration_ms=(time.perf_counter() - started) * 1000,
        )


@router.post("/reprocess", response_model=ReprocessResponse)
def reprocess(request: Request) -> ReprocessResponse:
    """Reprocessa o relatório: limpa o cache vetorial e reindexa."""
    trace_id = _trace_id(request)
    started = time.perf_counter()
    status = "ok"
    error_type = None
    report_name = None
    fingerprint = None

    try:
        # Libera os handles de ChromaDB (Windows) e invalida o cache do estado
        release_vector_store()

        try:
            clear_vector_cache()
            _vectordb, pdf_path, fingerprint = prepare_vector_store(force_reindex=True)
        except ReportNotFoundError as exc:
            status, error_type = "error", "HTTP_404"
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            status, error_type = "error", "HTTP_500"
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao reprocessar: {type(exc).__name__}",
            ) from exc

        report_name = pdf_path.name

        # O relatório parseado será relido na próxima consulta
        load_parsed_report.cache_clear()
        reset_conversation()

        return ReprocessResponse(
            status="ok",
            report_name=report_name,
            fingerprint=fingerprint,
        )
    finally:
        # Auditoria: fingerprint apenas como hash (não grava caminho)
        audit_reprocess(
            trace_id=trace_id,
            status=status,
            error_type=error_type,
            report_name=report_name,
            fingerprint=fingerprint,
            duration_ms=(time.perf_counter() - started) * 1000,
        )
