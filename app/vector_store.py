import shutil
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import EMBED_MODEL, VECTORDB_DIR
from app.embeddings import load_embedding_model

HASH_FILE = VECTORDB_DIR / ".source_hash"
CHROMA_DB_FILE = VECTORDB_DIR / "chroma.sqlite3"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 80


def _cache_key(source_fingerprint: str) -> str:
    return f"{source_fingerprint}|{EMBED_MODEL}"


def _has_persisted_store() -> bool:
    return CHROMA_DB_FILE.exists()


def clear_vector_cache() -> None:
    _clear_vectordb_dir()


def _clear_vectordb_dir() -> None:
    if not VECTORDB_DIR.exists():
        VECTORDB_DIR.mkdir(parents=True, exist_ok=True)
        return

    for item in VECTORDB_DIR.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


def _load_existing_store(embeddings):
    return Chroma(
        persist_directory=str(VECTORDB_DIR),
        embedding_function=embeddings,
    )


def try_load_cached_store(source_fingerprint: str):
    """Carrega o índice persistido sem reprocessar o PDF."""
    cache_key = _cache_key(source_fingerprint)
    VECTORDB_DIR.mkdir(parents=True, exist_ok=True)

    if not (
        HASH_FILE.exists()
        and HASH_FILE.read_text(encoding="utf-8").strip() == cache_key
        and _has_persisted_store()
    ):
        return None

    try:
        return _load_existing_store(load_embedding_model())
    except Exception:
        return None


def get_or_create_vector_store(text: str, source_fingerprint: str):
    VECTORDB_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = _cache_key(source_fingerprint)

    cached = try_load_cached_store(source_fingerprint)
    if cached is not None:
        return cached

    embeddings = load_embedding_model()
    _clear_vectordb_dir()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_text(text)

    vectordb = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory=str(VECTORDB_DIR),
    )

    HASH_FILE.write_text(cache_key, encoding="utf-8")
    return vectordb


def create_vector_store(text: str):
    fingerprint = f"legacy:{hash(text)}"
    return get_or_create_vector_store(text, fingerprint)
