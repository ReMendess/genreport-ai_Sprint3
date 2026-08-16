"""Camada de domínio para normalização e classificação de riscos genéticos.

Centraliza o mapeamento de nomenclaturas encontradas nos PDFs para um
conjunto padronizado de classificações, evitando regras espalhadas na
camada de interface (Streamlit).

Classificações internas (estáveis):
    - INCREASED  → "Predisposição aumentada"
    - MODERATE   → "Predisposição moderada"
    - REDUCED    → "Predisposição reduzida"
    - NORMAL     → "Sem alteração relevante"
    - UNKNOWN    → "Não identificado"

Princípios de governança:
    - A classificação representa APENAS o que está no relatório.
    - Nunca inferir risco médico adicional.
    - Nunca transformar "predisposição aumentada" em "você possui a doença".
    - Sempre diferenciar predisposição genética ≠ diagnóstico.
    - Se não houver informação suficiente → UNKNOWN.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from app.report_parser import Finding


# ---------------------------------------------------------------------------
# Classificações internas (estáveis, usadas em todo o código)
# ---------------------------------------------------------------------------
class RiskLevel(str, Enum):
    INCREASED = "INCREASED"
    MODERATE = "MODERATE"
    REDUCED = "REDUCED"
    NORMAL = "NORMAL"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Labels amigáveis para apresentação
# ---------------------------------------------------------------------------
RISK_LABELS: dict[str, str] = {
    RiskLevel.INCREASED.value: "Predisposição aumentada",
    RiskLevel.MODERATE.value: "Predisposição moderada",
    RiskLevel.REDUCED.value: "Predisposição reduzida",
    RiskLevel.NORMAL.value: "Sem alteração relevante",
    RiskLevel.UNKNOWN.value: "Não identificado",
}

# Ordenação para exibição (mais relevante primeiro)
RISK_ORDER: dict[str, int] = {
    RiskLevel.INCREASED.value: 0,
    RiskLevel.MODERATE.value: 1,
    RiskLevel.REDUCED.value: 2,
    RiskLevel.NORMAL.value: 3,
    RiskLevel.UNKNOWN.value: 4,
}

# ---------------------------------------------------------------------------
# Semântica visual — cores moderadas (sem alarmismo)
# ---------------------------------------------------------------------------
RISK_COLORS: dict[str, str] = {
    RiskLevel.INCREASED.value: "#B8860B",  # âmbar/dourado — atenção preventiva
    RiskLevel.MODERATE.value: "#2E86AB",  # azul médio — acompanhamento
    RiskLevel.REDUCED.value: "#6B8E47",  # verde-oliva — possível proteção
    RiskLevel.NORMAL.value: "#2E7D32",  # verde — dentro do esperado
    RiskLevel.UNKNOWN.value: "#7A8CA6",  # cinza-azulado — sem dado
}

RISK_BADGE_COLORS: dict[str, str] = {
    RiskLevel.INCREASED.value: "#FFF4E0",
    RiskLevel.MODERATE.value: "#E8F0FA",
    RiskLevel.REDUCED.value: "#F0F7E8",
    RiskLevel.NORMAL.value: "#E8F5E9",
    RiskLevel.UNKNOWN.value: "#F0F2F5",
}


# ---------------------------------------------------------------------------
# Mapeamento de nomenclaturas do PDF → classificações internas
# ---------------------------------------------------------------------------
# A ordem importa: entradas mais específicas vêm antes das genéricas.
_RISK_SYNONYMS: dict[str, tuple[str, ...]] = {
    RiskLevel.INCREASED.value: (
        "alto",
        "risco alto",
        "aumentado",
        "elevado",
        "aumentada",
        "alta",
        "risco aumentado",
        "predisposição aumentada",
        "susceptibilidade aumentada",
        "maior risco",
        "risco elevado",
        "predisposição elevada",
    ),
    RiskLevel.MODERATE.value: (
        "moderado",
        "moderada",
        "médio",
        "média",
        "risco moderado",
        "intermediário",
        "intermediária",
        "predisposição moderada",
    ),
    RiskLevel.REDUCED.value: (
        "baixo",
        "baixa",
        "reduzido",
        "reduzida",
        "risco reduzido",
        "menor risco",
        "risco baixo",
        "diminuído",
        "diminuída",
        "proteção",
        "protetor",
        "protetora",
        "predisposição reduzida",
    ),
    RiskLevel.NORMAL.value: (
        "sem alteração relevante",
        "normal",
        "sem alteração",
        "sem achado",
        "negativo",
        "não alterado",
        "não alterada",
        "dentro do esperado",
        "não há alteração",
        "sem variantes patogênicas",
        "sem variantes",
        "resultado normal",
    ),
    RiskLevel.UNKNOWN.value: (
        "não disponível",
        "indisponível",
        "não informado",
        "sem informação",
        "não relatado",
        "n/a",
        "não avaliado",
        "não identificado",
        "não determinado",
        "sem resultado",
    ),
}


def _normalize_text(value: str) -> str:
    """Remove acentos, converte para minúsculas e colapsa espaços."""
    text = unicodedata.normalize("NFD", value)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return " ".join(text.lower().split())


# Reverse lookup: texto normalizado (minúsculo, sem acento) → classificação
_NORMALIZED_TO_ID: dict[str, str] = {}
for _level_id, _synonyms in _RISK_SYNONYMS.items():
    for _syn in _synonyms:
        _NORMALIZED_TO_ID[_normalize_text(_syn)] = _level_id


# ---------------------------------------------------------------------------
# Estrutura de domínio: Risk
# ---------------------------------------------------------------------------
@dataclass
class Risk:
    """Um risco genético normalizado, pronto para exibição e RAG.

    Atributos
    ---------
    name : str
        Nome da condição/risco.
    category : str
        Categoria (ex.: Nutrição, Cardiovascular, Geral).
    level : str
        Classificação interna normalizada (INCREASED, MODERATE, ...).
    display_level : str
        Label amigável para apresentação.
    source_text : str
        Trecho original do relatório que fundamenta a classificação.
    description : str
        Descrição curta em linguagem simples.
    recommendations : list[str]
        Recomendações de prevenção (se houver).
    confidence : Optional[float]
        Confiança da classificação. Só é preenchido quando há justificativa
        técnica clara (ex.: correspondência exata de sinônimo). Caso
        contrário, permanece ``None``.
    ai_summary : Optional[str]
        Reservado para o futuro módulo de resumo automático.
    """

    name: str
    category: str
    level: str
    display_level: str
    source_text: str
    description: str = ""
    recommendations: list[str] = field(default_factory=list)
    confidence: Optional[float] = None
    ai_summary: Optional[str] = None

    @classmethod
    def from_finding(cls, finding: Finding) -> "Risk":
        """Converte um ``Finding`` do parser em um ``Risk`` normalizado."""
        level = normalize_risk_level(finding.risk_level)
        return cls(
            name=finding.condition,
            category=finding.category,
            level=level,
            display_level=RISK_LABELS.get(level, RISK_LABELS[RiskLevel.UNKNOWN.value]),
            source_text=finding.risk_level,
            description=finding.description,
            recommendations=list(finding.recommendations),
        )


# ---------------------------------------------------------------------------
# Compatibilidade: RiskCardData (mantido para não quebrar o dashboard)
# ---------------------------------------------------------------------------
@dataclass
class RiskCardData:
    """Dados normalizados prontos para exibição no RiskCard.

    Mantido para compatibilidade com o componente visual existente.
    """

    condition: str
    category: str
    risk_level_id: str  # identificador normalizado
    risk_display: str  # rótulo amigável
    description: str
    recommendations: list[str] = field(default_factory=list)
    ai_summary: Optional[str] = None  # preparado para resumo IA futuro

    @classmethod
    def from_finding(cls, finding: Finding) -> "RiskCardData":
        """Converte um ``Finding`` em dados prontos para exibição."""
        level_id = normalize_risk_level(finding.risk_level)
        return cls(
            condition=finding.condition,
            category=finding.category,
            risk_level_id=level_id,
            risk_display=RISK_LABELS.get(level_id, RISK_LABELS[RiskLevel.UNKNOWN.value]),
            description=finding.description,
            recommendations=list(finding.recommendations),
        )

    @classmethod
    def from_risk(cls, risk: Risk) -> "RiskCardData":
        """Converte um ``Risk`` em ``RiskCardData`` (compatibilidade)."""
        return cls(
            condition=risk.name,
            category=risk.category,
            risk_level_id=risk.level,
            risk_display=risk.display_level,
            description=risk.description,
            recommendations=list(risk.recommendations),
            ai_summary=risk.ai_summary,
        )


# ---------------------------------------------------------------------------
# Classificador central
# ---------------------------------------------------------------------------
class RiskClassifier:
    """Normaliza a classificação de riscos a partir do texto do relatório.

    Uso:
        classifier = RiskClassifier()
        level = classifier.classify("Risco aumentado")
        risk = classifier.build_risk(name="Diabetes", category="Geral",
                                     source_text="Nível de risco: Alto")
    """

    def __init__(self) -> None:
        self._synonym_map = dict(_NORMALIZED_TO_ID)

    def classify(self, raw_text: str) -> str:
        """Classifica um texto bruto em uma das classificações internas.

        Retorna sempre um dos valores de ``RiskLevel`` (nunca string vazia).
        """
        if not raw_text or not raw_text.strip():
            return RiskLevel.UNKNOWN.value

        normalized = _normalize_text(raw_text)
        if not normalized:
            return RiskLevel.UNKNOWN.value

        # Busca exata primeiro
        if normalized in self._synonym_map:
            return self._synonym_map[normalized]

        # Busca por substring (ex.: "risco aumentado para diabetes")
        for _syn, _level_id in self._synonym_map.items():
            if _syn in normalized:
                return _level_id

        return RiskLevel.UNKNOWN.value

    def display_label(self, level: str) -> str:
        """Retorna o label amigável para uma classificação interna."""
        return RISK_LABELS.get(level, RISK_LABELS[RiskLevel.UNKNOWN.value])

    def build_risk(
        self,
        *,
        name: str,
        category: str,
        source_text: str,
        description: str = "",
        recommendations: Optional[list[str]] = None,
    ) -> Risk:
        """Constrói um ``Risk`` normalizado a partir do texto do relatório.

        O ``source_text`` é preservado para explicabilidade e RAG.
        """
        level = self.classify(source_text)
        return Risk(
            name=name,
            category=category,
            level=level,
            display_level=self.display_label(level),
            source_text=source_text,
            description=description,
            recommendations=list(recommendations or []),
        )


# Instância singleton do classificador (reutilizada em todo o app)
_classifier = RiskClassifier()


# ---------------------------------------------------------------------------
# Funções de conveniência (mantidas para compatibilidade)
# ---------------------------------------------------------------------------
def normalize_risk_level(risk_level: str) -> str:
    """Converte a nomenclatura do PDF para uma classificação interna.

    Exemplos:
        "Alto" / "AUMENTADO" / "Risco elevado"  → "INCREASED"
        "Moderado" / "Médio"                    → "MODERATE"
        "Baixo" / "Reduzido"                    → "REDUCED"
        "Normal" / "Sem alteração"              → "NORMAL"
        "" (vazio) / "Não informado"            → "UNKNOWN"
    """
    return _classifier.classify(risk_level)


def risk_label(risk_level: str) -> str:
    """Retorna o label amigável para o usuário."""
    return _classifier.display_label(normalize_risk_level(risk_level))


def _resolve_level_id(value: str) -> str:
    """Resolve um valor para o ID normalizado.

    Aceita tanto o texto do PDF ("Alto", "Moderado") quanto o ID
    normalizado ("INCREASED", "MODERATE", ...).
    """
    if value in RISK_LABELS:
        return value
    return normalize_risk_level(value)


def risk_color(risk_level: str) -> str:
    """Cor semântica para o nível normalizado."""
    return RISK_COLORS.get(_resolve_level_id(risk_level), RISK_COLORS[RiskLevel.UNKNOWN.value])


def risk_badge_color(risk_level: str) -> str:
    """Cor de fundo do badge para o nível normalizado."""
    return RISK_BADGE_COLORS.get(_resolve_level_id(risk_level), RISK_BADGE_COLORS[RiskLevel.UNKNOWN.value])


def risk_short_description(risk_level: str) -> str:
    """Descrição curta e não alarmista para o nível de risco."""
    level_id = _resolve_level_id(risk_level)

    descriptions = {
        RiskLevel.INCREASED.value: (
            "Indica uma maior predisposição genética para a condição. "
            "Isso não é um diagnóstico e não significa que a condição "
            "vai se manifestar."
        ),
        RiskLevel.MODERATE.value: (
            "Indica uma predisposição intermediária. Acompanhamento "
            "preventivo e hábitos saudáveis podem fazer a diferença."
        ),
        RiskLevel.REDUCED.value: (
            "Indica uma predisposição menor que a média ou possível "
            "fator protetor. Isso não é uma garantia de que a condição "
            "nunca ocorrerá."
        ),
        RiskLevel.NORMAL.value: (
            "Nenhuma alteração relevante foi identificada para esta "
            "condição. Seguir os cuidados gerais de saúde é suficiente."
        ),
        RiskLevel.UNKNOWN.value: (
            "O relatório não fornece informação suficiente sobre esta "
            "condição. Consulte um profissional para esclarecimentos."
        ),
    }
    return descriptions.get(level_id, descriptions[RiskLevel.UNKNOWN.value])


def risk_icon(risk_level: str) -> str:
    """Ícone visual sutil para o nível de risco (sem alarmismo)."""
    level_id = _resolve_level_id(risk_level)

    icons = {
        RiskLevel.INCREASED.value: "◐",  # círculo parcialmente preenchido
        RiskLevel.MODERATE.value: "◑",
        RiskLevel.REDUCED.value: "◒",
        RiskLevel.NORMAL.value: "○",
        RiskLevel.UNKNOWN.value: "·",
    }
    return icons.get(level_id, "·")