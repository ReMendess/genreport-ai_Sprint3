"""Testes do harness de avaliação (Etapa 5 — Sprint 4).

Cobre (SEM rede — ask_question mockado):
    - Estrutura do set dorado real (data/eval/questions.json).
    - Cálculo de aderência, consistência, groundedness e violações.
    - Renderização Markdown da evidência.
"""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.evaluation.harness import (  # noqa: E402
    clarity_stats,
    evaluate,
    load_golden_set,
    render_markdown,
)

GOLDEN_PATH = Path(__file__).resolve().parent.parent / "data" / "eval" / "questions.json"


class TestGoldenSet(unittest.TestCase):
    """Valida o set dorado real (arquivo versionado)."""

    @classmethod
    def setUpClass(cls):
        cls.meta, cls.questions = load_golden_set(GOLDEN_PATH)

    def test_carrega_com_minimo_de_perguntas(self):
        self.assertGreaterEqual(len(self.questions), 15)

    def test_ids_unicos(self):
        ids = [q.id for q in self.questions]
        self.assertEqual(len(ids), len(set(ids)))

    def test_categorias_conhecidas(self):
        allowed = {"dominio", "dado_ausente", "fora_do_tema", "injecao", "limite"}
        for q in self.questions:
            self.assertIn(q.category, allowed, q.id)

    def test_refusas_tem_motivo(self):
        for q in self.questions:
            if q.expect_refused:
                self.assertIsNotNone(q.expect_reason, q.id)

    def test_sem_dados_pessoais(self):
        # Set dorado não pode conter o nome do paciente
        from app.validation.text_utils import normalize

        blob = normalize(" ".join(q.question for q in self.questions))
        self.assertNotIn("renan", blob)

    def test_json_bom_friendly(self):
        raw = GOLDEN_PATH.read_bytes()
        self.assertFalse(raw[:3] == b"\xef\xbb\xbf", "JSON não deve ter BOM")
        json.loads(raw.decode("utf-8"))


class TestClarity(unittest.TestCase):
    def test_frases_curtas(self):
        stats = clarity_stats("O risco é alto. Faça prevenção. Consulte o médico.")
        self.assertEqual(stats["sentences"], 3)
        self.assertLess(stats["avg_words_per_sentence"], 10)
        self.assertEqual(stats["long_sentences"], 0)

    def test_aviso_de_groundedness_ignorado(self):
        stats = clarity_stats(
            "Frase curta.\n\nObservação: parte desta resposta não foi localizada "
            "textualmente no trecho consultado do seu relatório."
        )
        self.assertEqual(stats["sentences"], 1)


NEGRINHA = {
    "id": "dom-01",
    "category": "dominio",
    "question": "Quais são meus riscos?",
    "expect": {"refused": False},
    "rationale": "x",
}


@mock.patch("app.evaluation.harness.ask_question")
class TestEvaluate(unittest.TestCase):
    """evaluate() com ask_question mockado (sem rede)."""

    @staticmethod
    def _golden():
        _, questions = load_golden_set(GOLDEN_PATH)
        return questions[:2]  # dom-01 e dom-02 (ambos: responder)

    @staticmethod
    def _ok_answer(text="O relatório indica predisposição aumentada para diabetes."):
        return {
            "answer": text,
            "sources": "chunk a\n\nchunk b",
            "refused": False,
            "refusal_reason": None,
            "groundedness": 0.8,
        }

    def test_tudo_certo_aprovado(self, ask):
        ask.return_value = self._ok_answer()
        report = evaluate(None, self._golden(), runs=2)
        self.assertEqual(report["summary"]["behavior_accuracy"], 1.0)
        self.assertEqual(report["summary"]["consistency_rate"], 1.0)
        self.assertEqual(report["summary"]["policy_violations"], 0)
        self.assertEqual(report["verdict"]["status"], "APROVADO")
        self.assertEqual(report["summary"]["groundedness_mean"], 0.8)

    def test_recusa_ineperada_vira_falha(self, ask):
        # Pergunta de domínio recusada inesperadamente → acurácia < 1
        ask.return_value = {
            "answer": "Não encontrei essa informação no seu relatório.",
            "sources": "",
            "refused": True,
            "refusal_reason": "no_context",
            "groundedness": None,
        }
        report = evaluate(None, self._golden(), runs=1)
        self.assertEqual(report["summary"]["behavior_accuracy"], 0.0)
        self.assertEqual(len(report["summary"]["failures"]), 2)
        self.assertEqual(report["verdict"]["status"], "APROVADO COM RESSALVAS")

    def test_inconsistencia_de_decisao_detectada(self, ask):
        # Consistência = MESMA decisão (recusa/resposta + motivo) entre execuções.
        recusa = {
            "answer": "Não encontrei essa informação no seu relatório.",
            "sources": "",
            "refused": True,
            "refusal_reason": "no_context",
            "groundedness": None,
        }
        ask.side_effect = [
            self._ok_answer(),  # Q1 run1: responde
            recusa,  # Q1 run2: recusa (mudou!)
            self._ok_answer(),  # Q2 run1
            recusa,  # Q2 run2 (mudou!)
        ]
        report = evaluate(None, self._golden(), runs=2)
        self.assertEqual(report["summary"]["consistency_rate"], 0.0)

    def test_jaccard_mede_estabilidade_textual(self, ask):
        # Respostas com vocabulários diferentes entre execuções → Jaccard < 1
        ask.side_effect = [
            self._ok_answer("Predisposição aumentada para diabetes e risco cardiovascular."),
            self._ok_answer("Composição ancestral europeia e africana no relatório."),
            self._ok_answer("Predisposição aumentada para diabetes e risco cardiovascular."),
            self._ok_answer("Composição ancestral europeia e africana no relatório."),
        ]
        report = evaluate(None, self._golden(), runs=2)
        self.assertIsNotNone(report["summary"]["jaccard_mean"])
        self.assertLess(report["summary"]["jaccard_mean"], 1.0)

    def test_violacao_de_politica_contada(self, ask):
        ask.return_value = {
            "answer": "Voce tem diabetes tipo 2.",
            "sources": "chunk",
            "refused": False,
            "refusal_reason": None,
            "groundedness": 0.8,
        }
        report = evaluate(None, self._golden(), runs=1)
        self.assertEqual(report["summary"]["policy_violations"], 2)
        self.assertEqual(report["verdict"]["status"], "APROVADO COM RESSALVAS")

    def test_redator_aplicado_nas_respostas(self, ask):
        ask.return_value = self._ok_answer(text="Olá Renan, seu risco é alto.")
        redactor = lambda t: t.replace("Renan", "R***")  # noqa: E731
        report = evaluate(None, self._golden(), runs=1, redactor=redactor)
        for result in report["results"]:
            self.assertNotIn("Renan", result["runs"][0]["answer"])
            self.assertIn("R***", result["runs"][0]["answer"])

    def test_markdown_contem_secoes(self, ask):
        ask.return_value = self._ok_answer()
        report = evaluate(None, self._golden(), runs=1)
        md = render_markdown(report, golden_meta={"version": "1.0"})
        for heading in (
            "# Evidência de Avaliação",
            "## 1. Metodologia",
            "## 2. Resultados gerais",
            "## 4. Resultado por pergunta",
            "## 5. Exemplos anotados",
            "## 7. Limitações",
        ):
            self.assertIn(heading, md)
        self.assertIn("APROVADO", md)

    def test_limit_respeitado(self, ask):
        ask.return_value = self._ok_answer()
        report = evaluate(None, self._golden(), runs=1, limit=1)
        self.assertEqual(report["meta"]["n_questions"], 1)


if __name__ == "__main__":
    unittest.main()
