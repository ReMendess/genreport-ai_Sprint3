"""Mensagens de recusa (refusal) em pt-BR — tom calmo e não alarmista.

Sempre reencaminha ao relatório/profissional de saúde, sem diagnosticar.
"""
from __future__ import annotations

REFUSAL_MESSAGES: dict[str, str] = {
    "empty": (
        "Não entendi sua pergunta. Escreva uma dúvida sobre o seu relatório "
        "genético."
    ),
    "too_long": (
        "Sua pergunta está muito longa. Reformule de forma mais curta, "
        "focada nos seus resultados."
    ),
    "prompt_injection": (
        "Só posso responder perguntas sobre o seu relatório genético. "
        "Faça uma pergunta relacionada aos seus resultados."
    ),
    "no_context": (
        "Não encontrei essa informação no seu relatório. Posso falar sobre os "
        "achados, riscos e recomendações descritos no documento. Em caso de "
        "dúvidas, converse com um profissional de saúde."
    ),
    "not_grounded": (
        "Não consegui confirmar essa informação nos trechos do seu relatório. "
        "Posso tentar com outra pergunta, ou você pode consultar o documento "
        "original com um profissional de saúde."
    ),
    "output_policy": (
        "Não consigo responder isso dentro das regras de segurança do "
        "assistente (sem diagnósticos ou prescrições). Consulte o relatório "
        "ou um profissional de saúde."
    ),
}

# Aviso de transparência quando a resposta não bate 100% com o trecho consultado
LOW_GROUNDEDNESS_NOTE = (
    "Observação: parte desta resposta não foi localizada textualmente no "
    "trecho consultado do seu relatório. Confirme os detalhes no documento "
    "original ou pergunte novamente."
)


def refusal_message(reason: str | None) -> str:
    """Retorna a mensagem de recusa para o motivo (ou a genérica)."""
    return REFUSAL_MESSAGES.get(reason or "", REFUSAL_MESSAGES["no_context"])
