import unittest
from api.main import app, API_VERSION


class TestPhase4Integration(unittest.TestCase):
    """Pruebas de la Fase 4: Integración y End-to-End de Seguridad y Endpoints."""

    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_welcome_endpoint_version(self):
        """Verifica que el endpoint raíz '/' exponga la versión correcta actualizada."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get("version"), API_VERSION)
        self.assertEqual(data.get("version"), "3.3.0")

    def test_custom_error_handlers(self):
        """Verifica el formato JSON estándar en errores 404 y 405."""
        # 404
        res_404 = self.client.get("/api/endpoint-inexistente")
        self.assertEqual(res_404.status_code, 404)
        self.assertEqual(res_404.get_json().get("codigo_error"), "NOT_FOUND")

        # 405
        res_405 = self.client.delete("/api/download")
        self.assertEqual(res_405.status_code, 405)
        self.assertEqual(res_405.get_json().get("codigo_error"), "METHOD_NOT_ALLOWED")

    def test_download_info_endpoint(self):
        """Verifica que la documentación de descarga responda con éxito."""
        response = self.client.get("/api/download")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
