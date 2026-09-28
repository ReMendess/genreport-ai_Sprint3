"""Testes do logging estruturado e da auditoria (governança Sprint 4).

Cobre:
    - Formatação JSON (válido, com trace_id e campos extras).
    - trace_id via contextvar.
    - Gravação de eventos de auditoria em audit.log.
    - PRIVACIDADE: auditoria nunca grava conteúdo do usuário.
    - Middleware: header X-Trace-ID presente nas respostas.
"""
import json
import logging
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.observability.audit import (  # noqa: E402
    FORBIDDEN_FIELDS,
    audit_chat_turn,
    fingerprint_hash,
    log_audit,
)
from app.observability.logging_config import (  # noqa: E402
    TRACE_ID_CTX,
    JsonFormatter,
    get_trace_id,
    new_trace_id,
    setup_logging,
)


class TestJsonFormatter(unittest.TestCase):
    """Testa a serialização JSON dos registros de log."""

    @staticmethod
    def _record(msg: str, extra: dict | None = None) -> logging.LogRecord:
        logger = logging.getLogger("teste.formatter")
        return logger.makeRecord(
            "teste.formatter", logging.INFO, "f", 1, msg, (), None, extra=extra or {}
        )

    def test_json_valido_com_campos_basicos(self):
        payload = json.loads(JsonFormatter().format(self._record("http_request")))
        self.assertEqual(payload["event"], "http_request")
        self.assertEqual(payload["level"], "INFO")
        self.assertEqual(payload["logger"], "teste.formatter")
        self.assertIn("ts", payload)

    def test_campos_extra_incluidos(self):
        record = self._record(
            "chat_turn", extra={"trace_id": "abc123", "status": "ok"}
        )
        payload = json.loads(JsonFormatter().format(record))
        self.assertEqual(payload["trace_id"], "abc123")
        self.assertEqual(payload["status"], "ok")

    def test_trace_id_vem_do_contextvar(self):
        token = TRACE_ID_CTX.set("ctx0001")
        try:
            payload = json.loads(JsonFormatter().format(self._record("x")))
            self.assertEqual(payload["trace_id"], "ctx0001")
        finally:
            TRACE_ID_CTX.reset(token)


class TestTraceId(unittest.TestCase):
    """Testa helpers de trace_id."""

    def test_novo_trace_id(self):
        trace_id = new_trace_id()
        self.assertEqual(len(trace_id), 12)
        self.assertRegex(trace_id, r"^[0-9a-f]+$")
        # Opaco: não carrega dado pessoal
        self.assertNotIn("@", trace_id)

    def test_get_trace_id_sem_contexto(self):
        self.assertIsNone(get_trace_id())


class TestAudit(unittest.TestCase):
    """Testa eventos de auditoria em audit.log."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aireport_audit_"))
        setup_logging(log_dir=self.tmp, force=True)

    def tearDown(self):
        for handler_group in (
            logging.getLogger().handlers,
            logging.getLogger("aireport.audit").handlers,
        ):
            for handler in list(handler_group):
                if getattr(handler, "_aireport", False):
                    handler_group.remove(handler)
                    handler.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _audit_events(self) -> list[dict]:
        path = self.tmp / "audit.log"
        if not path.exists():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_chat_turn_grava_json_com_trace(self):
        audit_chat_turn(
            trace_id="tid00001",
            status="ok",
            question_chars=10,
            answer_chars=20,
            n_sources=2,
            duration_ms=12.5,
            model="openai/gpt-oss-120b",
            conversation_turns=1,
        )
        events = self._audit_events()
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["event"], "chat_turn")
        self.assertEqual(event["trace_id"], "tid00001")
        self.assertEqual(event["question_chars"], 10)
        self.assertEqual(event["n_sources"], 2)
        self.assertEqual(event["model"], "openai/gpt-oss-120b")

    def test_auditoria_nunca_grava_conteudo_do_usuario(self):
        segredo = "SEGREDO-ULTRA-PRIVADO-XYZ"
        audit_chat_turn(
            trace_id="tid00002",
            status="ok",
            question_chars=len(segredo),
            answer_chars=7,
            n_sources=1,
            duration_ms=3.0,
            model="m",
        )
        raw = (self.tmp / "audit.log").read_text(encoding="utf-8")
        event = json.loads(raw.strip().splitlines()[-1])
        # Não existem campos de texto livre
        self.assertNotIn("question", event)
        self.assertNotIn("answer", event)
        self.assertNotIn("sources", event)
        # O conteúdo em si jamais aparece no arquivo
        self.assertNotIn(segredo, raw)

    def test_guard_rejeita_campos_proibidos(self):
        with self.assertRaises(ValueError):
            log_audit("chat_turn", question="conteúdo proibido")
        self.assertIn("question", FORBIDDEN_FIELDS)

    def test_fingerprint_hash_nao_expoe_caminho(self):
        digest = fingerprint_hash(r"C:\Users\Pessoa\relatorio.pdf")
        self.assertTrue(digest.startswith("sha256:"))
        self.assertNotIn("Pessoa", digest)
        self.assertLess(len(digest), 30)


class TestTraceMiddleware(unittest.TestCase):
    """Testa o middleware (header X-Trace-ID) via TestClient."""

    def test_health_retorna_header_trace(self):
        from fastapi.testclient import TestClient

        from api.main import app

        client = TestClient(app)
        response = client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        self.assertIn("x-trace-id", response.headers)
        self.assertRegex(response.headers["x-trace-id"], r"^[A-Za-z0-9_-]{8,64}$")
        self.assertEqual(response.json()["status"], "ok")

    def test_trace_id_do_cliente_e_respeitado(self):
        from fastapi.testclient import TestClient

        from api.main import app

        client = TestClient(app)
        response = client.get(
            "/api/v1/health", headers={"X-Trace-ID": "clienttrace01"}
        )
        self.assertEqual(response.headers["x-trace-id"], "clienttrace01")


if __name__ == "__main__":
    unittest.main()
