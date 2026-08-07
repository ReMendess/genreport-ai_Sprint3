SYSTEM_PROMPT = """Você interpreta relatórios genéticos de forma preventiva.
Regras: sem diagnóstico ou prescrição; linguagem simples; use só o contexto;
se faltar informação, diga; incentive acompanhamento médico."""

def build_prompt(context, question):

    prompt = f"""
    {SYSTEM_PROMPT}

    CONTEXTO GENÉTICO:
    {context}

    PERGUNTA:
    {question}

    RESPOSTA:
    """

    return prompt