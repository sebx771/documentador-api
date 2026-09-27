import unittest
from api.main import app


class TestPhase1PayloadLimit(unittest.TestCase):
    """Pruebas de la Fase 1: Control de Tamaño de Carga y Manejo de Error 413."""

    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_payload_exceeding_limit_returns_413(self):
        """Peticiones mayores a 15 MB deben ser rechazadas con 413 y JSON estructurado."""
        payload_16mb = "a" * (16 * 1024 * 1024)
        response = self.client.post("/api/download/markdown", data=payload_16mb)

        self.assertEqual(response.status_code, 413)
        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data.get("codigo_error"), "PAYLOAD_TOO_LARGE")
        self.assertIn("15 MB", data.get("error", ""))

    def test_payload_within_limit_passes_413_check(self):
        """Peticiones menores a 15 MB deben superar la validación de tamaño (sin 413)."""
        response = self.client.post("/api/download/markdown", json={"code": ""})
        # Debe pasar el middleware de 413 (retornará 400 por código vacío, no 413)
        self.assertNotEqual(response.status_code, 413)


if __name__ == "__main__":
    unittest.main()
