"""Endpoint de conversação (RAG).

Reutiliza ``ask_question`` e ``ConversationManager`` existentes; NÃO recria
o mecanismo RAG. Registra auditoria de metadados (sem conteúdo do usuário).
"""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Request

from api.dependencies import get_conversation, get_vector_store_state
from api.schemas import ChatRequest, ChatResponse
from app.config import GROQ_MODEL
from app.governance.consent import get_registry
from app.governance.policy import consent_required
from app.observability.audit import audit_chat_turn
from app.observability.metrics import record_chat
from app.rag_engine import ask_question
from app.report_pipeline import ReportNotFoundError

router = APIRouter(tags=["chat"])


def _sources_to_list(sources: str) -> list[str]:
    """Converte o texto de fontes (chunks unidos pelo separador de parágrafo)."""
    return [segment.strip() for segment in sources.split("\n\n") if segment.strip()]


def _trace_id(request: Request) -> str | None:
    """trace_id atribuído pelo TraceContextMiddleware."""
    return getattr(request.state, "trace_id", None)


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    """Responde a uma pergunta usando o pipeline RAG existente."""
    question = payload.question.strip()
    trace_id = _trace_id(request)
    started = time.perf_counter()
    status = "ok"
    error_type = None
    answer_chars = 0
    n_sources = 0
    conversation = None
    refused = False
    refusal_reason = None
    groundedness = None

    try:
        # Consentimento LGPD (exigido apenas com REQUIRE_CONSENT=true)
        if consent_required() and not get_registry().is_granted():
            status, error_type = "error", "HTTP_403"
            raise HTTPException(
                status_code=403,
                detail="Consentimento LGPD não registrado. "
                "Envie POST /api/v1/consent para continuar.",
            )

        try:
            vectordb, _pdf, _fp = get_vector_store_state()
        except ReportNotFoundError as exc:
            status, error_type = "error", "HTTP_404"
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            status, error_type = "error", "HTTP_500"
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao inicializar o índice: {type(exc).__name__}",
            ) from exc

        conversation = get_conversation()
        # Mesmo fluxo que Streamlit: a pergunta entra no histórico e o contexto
        # é construído a partir dele (referências como "isso" / "este risco").
        conversation.add_message("user", question)
        conversation_context = conversation.get_context()

        try:
            result = ask_question(vectordb, question, conversation_context)
        except Exception as exc:
            status, error_type = "error", "HTTP_502"
            raise HTTPException(
                status_code=502,
                detail=f"Erro ao gerar resposta: {type(exc).__name__}",
            ) from exc

        conversation.add_message("assistant", result["answer"], sources=result["sources"])
        sources = _sources_to_list(result["sources"])
        answer_chars = len(result["answer"])
        n_sources = len(sources)
        refused = bool(result.get("refused", False))
        refusal_reason = result.get("refusal_reason")
        groundedness = result.get("groundedness")

        return ChatResponse(
            answer=result["answer"],
            sources=sources,
            refused=refused,
            refusal_reason=refusal_reason,
            groundedness=groundedness,
        )
    finally:
        # Métricas operacionais (agregados sem conteúdo)
        chat_duration_ms = (time.perf_counter() - started) * 1000
        record_chat(
            status=status,
            refused=refused,
            refusal_reason=refusal_reason,
            groundedness=groundedness,
            duration_ms=chat_duration_ms,
        )
        # Auditoria: somente metadados (nunca a pergunta/resposta)
        audit_chat_turn(
            trace_id=trace_id,
            status=status,
            error_type=error_type,
            question_chars=len(question),
            answer_chars=answer_chars,
            n_sources=n_sources,
            duration_ms=(time.perf_counter() - started) * 1000,
            model=GROQ_MODEL,
            conversation_turns=len(conversation.get_history()) if conversation else None,
            refused=refused,
            refusal_reason=refusal_reason,
            groundedness=groundedness,
        )
