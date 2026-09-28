from functools import lru_cache

from langchain_groq import ChatGroq

from app.config import GROQ_API_KEY, GROQ_MODEL, LLM_NUM_PREDICT, MAX_CONTEXT_CHARS, RETRIEVAL_K
from app.prompt_engineering import build_prompt
from app.validation.groundedness import (
    MIN_GROUNDEDNESS,
    context_relevance,
    groundedness_score,
    missing_numbers,
)
from app.validation.input_sanitizer import sanitize_input
from app.validation.output_policy import check_output
from app.validation.refusals import LOW_GROUNDEDNESS_NOTE, refusal_message


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


def _result(
    question: str,
    answer: str,
    sources: str,
    *,
    refused: bool,
    refusal_reason: str | None,
    groundedness: float | None,
) -> dict:
    """Monta a resposta padrão (inclui campos de validação da Sprint 4)."""
    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "refused": refused,
        "refusal_reason": refusal_reason,
        "groundedness": groundedness,
    }


def ask_question(
    vectordb,
    question: str,
    conversation_context: str | None = None,
) -> dict:
    """Faz uma pergunta ao RAG, com validações programáticas (Sprint 4).

    Parâmetros
    ----------
    vectordb
        Índice vetorial do relatório.
    question : str
        Pergunta do usuário.
    conversation_context : str, opcional
        Histórico da conversa (últimas mensagens) para interpretar
        referências como "isso", "esse risco". NÃO substitui o relatório.

    Fluxo de validação (não altera o mecanismo RAG):
        1. Entrada: vazio, tamanho e injeção de prompt.
        2. Relevância: recusa se o contexto não aborda a pergunta
           (fora do tema / dado inexistente no relatório).
        3. Saída: política (sem diagnóstico/prescrição/garantia).
        4. Groundedness: score de fundamentação + aviso se fraco.

    Retorno inclui ``refused``, ``refusal_reason`` e ``groundedness``
    (campos adicionais — ``answer``/``sources`` permanecem iguais).
    """
    # 1) Validação de entrada (antes de qualquer chamada externa)
    check = sanitize_input(question)
    if not check.ok:
        return _result(
            question[:200],
            refusal_message(check.reason),
            "",
            refused=True,
            refusal_reason=check.reason,
            groundedness=None,
        )

    docs = vectordb.similarity_search(question, k=RETRIEVAL_K)
    context = _trim_context("\n\n".join(doc.page_content for doc in docs))

    # 2) Relevância do contexto (off-topic / dado inexistente)
    relevance = context_relevance(question, context, conversation_context)
    if not relevance["relevant"]:
        return _result(
            question,
            refusal_message("no_context"),
            context,
            refused=True,
            refusal_reason="no_context",
            groundedness=None,
        )

    prompt = build_prompt(context, question, conversation_context)
    response = get_llm().invoke(prompt)
    answer = response.content

    # 3) Política de saída (guardrails de conteúdo)
    violation = check_output(answer)
    if violation:
        return _result(
            question,
            refusal_message("output_policy"),
            context,
            refused=True,
            refusal_reason="output_policy",
            groundedness=None,
        )

    # 4) Fundamentação no relatório: abaixo do mínimo → extrapolação → recusa
    score = groundedness_score(answer, context)
    if score < MIN_GROUNDEDNESS:
        return _result(
            question,
            refusal_message("not_grounded"),
            context,
            refused=True,
            refusal_reason="not_grounded",
            groundedness=round(score, 3),
        )

    # Números fora do contexto → apenas aviso de transparência
    if missing_numbers(answer, context):
        answer = f"{answer}\n\n{LOW_GROUNDEDNESS_NOTE}"

    return _result(
        question,
        answer,
        context,
        refused=False,
        refusal_reason=None,
        groundedness=round(score, 3),
    )
