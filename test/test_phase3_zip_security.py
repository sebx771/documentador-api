import io
import unittest
import zipfile
from api.main import app


class TestPhase3ZipSecurity(unittest.TestCase):
    """Pruebas de la Fase 3: Validación segura de ZIPs (Anti-ZIP-Bomb y Path Traversal)."""

    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_valid_zip_accepted(self):
        """Un archivo ZIP legítimo debe procesarse correctamente."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("app.py", "print('hello')")
        buf.seek(0)

        response = self.client.post(
            "/api/preview-zip",
            data={"file": (buf, "valid.zip")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["file"], "app.py")

    def test_path_traversal_blocked(self):
        """Un archivo ZIP con rutas relativas peligrosas ('../') debe ser rechazado."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("../etc/passwd.py", "malicious_content")
        buf.seek(0)

        response = self.client.post(
            "/api/preview-zip",
            data={"file": (buf, "traversal.zip")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data.get("codigo_error"), "VALIDATION_ERROR")
        self.assertIn("Ruta de archivo no permitida", data.get("error", ""))

    def test_excessive_files_count_blocked(self):
        """Un archivo ZIP con más de 300 archivos debe ser rechazado."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for i in range(305):
                zf.writestr(f"file_{i}.py", "x = 1")
        buf.seek(0)

        response = self.client.post(
            "/api/preview-zip",
            data={"file": (buf, "many_files.zip")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data.get("codigo_error"), "VALIDATION_ERROR")
        self.assertIn("demasiados archivos", data.get("error", ""))

    def test_zip_bomb_uncompressed_size_blocked(self):
        """Un archivo ZIP cuyo contenido descomprimido supere 40 MB debe ser rechazado."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # 45 MB comprimidos a unos pocos kilobytes
            zf.writestr("large.py", " " * (45 * 1024 * 1024))
        buf.seek(0)

        response = self.client.post(
            "/api/preview-zip",
            data={"file": (buf, "bomb.zip")},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data.get("codigo_error"), "VALIDATION_ERROR")
        self.assertIn("límite de seguridad permitido", data.get("error", ""))


if __name__ == "__main__":
    unittest.main()
