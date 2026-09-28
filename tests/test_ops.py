"""Testes de operação (Etapa 6 — Sprint 4).

Cobre:
    - Métricas: contadores, latências, p95, reset, snapshot.
    - is_cache_valid: fingerprint inválido → False.
    - Endpoints /status e /metrics (TestClient).
    - collect_health: saudável + PDF ausente (erro tipificado).
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.observability import metrics  # noqa: E402
from scripts.monitor import collect_health  # noqa: E402


class TestMetrics(unittest.TestCase):
    def setUp(self):
        metrics.reset()

    def test_record_request_atualiza_contadores(self):
        metrics.record_request("/api/v1/health", "GET", 200, 5.0)
        metrics.record_request("/api/v1/chat", "POST", 200, 1000.0)
        metrics.record_request("/api/v1/chat", "POST", 403, 1.0)
        metrics.record_request("/api/v1/x", "GET", 500, 10.0)
        snap = metrics.snapshot()
        self.assertEqual(snap["http"]["requests_total"], 4)
        self.assertEqual(snap["http"]["by_status"], {"200": 2, "403": 1, "500": 1})
        self.assertEqual(snap["http"]["errors_client_total"], 1)
        self.assertEqual(snap["http"]["errors_server_total"], 1)

    def test_latencias_e_p95(self):
        for ms in (10.0, 20.0, 30.0, 40.0, 50.0):
            metrics.record_request("/api/v1/health", "GET", 200, ms)
        stats = metrics.snapshot()["http"]["by_path"]["/api/v1/health"]
        self.assertEqual(stats["count"], 5)
        self.assertEqual(stats["avg_ms"], 30.0)
        self.assertEqual(stats["min_ms"], 10.0)
        self.assertEqual(stats["max_ms"], 50.0)
        self.assertEqual(stats["p95_ms"], 50.0)

    def test_record_chat_refusas(self):
        metrics.record_chat(
            status="ok", refused=True, refusal_reason="no_context",
            groundedness=None, duration_ms=10.0,
        )
        metrics.record_chat(
            status="ok", refused=False, refusal_reason=None,
            groundedness=0.5, duration_ms=20.0,
        )
        metrics.record_chat(
            status="ok", refused=False, refusal_reason=None,
            groundedness=0.7, duration_ms=30.0,
        )
        chat = metrics.snapshot()["chat"]
        self.assertEqual(chat["turns_total"], 3)
        self.assertEqual(chat["refusals_total"], 1)
        self.assertEqual(chat["refusals_by_reason"], {"no_context": 1})
        self.assertEqual(chat["groundedness_avg"], 0.6)
        self.assertEqual(chat["avg_duration_ms"], 20.0)

    def test_snapshot_estrutura(self):
        snap = metrics.snapshot()
        for key in ("started_at", "uptime_seconds", "http", "chat"):
            self.assertIn(key, snap)
        self.assertIn("by_path", snap["http"])


class TestCacheValid(unittest.TestCase):
    def test_fingerprint_invalido_retorna_false(self):
        from app.vector_store import is_cache_valid

        self.assertFalse(is_cache_valid("fingerprint:inexistente:0"))

    def test_fingerprint_atual_retorna_bool(self):
        from app.report_pipeline import file_fingerprint, resolve_report_pdf
        from app.vector_store import is_cache_valid

        self.assertIsInstance(is_cache_valid(file_fingerprint(resolve_report_pdf())), bool)


class TestStatusEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        from api.main import app

        cls.client = TestClient(app)

    def test_status_ok(self):
        response = self.client.get("/api/v1/status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn(body["status"], {"ok", "degraded", "error"})
        self.assertTrue(body["report"]["found"])
        self.assertIn(body["index"]["valid"], {True, False})
        self.assertIn("consent", body)
        self.assertIn("logging", body)
        # Não expõe caminho completo do paciente
        self.assertNotIn("Pichau", response.text)

    def test_metrics_ok(self):
        self.client.get("/api/v1/health")
        response = self.client.get("/api/v1/metrics")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("http", body)
        self.assertIn("chat", body)
        # health requisitado acima já contabilizado (ou a própria chamada anterior)
        self.assertGreaterEqual(body["http"]["requests_total"], 1)


class TestCollectHealth(unittest.TestCase):
    def test_saude_do_repositorio(self):
        health = collect_health()
        self.assertTrue(health["healthy"], health["checks"])
        ids = [c["id"] for c in health["checks"]]
        self.assertEqual(ids, ["report_pdf", "index_cache", "logs"])
        self.assertIn("consent", health["info"])

    def test_pdf_ausente_falha_tipificada(self):
        # Simula diretório sem PDF (erro tipificado, sem tocar no PDF real)
        with mock.patch(
            "app.report_pipeline.RAW_DATA_DIR", Path("diretorio_inexistente_xyz")
        ):
            health = collect_health()
        self.assertFalse(health["healthy"])
        pdf_check = health["checks"][0]
        self.assertEqual(pdf_check["id"], "report_pdf")
        self.assertFalse(pdf_check["ok"])
        self.assertEqual(pdf_check["detail"], "ReportNotFoundError")


if __name__ == "__main__":
    unittest.main()
