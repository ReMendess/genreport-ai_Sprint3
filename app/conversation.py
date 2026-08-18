"""Gerenciador de contexto de sessão para o agente conversacional.

Mantém o histórico da conversa durante a sessão do Streamlit, permitindo
que o agente interprete perguntas de acompanhamento (ex.: "isso", "esse
risco") sem que o usuário precise repetir informações.

O contexto existe apenas durante a sessão da aplicação (via
``st.session_state``) — não há persistência permanente de dados sensíveis.

O histórico NÃO substitui o relatório como fonte de verdade. O RAG
continua sendo a fonte principal para informações genéticas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

# Limite de mensagens enviadas ao LLM (evita contexto ilimitado)
MAX_HISTORY_MESSAGES = 6
# Limite de caracteres por mensagem no contexto
MAX_MESSAGE_CHARS = 500


@dataclass
class ConversationMessage:
    """Uma mensagem da conversa."""

    role: str  # "user" ou "assistant"
    content: str
    sources: Optional[str] = None


class ConversationManager:
    """Abstração para gerenciar o histórico da conversa.

    Responsabilidades:
        - adicionar mensagem;
        - recuperar histórico;
        - limpar histórico;
        - limitar tamanho do contexto;
        - construir contexto para o LLM.
    """

    def __init__(self, session_state: Any) -> None:
        self._state = session_state
        if "conversation_messages" not in self._state:
            self._state.conversation_messages = []

    # ------------------------------------------------------------------
    # Operações básicas
    # ------------------------------------------------------------------
    def add_message(
        self,
        role: str,
        content: str,
        sources: Optional[str] = None,
    ) -> None:
        """Adiciona uma mensagem ao histórico da sessão."""
        self._state.conversation_messages.append(
            ConversationMessage(role=role, content=content, sources=sources)
        )

    def get_history(self) -> list[ConversationMessage]:
        """Retorna o histórico completo da conversa."""
        return list(self._state.conversation_messages)

    def clear(self) -> None:
        """Limpa o histórico da conversa (sem apagar relatório/índice)."""
        self._state.conversation_messages = []

    # ------------------------------------------------------------------
    # Contexto para o LLM
    # ------------------------------------------------------------------
    def get_context(self, max_messages: int = MAX_HISTORY_MESSAGES) -> str:
        """Constrói o contexto conversacional para o LLM.

        Usa apenas as últimas ``max_messages`` mensagens, com limite de
        caracteres por mensagem, para evitar contexto ilimitado.

        O contexto serve apenas para entender referências como "isso",
        "esse resultado", "e no meu caso?" — NÃO substitui o relatório.
        """
        history = self._state.conversation_messages
        if not history:
            return ""

        # Pega as últimas N mensagens
        recent = history[-max_messages:]

        lines: list[str] = []
        for msg in recent:
            content = msg.content
            if len(content) > MAX_MESSAGE_CHARS:
                content = content[:MAX_MESSAGE_CHARS] + "…"

            role_label = "Usuário" if msg.role == "user" else "Assistente"
            lines.append(f"{role_label}: {content}")

        return "\n".join(lines)

    def get_last_user_question(self) -> Optional[str]:
        """Retorna a última pergunta do usuário (para referência)."""
        history = self._state.conversation_messages
        for msg in reversed(history):
            if msg.role == "user":
                return msg.content
        return None

    def get_topic_context(self) -> str:
        """Resumo dos tópicos discutidos (para referência rápida).

        Extrai as condições/riscos mencionados nas últimas mensagens.
        """
        history = self._state.conversation_messages
        if not history:
            return ""

        # Palavras-chave de condições comuns (extraídas do relatório)
        keywords = [
            "diabetes",
            "obesidade",
            "hipertensão",
            "colesterol",
            "insônia",
            "lactose",
            "recuperação muscular",
            "risco",
            "predisposição",
        ]

        mentioned: list[str] = []
        for msg in history[-MAX_HISTORY_MESSAGES:]:
            content_lower = msg.content.lower()
            for kw in keywords:
                if kw in content_lower and kw not in mentioned:
                    mentioned.append(kw)

        if not mentioned:
            return ""

        return "Tópicos discutidos: " + ", ".join(mentioned) + "."

    # ------------------------------------------------------------------
    # Compatibilidade com o estado atual do Streamlit
    # ------------------------------------------------------------------
    @property
    def messages(self) -> list[dict]:
        """Retorna as mensagens no formato usado pelo Streamlit (dict)."""
        return [
            {
                "role": m.role,
                "content": m.content,
                "sources": m.sources,
            }
            for m in self._state.conversation_messages
        ]

    @messages.setter
    def messages(self, value: list[dict]) -> None:
        """Define as mensagens a partir de uma lista de dicts."""
        self._state.conversation_messages = [
            ConversationMessage(
                role=m.get("role", "user"),
                content=m.get("content", ""),
                sources=m.get("sources"),
            )
            for m in value
        ]