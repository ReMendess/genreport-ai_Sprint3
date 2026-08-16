"""Testes unitários para a camada de classificação de riscos genéticos.

Cobre os principais cenários:
    - Predisposição aumentada
    - Predisposição moderada
    - Predisposição reduzida
    - Resultado normal
    - Texto ambíguo
    - Ausência de classificação
"""
import sys
import unittest
from pathlib import Path

# Garante que o diretório raiz está no path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.risk_classifier import (
    RISK_BADGE_COLORS,
    RISK_COLORS,
    RISK_LABELS,
    Risk,
    RiskCardData,
    RiskClassifier,
    RiskLevel,
    normalize_risk_level,
    risk_badge_color,
    risk_color,
    risk_icon,
    risk_label,
    risk_short_description,
)


class TestRiskLevelEnum(unittest.TestCase):
    """Testa os valores estáveis do enum RiskLevel."""

    def test_enum_values(self):
        self.assertEqual(RiskLevel.INCREASED.value, "INCREASED")
        self.assertEqual(RiskLevel.MODERATE.value, "MODERATE")
        self.assertEqual(RiskLevel.REDUCED.value, "REDUCED")
        self.assertEqual(RiskLevel.NORMAL.value, "NORMAL")
        self.assertEqual(RiskLevel.UNKNOWN.value, "UNKNOWN")

    def test_labels(self):
        self.assertEqual(RISK_LABELS[RiskLevel.INCREASED.value], "Predisposição aumentada")
        self.assertEqual(RISK_LABELS[RiskLevel.MODERATE.value], "Predisposição moderada")
        self.assertEqual(RISK_LABELS[RiskLevel.REDUCED.value], "Predisposição reduzida")
        self.assertEqual(RISK_LABELS[RiskLevel.NORMAL.value], "Sem alteração relevante")
        self.assertEqual(RISK_LABELS[RiskLevel.UNKNOWN.value], "Não identificado")


class TestNormalizeRiskLevel(unittest.TestCase):
    """Testa a normalização de nomenclaturas do PDF."""

    def test_increased_synonyms(self):
        cases = [
            "Alto",
            "AUMENTADO",
            "Risco elevado",
            "Predisposição aumentada",
            "Risco alto",
            "Elevado",
            "Alta",
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(normalize_risk_level(case), RiskLevel.INCREASED.value)

    def test_moderate_synonyms(self):
        cases = [
            "Moderado",
            "Moderada",
            "Médio",
            "Média",
            "Risco moderado",
            "Intermediário",
            "Predisposição moderada",
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(normalize_risk_level(case), RiskLevel.MODERATE.value)

    def test_reduced_synonyms(self):
        cases = [
            "Baixo",
            "Baixa",
            "Reduzido",
            "Reduzida",
            "Risco reduzido",
            "Menor risco",
            "Risco baixo",
            "Predisposição reduzida",
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(normalize_risk_level(case), RiskLevel.REDUCED.value)

    def test_normal_synonyms(self):
        cases = [
            "Sem alteração relevante",
            "Normal",
            "Sem alteração",
            "Sem achado",
            "Negativo",
            "Dentro do esperado",
            "Resultado normal",
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(normalize_risk_level(case), RiskLevel.NORMAL.value)

    def test_unknown_synonyms(self):
        cases = [
            "Não disponível",
            "Indisponível",
            "Não informado",
            "Sem informação",
            "N/A",
            "Não avaliado",
            "Não identificado",
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(normalize_risk_level(case), RiskLevel.UNKNOWN.value)

    def test_empty_string(self):
        self.assertEqual(normalize_risk_level(""), RiskLevel.UNKNOWN.value)
        self.assertEqual(normalize_risk_level("   "), RiskLevel.UNKNOWN.value)
        self.assertEqual(normalize_risk_level(None), RiskLevel.UNKNOWN.value)

    def test_ambiguous_text(self):
        """Texto ambíguo sem correspondência clara → UNKNOWN."""
        self.assertEqual(normalize_risk_level("Resultado pendente de análise"), RiskLevel.UNKNOWN.value)
        self.assertEqual(normalize_risk_level("Verificar com médico"), RiskLevel.UNKNOWN.value)
        self.assertEqual(normalize_risk_level("Lorem ipsum dolor sit amet"), RiskLevel.UNKNOWN.value)

    def test_substring_matching(self):
        """Texto com contexto extra ainda deve ser classificado."""
        self.assertEqual(
            normalize_risk_level("Risco aumentado para diabetes tipo 2"),
            RiskLevel.INCREASED.value,
        )
        self.assertEqual(
            normalize_risk_level("Nível de risco: Moderado"),
            RiskLevel.MODERATE.value,
        )


class TestRiskClassifier(unittest.TestCase):
    """Testa a classe RiskClassifier."""

    def setUp(self):
        self.classifier = RiskClassifier()

    def test_classify(self):
        self.assertEqual(self.classifier.classify("Alto"), RiskLevel.INCREASED.value)
        self.assertEqual(self.classifier.classify("Moderado"), RiskLevel.MODERATE.value)
        self.assertEqual(self.classifier.classify("Baixo"), RiskLevel.REDUCED.value)
        self.assertEqual(self.classifier.classify("Normal"), RiskLevel.NORMAL.value)
        self.assertEqual(self.classifier.classify(""), RiskLevel.UNKNOWN.value)

    def test_display_label(self):
        self.assertEqual(
            self.classifier.display_label(RiskLevel.INCREASED.value),
            "Predisposição aumentada",
        )
        self.assertEqual(
            self.classifier.display_label(RiskLevel.UNKNOWN.value),
            "Não identificado",
        )

    def test_build_risk(self):
        risk = self.classifier.build_risk(
            name="Diabetes Tipo 2",
            category="Geral",
            source_text="Nível de risco: Alto",
            description="Predisposição aumentada para diabetes.",
            recommendations=["Acompanhar glicemia"],
        )
        self.assertEqual(risk.name, "Diabetes Tipo 2")
        self.assertEqual(risk.category, "Geral")
        self.assertEqual(risk.level, RiskLevel.INCREASED.value)
        self.assertEqual(risk.display_level, "Predisposição aumentada")
        self.assertEqual(risk.source_text, "Nível de risco: Alto")
        self.assertEqual(risk.description, "Predisposição aumentada para diabetes.")
        self.assertEqual(risk.recommendations, ["Acompanhar glicemia"])
        self.assertIsNone(risk.confidence)  # sem justificativa técnica → None


class TestRisk(unittest.TestCase):
    """Testa a estrutura de domínio Risk."""

    def test_risk_from_finding(self):
        from app.report_parser import Finding

        finding = Finding(
            condition="Obesidade",
            risk_level="Moderado",
            risk_class="",
            category="Cardiovascular",
            description="Predisposição moderada.",
            recommendations=["Manter dieta"],
        )
        risk = Risk.from_finding(finding)
        self.assertEqual(risk.name, "Obesidade")
        self.assertEqual(risk.category, "Cardiovascular")
        self.assertEqual(risk.level, RiskLevel.MODERATE.value)
        self.assertEqual(risk.display_level, "Predisposição moderada")
        self.assertEqual(risk.source_text, "Moderado")
        self.assertEqual(risk.recommendations, ["Manter dieta"])

    def test_risk_governance(self):
        """Nunca transformar predisposição em diagnóstico."""
        risk = Risk(
            name="Diabetes",
            category="Geral",
            level=RiskLevel.INCREASED.value,
            display_level="Predisposição aumentada",
            source_text="Predisposição aumentada",
        )
        # O display_level deve dizer "predisposição", nunca "você tem"
        self.assertNotIn("você tem", risk.display_level.lower())
        self.assertNotIn("diagnóstico", risk.display_level.lower())
        self.assertIn("predisposição", risk.display_level.lower())


class TestRiskCardData(unittest.TestCase):
    """Testa a compatibilidade com o componente visual."""

    def test_from_finding(self):
        from app.report_parser import Finding

        finding = Finding(
            condition="Insônia",
            risk_level="Baixo",
            risk_class="",
            category="Nutrição",
            description="Predisposição reduzida.",
        )
        card = RiskCardData.from_finding(finding)
        self.assertEqual(card.condition, "Insônia")
        self.assertEqual(card.risk_level_id, RiskLevel.REDUCED.value)
        self.assertEqual(card.risk_display, "Predisposição reduzida")

    def test_from_risk(self):
        risk = Risk(
            name="Hipertensão",
            category="Geral",
            level=RiskLevel.MODERATE.value,
            display_level="Predisposição moderada",
            source_text="Moderado",
        )
        card = RiskCardData.from_risk(risk)
        self.assertEqual(card.condition, "Hipertensão")
        self.assertEqual(card.risk_level_id, RiskLevel.MODERATE.value)
        self.assertEqual(card.risk_display, "Predisposição moderada")


class TestVisualHelpers(unittest.TestCase):
    """Testa helpers visuais (cores, ícones, descrições)."""

    def test_risk_color(self):
        self.assertEqual(risk_color("Alto"), RISK_COLORS[RiskLevel.INCREASED.value])
        self.assertEqual(risk_color("Moderado"), RISK_COLORS[RiskLevel.MODERATE.value])
        self.assertEqual(risk_color("Baixo"), RISK_COLORS[RiskLevel.REDUCED.value])
        self.assertEqual(risk_color("Normal"), RISK_COLORS[RiskLevel.NORMAL.value])
        self.assertEqual(risk_color(""), RISK_COLORS[RiskLevel.UNKNOWN.value])

    def test_risk_badge_color(self):
        self.assertEqual(risk_badge_color("Alto"), RISK_BADGE_COLORS[RiskLevel.INCREASED.value])
        self.assertEqual(risk_badge_color(""), RISK_BADGE_COLORS[RiskLevel.UNKNOWN.value])

    def test_risk_icon(self):
        self.assertEqual(risk_icon("Alto"), "◐")
        self.assertEqual(risk_icon("Moderado"), "◑")
        self.assertEqual(risk_icon("Baixo"), "◒")
        self.assertEqual(risk_icon("Normal"), "○")
        self.assertEqual(risk_icon(""), "·")

    def test_risk_short_description(self):
        desc = risk_short_description("Alto")
        self.assertIn("predisposição", desc.lower())
        # Não deve usar linguagem alarmista ("você tem a doença")
        self.assertNotIn("você tem", desc.lower())
        # Pode mencionar "diagnóstico" de forma negativa ("não é um diagnóstico")
        self.assertIn("não é um diagnóstico", desc.lower())

        desc_unknown = risk_short_description("")
        self.assertIn("não fornece", desc_unknown.lower())


if __name__ == "__main__":
    unittest.main()