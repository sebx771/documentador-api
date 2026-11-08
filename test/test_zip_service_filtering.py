import io
import unittest
import zipfile

from api.services.zip_services import ZipService


class TestZipServicePathFiltering(unittest.TestCase):
    def setUp(self):
        self.service = ZipService()

    def _make_zip(self, files):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for path, content in files.items():
                archive.writestr(path, content)
        return buffer.getvalue()

    def test_extract_keeps_routes_and_ignores_excluded_directories(self):
        zip_content = self._make_zip(
            {
                "project/backend/src/routes/authRoutes.js": "const route = true;",
                "project/backend/src/controllers/userController.js": "const user = true;",
                "project/backend/node_modules/pkg/index.js": "const ignored = true;",
                "project/backend/out/generated.js": "const ignored = true;",
                "project/backend/build/generated.js": "const ignored = true;",
            }
        )

        extracted, invalid_files = self.service.extraer_zip(zip_content)
        extracted_filenames = [item["filename"] for item in extracted]

        self.assertEqual(invalid_files, [])
        self.assertIn("project/backend/src/routes/authRoutes.js", extracted_filenames)
        self.assertIn("project/backend/src/controllers/userController.js", extracted_filenames)
        self.assertTrue(all("node_modules" not in fn for fn in extracted_filenames))
        self.assertTrue(all("generated.js" not in fn for fn in extracted_filenames))

    def test_preview_uses_the_same_path_filtering_as_extraction(self):
        zip_content = self._make_zip(
            {
                "project/backend/src/routes/authRoutes.js": "const route = true;",
                "project/backend/node_modules/pkg/index.js": "const ignored = true;",
                "project/backend/out/generated.js": "const ignored = true;",
                "project/backend/build/generated.js": "const ignored = true;",
            }
        )

        preview = self.service.listar_contenido_zip(zip_content)
        filenames = [entry["file"] for entry in preview]

        self.assertEqual(filenames, ["project/backend/src/routes/authRoutes.js"])


if __name__ == "__main__":
    unittest.main()
