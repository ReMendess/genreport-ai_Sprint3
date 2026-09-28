"""Testes da governança LGPD (Etapa 3 — Sprint 4).

Cobre:
    - Política: versão, retenção configurável, expurgo de logs, mascaramento.
    - Consentimento: registro, revogação, persistência, ausência de PII.
    - Endpoints de consentimento (GET/POST) e gate do chat (403).
"""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.governance.consent import ConsentRegistry, get_registry  # noqa: E402
from app.governance.policy import (  # noqa: E402
    DATA_INVENTORY,
    POLICY_VERSION,
    consent_required,
    log_retention_days,
    mask_name,
    purge_expired_logs,
)


class TestPolicy(unittest.TestCase):
    """Testa a política de governança e retenção."""

    def test_policy_version_formatada(self):
        self.assertRegex(POLICY_VERSION, r"^\d+\.\d+")

    def test_retention_padrao_30(self):
        old = os.environ.pop("LOG_RETENTION_DAYS", None)
        try:
            self.assertEqual(log_retention_days(), 30)
        finally:
            if old is not None:
                os.environ["LOG_RETENTION_DAYS"] = old

    def test_retention_configuravel(self):
        os.environ["LOG_RETENTION_DAYS"] = "7"
        try:
            self.assertEqual(log_retention_days(), 7)
        finally:
            del os.environ["LOG_RETENTION_DAYS"]

    def test_retention_invalida_usa_padrao(self):
        os.environ["LOG_RETENTION_DAYS"] = "abc"
        try:
            self.assertEqual(log_retention_days(), 30)
        finally:
            del os.environ["LOG_RETENTION_DAYS"]

    def test_expurga_somente_logs_expirados(self):
        tmp = Path(tempfile.mkdtemp(prefix="purge_"))
        try:
            expirado = tmp / "antigo.log"
            recente = tmp / "novo.log"
            outro = tmp / "nao_log.py"
            for f in (expirado, recente, outro):
                f.write_text("x", encoding="utf-8")
            antigo_ts = time.time() - (60 * 86400)  # 60 dias
            os.utime(expirado, (antigo_ts, antigo_ts))

            removed = purge_expired_logs(log_dir=tmp, retention_days=30)

            self.assertEqual(removed, ["antigo.log"])
            self.assertFalse(expirado.exists())
            self.assertTrue(recente.exists())
            self.assertTrue(outro.exists())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_expurga_dir_inexistente_segura(self):
        self.assertEqual(purge_expired_logs(log_dir=Path("nao_existe_xyz")), [])

    def test_mask_name_esconde_nome_completo(self):
        completo = "Renan de Oliveira Mendes"
        mascarado = mask_name(completo)
        self.assertNotIn("Renan", mascarado)
        self.assertNotIn("Oliveira", mascarado)
        self.assertIn("***", mascarado)

    def test_inventario_completo(self):
        self.assertGreaterEqual(len(DATA_INVENTORY), 5)
        obrigatorias = {"data", "where", "retention", "legal_basis"}
        for item in DATA_INVENTORY:
            self.assertTrue(obrigatorias.issubset(item.keys()))


class TestConsent(unittest.TestCase):
    """Testa o registro de consentimento (sem PII)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="consent_"))
        self.arquivo = self.tmp / "consent.json"
        self.registry = ConsentRegistry(path=self.arquivo)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_inicial_nao_concedido(self):
        self.assertFalse(self.registry.is_granted())

    def test_registrar_consentimento(self):
        state = self.registry.record(True, source="test")
        self.assertTrue(self.registry.is_granted())
        self.assertEqual(state["policy_version"], POLICY_VERSION)
        self.assertIsNotNone(state["granted_at"])

    def test_persistencia_round_trip(self):
        self.registry.record(True, source="test")
        novo = ConsentRegistry(path=self.arquivo)
        self.assertTrue(novo.is_granted())
        self.assertEqual(novo.status()["source"], "test")

    def test_revogar_consentimento(self):
        self.registry.record(True, source="test")
        self.registry.record(False)
        self.assertFalse(self.registry.is_granted())
        self.assertIsNone(self.registry.status()["policy_version"])

    def test_registro_nao_contem_pii(self):
        self.registry.record(True, source="test")
        dados = json.loads(self.arquivo.read_text(encoding="utf-8"))
        permitidas = {"granted", "policy_version", "granted_at", "source"}
        self.assertTrue(set(dados.keys()) <= permitidas)

    def test_consent_required_padrao_false(self):
        old = os.environ.pop("REQUIRE_CONSENT", None)
        try:
            self.assertFalse(consent_required())
        finally:
            if old is not None:
                os.environ["REQUIRE_CONSENT"] = old

    def test_consent_required_env_true(self):
        os.environ["REQUIRE_CONSENT"] = "true"
        try:
            self.assertTrue(consent_required())
        finally:
            del os.environ["REQUIRE_CONSENT"]


class TestConsentEndpoints(unittest.TestCase):
    """Testa GET/POST /api/v1/consent e o gate do chat via TestClient."""

    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        from api.main import app

        cls.client = TestClient(app)
        cls.registry = get_registry()
        cls._estado_inicial = cls.registry.status()

    @classmethod
    def tearDownClass(cls):
        # Restaura o estado de consentimento original (demo sem resíduo)
        cls.registry.record(
            granted=bool(cls._estado_inicial.get("granted")),
            policy_version=cls._estado_inicial.get("policy_version"),
            source="test",
        )

    def test_get_consent_status(self):
        response = self.client.get("/api/v1/consent")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("required", body)
        self.assertIn("granted", body)
        self.assertIn("current_policy_version", body)
        self.assertEqual(body["current_policy_version"], POLICY_VERSION)

    def test_post_consent_e_revogacao(self):
        ok = self.client.post("/api/v1/consent", json={"granted": True})
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.json()["granted"])

        revogado = self.client.post("/api/v1/consent", json={"granted": False})
        self.assertEqual(revogado.status_code, 200)
        self.assertFalse(revogado.json()["granted"])

    def test_chat_retorna_403_sem_consentimento_quando_exigido(self):
        estado = self.registry.status()
        self.registry.clear()
        os.environ["REQUIRE_CONSENT"] = "true"
        try:
            response = self.client.post("/api/v1/chat", json={"question": "teste"})
            self.assertEqual(response.status_code, 403)
            self.assertIn("consentimento", response.json()["detail"].lower())
        finally:
            del os.environ["REQUIRE_CONSENT"]
            if estado.get("granted"):
                self.registry.record(True, policy_version=estado.get("policy_version"))


if __name__ == "__main__":
    unittest.main()
