"""Ponto de entrada da API REST de AIReport Gen-Experience.

Executar com:
    python -m uvicorn api.main:app --port 8000
ou diretamente:
    python -m api.main
"""
from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware import TraceContextMiddleware
from api.routers import chat, consent, ops, report
from api.schemas import HealthResponse
from app.governance.policy import purge_expired_logs
from app.observability.logging_config import setup_logging

# Retenção LGPD: expurga logs vencidos ANTES de abrir os handlers
try:
    purge_expired_logs()
except Exception:
    pass

# Logging estruturado (JSON em logs/app.log + logs/audit.log) — idempotente
setup_logging()

def _cors_origins() -> list[str]:
    """Origens permitidas (env CORS_ALLOW_ORIGINS, separadas por vírgula)."""
    raw = os.getenv("CORS_ALLOW_ORIGINS", "*")
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or ["*"]


app = FastAPI(
    title="AIReport Gen-Experience API",
    description=(
        "Capa REST sobre o pipeline RAG existente (ChromaDB + FastEmbed + Groq). "
        "Será consumida pela futura app React Native; reutiliza a lógica de app/."
    ),
    version="0.1.0",
)

# trace_id + log por requisição (middleware externo, envolve todas as rotas)
app.add_middleware(TraceContextMiddleware)

# CORS (Etapa 8): libera o Expo Web / clientes externos (preflight incluído)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1")
app.include_router(report.router, prefix="/api/v1")
app.include_router(consent.router, prefix="/api/v1")
app.include_router(ops.router, prefix="/api/v1")


@app.get("/api/v1/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    """Health check simples."""
    return HealthResponse(status="ok")


if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=False)
