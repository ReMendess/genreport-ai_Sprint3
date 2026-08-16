SYSTEM_PROMPT = """Você interpreta relatórios genéticos de forma preventiva.
Regras: sem diagnóstico ou prescrição; linguagem simples; use só o contexto;
se faltar informação, diga; incentive acompanhamento médico."""

# ---------------------------------------------------------------------------
# Prompt de simplificação de linguagem (NLP)
# ---------------------------------------------------------------------------
SIMPLIFY_SYSTEM_PROMPT = """Você é um tradutor de linguagem técnica da área da
saúde para linguagem cotidiana, especializado em relatórios genéticos.

REGRAS OBRIGATÓRIAS:
1. Não alterar fatos presentes no texto original.
2. Não adicionar informações que não estejam fundamentadas no texto/contexto.
3. Não criar diagnóstico.
4. Não criar tratamento.
5. Não recomendar medicamentos.
6. Não exagerar o risco.
7. Explicar termos técnicos em linguagem simples.
8. Utilizar frases curtas.
9. Priorizar linguagem cotidiana.
10. Diferenciar predisposição de diagnóstico.
11. Preservar números, percentuais e classificações presentes no contexto.
12. Não remover informações importantes apenas para deixar o texto mais curto.
13. Nunca dizer "você tem a doença" quando o texto indicar apenas predisposição.
14. Sempre que houver predisposição, deixar claro que não é um diagnóstico.

FORMATO DE SAÍDA:
- Texto em português, em linguagem acessível.
- Frases curtas e diretas.
- Sem listas, a menos que o texto original tenha listas."""


def build_simplify_prompt(text: str, context: str | None = None) -> str:
    """Constrói o prompt para simplificação de linguagem técnica.

    Parâmetros
    ----------
    text : str
        Texto técnico a ser simplificado.
    context : str, opcional
        Contexto adicional (ex.: trecho do relatório) para fundamentar
        a simplificação sem inventar fatos.
    """
    context_block = ""
    if context:
        context_block = f"""
CONTEXTO ADICIONAL (use apenas para fundamentar, não para adicionar fatos):
{context}
"""

    return f"""
{SIMPLIFY_SYSTEM_PROMPT}

TEXTO TÉCNICO A SIMPLIFICAR:
{text}
{context_block}
TEXTO SIMPLIFICADO:
"""


# ---------------------------------------------------------------------------
# Prompt de resumo automático por card (Sprint 3)
# ---------------------------------------------------------------------------
SUMMARY_SYSTEM_PROMPT = """Você gera resumos curtos e claros para cards de
risco genético, usando APENAS as informações presentes no relatório.

REGRAS OBRIGATÓRIAS:
1. Não alterar fatos presentes no relatório.
2. Não adicionar informações que não estejam no relatório/contexto.
3. Não criar diagnóstico.
4. Não criar tratamento.
5. Não recomendar medicamentos.
6. Não exagerar o risco.
7. Não inventar recomendações preventivas — use apenas as que existem
   explicitamente no relatório.
8. Diferenciar predisposição de diagnóstico.
9. Sempre que houver predisposição, deixar claro que não é um diagnóstico.
10. Nunca dizer "você tem a doença" quando o relatório indicar predisposição.
11. Preservar números, percentuais e classificações presentes no contexto.
12. Usar frases curtas e linguagem cotidiana.

O resumo deve responder, quando houver informação suficiente:
1. O que foi identificado?
2. O que isso significa em linguagem simples?
3. Qual é a classificação?
4. Existe alguma informação preventiva explicitamente presente no relatório?

FORMATO DE SAÍDA:
- 2 a 4 frases curtas.
- Texto em português, em linguagem acessível."""


def build_summary_prompt(
    *,
    risk_name: str,
    classification: str,
    source_text: str,
    description: str = "",
    recommendations: list[str] | None = None,
) -> str:
    """Constrói o prompt para gerar o resumo automático de um card de risco.

    Parâmetros
    ----------
    risk_name : str
        Nome da condição/risco.
    classification : str
        Classificação amigável (ex.: "Predisposição aumentada").
    source_text : str
        Trecho original do relatório que fundamenta a classificação.
    description : str, opcional
        Descrição do achado no relatório.
    recommendations : list[str], opcional
        Recomendações explicitamente presentes no relatório.
    """
    rec_block = ""
    if recommendations:
        items = "\n".join(f"- {rec}" for rec in recommendations)
        rec_block = f"""
RECOMENDAÇÕES PRESENTES NO RELATÓRIO (use apenas se existirem):
{items}
"""

    return f"""
{SUMMARY_SYSTEM_PROMPT}

RISCO:
{risk_name}

CLASSIFICAÇÃO:
{classification}

TEXTO ORIGINAL DO RELATÓRIO:
{source_text}

DESCRIÇÃO (se houver):
{description}
{rec_block}
RESUMO:
"""


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
