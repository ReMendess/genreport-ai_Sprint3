"""Camada de transformação estruturada do relatório genético.

Extrai dados estruturados (paciente, achados, ancestralidade) a partir do
texto limpo do PDF, sem alterar o pipeline RAG existente.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

from app.parser_pdf import extract_text_from_pdf
from app.report_pipeline import resolve_report_pdf
from app.text_cleaner import clean_text

# Mapeamento dos níveis de risco para classificação amigável
# (mantido para compatibilidade; a normalização central está em risk_classifier)
RISK_CLASSIFICATION = {
    "alto": "Risco aumentado",
    "moderado": "Risco moderado",
    "baixo": "Sem alteração relevante",
}

RISK_ORDER = {"alto": 0, "moderado": 1, "baixo": 2}


@dataclass
class Finding:
    """Um achado/condição identificado no relatório."""

    condition: str
    risk_level: str  # valor original: Alto / Moderado / Baixo
    risk_class: str  # classificação amigável
    category: str
    description: str
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ParsedReport:
    """Estrutura completa dos dados extraídos do relatório."""

    patient_name: Optional[str] = None
    age: Optional[str] = None
    exam_date: Optional[str] = None
    findings: list[Finding] = field(default_factory=list)
    ancestry: list[dict] = field(default_factory=list)

    @property
    def has_ancestry(self) -> bool:
        return bool(self.ancestry)

    @property
    def high_risk_count(self) -> int:
        from app.risk_classifier import RiskLevel, normalize_risk_level

        return sum(
            1
            for f in self.findings
            if normalize_risk_level(f.risk_level) == RiskLevel.INCREASED.value
        )

    @property
    def moderate_risk_count(self) -> int:
        from app.risk_classifier import RiskLevel, normalize_risk_level

        return sum(
            1
            for f in self.findings
            if normalize_risk_level(f.risk_level) == RiskLevel.MODERATE.value
        )

    @property
    def no_relevant_change_count(self) -> int:
        from app.risk_classifier import RiskLevel, normalize_risk_level

        return sum(
            1
            for f in self.findings
            if normalize_risk_level(f.risk_level) == RiskLevel.NORMAL.value
        )

    @property
    def sorted_findings(self) -> list[Finding]:
        """Achados ordenados por severidade (Alto → Moderado → Baixo)."""
        return sorted(
            self.findings,
            key=lambda f: RISK_ORDER.get(f.risk_level.lower(), 99),
        )


def _normalize_risk(risk_level: str) -> str:
    return RISK_CLASSIFICATION.get(risk_level.strip().lower(), risk_level.strip())


def _extract_patient_info(text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    name_match = re.search(r"Paciente:\s*(.+)", text)
    age_match = re.search(r"Idade:\s*(\d+)\s*anos?", text)
    date_match = re.search(r"Data do exame:\s*(.+)", text)

    return (
        name_match.group(1).strip() if name_match else None,
        age_match.group(1) if age_match else None,
        date_match.group(1).strip() if date_match else None,
    )


def _extract_ancestry(text: str) -> list[dict]:
    """Extrai a composição genética estimada, se presente no relatório."""
    ancestry_block = re.search(
        r"Ancestralidade\s*\n(.*?)(?=\n\s*(?:Observações|$))",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if not ancestry_block:
        return []

    results: list[dict] = []
    for line in ancestry_block.group(1).splitlines():
        match = re.match(r"^\s*[-•*]?\s*([A-Za-zÀ-ÿ ]+?)\s*:\s*(\d+(?:[.,]\d+)?)\s*%", line)
        if match:
            origin = match.group(1).strip()
            percentage = float(match.group(2).replace(",", "."))
            results.append({"origin": origin, "percentage": percentage})

    return results


def _extract_findings(text: str) -> list[Finding]:
    """Extrai todas as condições/achados do relatório."""
    findings: list[Finding] = []
    # Divide o texto em blocos iniciados por "Condição:"
    blocks = re.split(r"(?=Condição:\s*)", text)

    for block in blocks:
        condition_match = re.search(r"Condição:\s*(.+)", block)
        if not condition_match:
            continue

        condition = condition_match.group(1).strip()

        risk_match = re.search(r"Nível de risco:\s*(.+)", block)
        risk_level = risk_match.group(1).strip() if risk_match else ""

        category_match = re.search(r"Seção:\s*(.+)", block)
        category = category_match.group(1).strip() if category_match else "Geral"

        description_match = re.search(
            r"Descrição:\s*\n(.*?)(?=\n\s*(?:Recomendações:|Condição:|Seção:|\Z))",
            block,
            re.DOTALL,
        )
        description = (
            " ".join(description_match.group(1).split()).strip()
            if description_match
            else ""
        )

        recommendations: list[str] = []
        rec_match = re.search(
            r"Recomendações:\s*\n(.*?)(?=\n\s*(?:Condição:|Seção:|\Z))",
            block,
            re.DOTALL,
        )
        if rec_match:
            recommendations = [
                re.sub(r"^\s*[-•*]\s*", "", line).strip()
                for line in rec_match.group(1).splitlines()
                if line.strip()
            ]

        findings.append(
            Finding(
                condition=condition,
                risk_level=risk_level,
                risk_class=_normalize_risk(risk_level),
                category=category,
                description=description,
                recommendations=recommendations,
            )
        )

    return findings


def parse_report(text: str) -> ParsedReport:
    """Transforma o texto limpo do relatório em dados estruturados."""
    patient_name, age, exam_date = _extract_patient_info(text)

    return ParsedReport(
        patient_name=patient_name,
        age=age,
        exam_date=exam_date,
        findings=_extract_findings(text),
        ancestry=_extract_ancestry(text),
    )


@lru_cache(maxsize=1)
def load_parsed_report() -> ParsedReport:
    """Carrega e estrutura o relatório atual sem reprocessar o índice RAG."""
    pdf_path = resolve_report_pdf()
    raw_text = extract_text_from_pdf(str(pdf_path))
    cleaned_text = clean_text(raw_text)
    return parse_report(cleaned_text)