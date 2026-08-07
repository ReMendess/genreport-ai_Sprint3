from functools import lru_cache

from langchain_community.embeddings import FastEmbedEmbeddings

from app.config import EMBED_MODEL


@lru_cache(maxsize=1)
def load_embedding_model():
    return FastEmbedEmbeddings(model_name=EMBED_MODEL)
