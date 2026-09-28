"""Utilidades de normalização textual para as validações (Sprint 4)."""
from __future__ import annotations

import re
import unicodedata

# Stopwords (pt-BR + termos meta de pergunta) após normalização (sem acento).
# Objetivo: isolar TERMOS DE CONTEÚDO para relevância/groundedness sem
# falso-positivo em perguntas conversacionais ("explicar melhor" etc.).
STOPWORDS: set[str] = {
    # pronomes / artigos / possessivos / demonstrativos (len >= 4)
    "essa", "esse", "esta", "este", "esses", "essas", "estes", "estas",
    "isso", "isto", "aquilo", "aquele", "aquela", "aqueles", "aquelas",
    "elas", "eles", "voce", "voces", "nosso", "nossa", "nossos", "nossas",
    "meus", "minhas", "seus", "suas", "dele", "dela", "deles", "delas",
    "nele", "nela", "neles", "nelas", "lhes", "para", "porque", "porem",
    # verbos auxiliares / comuns frequentes
    "sera", "serao", "seria", "seriam", "estao", "estava", "estavam",
    "tinham", "houve", "fazer", "fazem", "vou", "vai", "vao", "deve",
    "devem", "deveria", "pode", "podem", "podia", "sabe", "sabem", "quer",
    "quero", "vamos", "preciso", "precisa", "gostaria", "posso", "consegue",
    "conseguem", "temos", "tenho", "tinha", "fica", "ficam", "ficar",
    # advérbios / conjuções / locuções
    "muito", "mais", "menos", "tambem", "ainda", "sempre", "nunca", "aqui",
    "ali", "onde", "quando", "assim", "entao", "talvez", "outro", "outra",
    "outros", "outras", "mesmo", "mesma", "proprio", "prpria", "entretanto",
    "portanto", "cada", "apenas", "somente", "agora", "depois", "antes",
    "durante", "conforme", "atraves", "sobre", "entre", "segundo",
    # palavras de pergunta
    "qual", "quais", "como", "quem", "quanto", "quantos", "quantas",
    "pode", "deve", "faria", "seria", "teria", "esta", "estao",
    # termos META (pedido de explicação/resumo — não são tópico do relatório)
    "explicar", "explicacao", "exemplo", "detalhe", "detalhar", "melhor",
    "melhorar", "repetir", "refazer", "confirmar", "verdade", "importante",
    "grave", "graves", "serio", "ajuda", "ajudar", "orientar", "orientacao",
    "entender", "compreender", "informacao", "informacoes", "duvida",
    "duvidas", "resumo", "resumir", "mostra", "mostram", "dizer", "disse",
    "contar", "coisa", "coisas", "maneira", "jeito", "caso", "casos",
    "parte", "obrigado", "obrigada", "entendi", "perfeito", "obrigado",
    "servico", "servicos", "opcao", "opcoes", "nivel", "niveis", "tipo",
    "tipos", "forma", "formas", "fato", "fatos",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def normalize(text: str) -> str:
    """Minúsculas, sem acentos e espaços colapsados."""
    lowered = (text or "").lower()
    stripped = "".join(
        ch
        for ch in unicodedata.normalize("NFD", lowered)
        if unicodedata.category(ch) != "Mn"
    )
    return re.sub(r"\s+", " ", stripped).strip()


def content_tokens(text: str, min_len: int = 4) -> list[str]:
    """Tokens de conteúdo (sem stopwords) para comparações lexicais."""
    return [
        tok
        for tok in _TOKEN_RE.findall(normalize(text))
        if len(tok) >= min_len and tok not in STOPWORDS
    ]
