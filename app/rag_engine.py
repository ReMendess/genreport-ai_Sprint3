from functools import lru_cache

from langchain_groq import ChatGroq

from app.config import GROQ_API_KEY, GROQ_MODEL, LLM_NUM_PREDICT, MAX_CONTEXT_CHARS, RETRIEVAL_K
from app.prompt_engineering import build_prompt


@lru_cache(maxsize=1)
def get_llm():
    return ChatGroq(
        model=GROQ_MODEL,
        temperature=0.2,
        max_tokens=LLM_NUM_PREDICT,
        api_key=GROQ_API_KEY,
    )


def _trim_context(context: str) -> str:
    if len(context) <= MAX_CONTEXT_CHARS:
        return context
    return context[:MAX_CONTEXT_CHARS] + "\n\n[...]"


def ask_question(vectordb, question: str) -> dict:
    docs = vectordb.similarity_search(question, k=RETRIEVAL_K)
    context = _trim_context("\n\n".join(doc.page_content for doc in docs))
    prompt = build_prompt(context, question)
    response = get_llm().invoke(prompt)

    return {
        "question": question,
        "answer": response.content,
        "sources": context,
    }
