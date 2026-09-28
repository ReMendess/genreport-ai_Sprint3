"""Dependências compartilhadas da API (FastAPI).

Contêm apenas carga/estado reutilizável: índice vetorial (pipeline existente)
e sessão conversacional em memória. NÃO contêm lógica de negócio.
"""
from __future__ import annotations

import gc
from functools import lru_cache

from app.conversation import ConversationManager
from app.report_pipeline import prepare_vector_store


class DictSessionState(dict):
    """Estado de sessão em memória compatível com ``ConversationManager``.

    Expõe os valores como atributos (``state.conversation_messages``), igual
    que faz ``st.session_state`` no Streamlit.
    """

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name: str, value) -> None:
        self[name] = value


_session_state = DictSessionState()
_conversation = ConversationManager(_session_state)


@lru_cache(maxsize=1)
def get_vector_store_state():
    """Carrega (ou reutiliza o cache) o estado do índice vetorial.

    Retorna a tupla ``(vectordb, pdf_path, fingerprint)`` produzida pelo
    pipeline existente ``prepare_vector_store``.
    """
    return prepare_vector_store()


def get_conversation() -> ConversationManager:
    """Retorna o gestor de conversação compartilhado (em memória)."""
    return _conversation


def reset_conversation() -> None:
    """Limpa o histórico da conversa (por exemplo, após reprocessar)."""
    _conversation.clear()


def release_vector_store() -> None:
    """Libera os handles de ChromaDB antes de reprocessar o índice.

    Necessário em Windows: com o índice cargado, chromadb mantiene aberto
    ``chroma.sqlite3`` e o sistema não permite removê-lo (PermissionError).
    """
    vectordb = client = close = clear_system_cache = None
    try:
        vectordb, _pdf, _fp = get_vector_store_state()
        client = getattr(vectordb, "_client", None)
        close = getattr(client, "close", None)
        if callable(close):
            close()
            close = None
        clear_system_cache = getattr(client, "clear_system_cache", None)
        if callable(clear_system_cache):
            clear_system_cache()
    except Exception:
        pass
    finally:
        get_vector_store_state.cache_clear()
        # Libera TODAS las referencias antes do GC: si ficam vivas (client ou
        # bound method), o refcount impede a recolção e o handle continua aberto.
        # ``client.close()`` fecha a conexão sqlite de chromadb (necesário en Windows).
        vectordb = None
        client = None
        clear_system_cache = None
        gc.collect()
        gc.collect()
