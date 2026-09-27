import unittest
import uuid
from api.main import app


class TestPhase2RateLimiter(unittest.TestCase):
    """Pruebas de la Fase 2: Rate Limiting por IP para proteger Free Tier."""

    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        # Generar una IP única para aislar cada ejecución de prueba
        self.test_ip = f"198.51.{uuid.uuid4().int % 250}.{uuid.uuid4().int % 250}"

    def test_ai_endpoint_blocks_after_10_requests(self):
        """Endpoints pesados de IA permiten 10 requests y el 11 debe retornar 429."""
        statuses = []
        last_response = None

        for _ in range(11):
            response = self.client.post(
                "/api/download/markdown",
                json={"code": "x = 1"},
                headers={"X-Forwarded-For": self.test_ip},
            )
            statuses.append(response.status_code)
            last_response = response

        # El último request debe ser bloqueado por Rate Limiting
        self.assertEqual(last_response.status_code, 429)
        self.assertIn("Retry-After", last_response.headers)
        self.assertEqual(last_response.headers.get("X-RateLimit-Limit"), "10")
        self.assertEqual(last_response.headers.get("X-RateLimit-Remaining"), "0")

        data = last_response.get_json()
        self.assertEqual(data.get("codigo_error"), "RATE_LIMIT_EXCEEDED")
        self.assertIn("retry_after", data)

    def test_light_endpoint_allows_higher_capacity(self):
        """Endpoints ligeros (/api/preview-zip) tienen mayor capacidad (30 req/min)."""
        preview_ip = f"198.52.{uuid.uuid4().int % 250}.{uuid.uuid4().int % 250}"
        statuses = []

        # Realizar 15 peticiones (deben ser permitidas, a diferencia del límite de 10 de IA)
        for _ in range(15):
            res = self.client.post(
                "/api/preview-zip",
                headers={"X-Forwarded-For": preview_ip},
            )
            statuses.append(res.status_code)

        # Ninguno de los primeros 15 debe ser 429
        self.assertNotIn(429, statuses)


if __name__ == "__main__":
    unittest.main()
