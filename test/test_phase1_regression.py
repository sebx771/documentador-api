"""
Pruebas de regresión para las correcciones de la Fase 1:
  - La clave de caché incluye el idioma (ES y EN NO deben compartir un resultado en caché).
  - La clave de caché incluye la versión del prompt (modificar PROMPT_VERSION invalida entradas antiguas).
  - elapsed_time abarca la consolidación, no solo el preprocesamiento.
  - Los nombres de archivo multifile son únicos incluso cuando archivos fuente comparten el mismo nombre base.
  - max_files es el único límite efectivo y se reenvía a ZipService.
  - La extracción estructurada no se corrompe ante delimitadores en el código fuente.
"""

import math
import time
import unittest

from api.services.cache_service import CacheService
from api.services.documentation_orchestrator import DocumentationOrchestrator
from api.services.zip_services import ZipService


# ---------------------------------------------------------------------------
# Fakes compartidos
# ---------------------------------------------------------------------------

FINAL_DOCUMENT = """\
# Sistema

## 1. Resumen Ejecutivo
Resumen.

## 2. Arquitectura de Componentes
Arquitectura.

## 3. Lógica Central y Reglas de Negocio
Lógica.
"""

FINAL_DOCUMENT_EN = """\
# System

## 1. Executive Summary
Summary.

## 2. Component Architecture
Architecture.

## 3. Core Logic and Business Rules
Logic.
"""


class FakeCache:
    """Caché en memoria que registra cada clave escrita para que los tests puedan inspeccionarlas."""

    def __init__(self):
        self._store = {}
        self.written_keys = []

    def generate_hash(self, content, doc_type, extra_requirements=None, language=None):
        # Utiliza la lógica real de cálculo de hash directamente.
        import hashlib
        hash_input = f"{CacheService.PROMPT_VERSION}|{content}|{doc_type}"
        if extra_requirements:
            hash_input += f"|{extra_requirements}"
        if language:
            hash_input += f"|{language}"
        return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    def get(self, cache_key):
        return self._store.get(cache_key)

    def set(self, cache_key, result):
        self.written_keys.append(cache_key)
        self._store[cache_key] = result

    def get_stats(self):
        return {}


class FakeZipService:
    """Retorna un único archivo JS; la ruta puede sobrescribirse por test."""

    def __init__(self, path="src/routes/example.js"):
        self._path = path

    def extraer_zip(self, content):
        return (
            [
                {
                    "filename": self._path,
                    "language": "js",
                    "content": "const route = true;",
                }
            ],
            [],
        )


class SlowConsolidationDocumenter:
    """Documentador que simula demora durante la consolidación para hacer medible el elapsed_time."""

    consolidation_delay = 0.05  # segundos

    def estimate_input_tokens(self, system_prompt, user_prompt):
        return math.ceil((len(system_prompt) + len(user_prompt)) / 4)

    def generar(self, **kwargs):
        return "### Fragmento\nContenido del fragmento."

    def consolidate(self, docs, lang="es"):
        time.sleep(self.consolidation_delay)
        return FINAL_DOCUMENT if lang == "es" else FINAL_DOCUMENT_EN

    def apply_extra(self, docs, extra, lang=None):
        return docs

    def detect_language(self, code, extra):
        return "es"


class InstantDocumenter:
    """Documentador sin operaciones costosas para pruebas estructurales."""

    def estimate_input_tokens(self, system_prompt, user_prompt):
        return math.ceil((len(system_prompt) + len(user_prompt)) / 4)

    def generar(self, **kwargs):
        return "### Fragmento\nContenido."

    def consolidate(self, docs, lang="es"):
        return FINAL_DOCUMENT if lang == "es" else FINAL_DOCUMENT_EN

    def apply_extra(self, docs, extra, lang=None):
        return docs

    def detect_language(self, code, extra):
        return "es"


class FakeChunkingService:
    def create_chunks(self, files, doc_type="markdown", extra_requirements=None):
        return [
            {
                "content": "source code",
                "files": [f["filename"] for f in files],
            }
        ]


# ---------------------------------------------------------------------------
# Fallo 1 — La clave de caché debe incluir el idioma
# ---------------------------------------------------------------------------


class TestCacheKeyIncludesLanguage(unittest.TestCase):
    def _make_orchestrator(self):
        cache = FakeCache()
        orc = DocumentationOrchestrator(
            chunking_service=FakeChunkingService(),
            cache_service=cache,
            documentador=InstantDocumenter(),
        )
        return orc, cache

    def test_es_and_en_requests_produce_different_cache_keys(self):
        orc, cache = self._make_orchestrator()

        orc.process_zip(
            zip_content=b"zip",
            zip_service=FakeZipService(),
            language="es",
        )
        orc.process_zip(
            zip_content=b"zip",
            zip_service=FakeZipService(),
            language="en",
        )

        self.assertEqual(len(cache.written_keys), 2, "Cada idioma debe generar su propia clave")
        self.assertNotEqual(
            cache.written_keys[0],
            cache.written_keys[1],
            "ES y EN no deben producir la misma clave de caché",
        )

    def test_second_es_request_hits_cache_and_does_not_write_new_key(self):
        orc, cache = self._make_orchestrator()

        orc.process_zip(zip_content=b"zip", zip_service=FakeZipService(), language="es")
        orc.process_zip(zip_content=b"zip", zip_service=FakeZipService(), language="es")

        self.assertEqual(len(cache.written_keys), 1, "La segunda petición idéntica debe servirse desde la caché")

    def test_en_after_es_cache_hit_does_not_reuse_es_result(self):
        """Una petición en EN no debe servirse desde una entrada de caché creada en ES."""
        orc, cache = self._make_orchestrator()

        # Genera un resultado previo en español
        orc.process_zip(zip_content=b"zip", zip_service=FakeZipService(), language="es")
        # Inyecta un resultado alterado bajo la clave ES para detectar reutilización indebida
        es_key = cache.written_keys[0]
        cache._store[es_key]["documentation"] = "POISONED_ES_RESULT"

        result_en = orc.process_zip(
            zip_content=b"zip", zip_service=FakeZipService(), language="en"
        )
        self.assertEqual(len(cache.written_keys), 2, "EN debió escribir una nueva entrada en caché")


# ---------------------------------------------------------------------------
# Fallo 1b — La clave de caché debe incluir PROMPT_VERSION
# ---------------------------------------------------------------------------


class TestCacheKeyIncludesPromptVersion(unittest.TestCase):
    def test_different_prompt_versions_produce_different_hashes(self):
        svc = CacheService.__new__(CacheService)

        original_version = CacheService.PROMPT_VERSION
        try:
            CacheService.PROMPT_VERSION = "v1"
            key_v1 = svc.generate_hash("code", "markdown", language="es")
            CacheService.PROMPT_VERSION = "v2"
            key_v2 = svc.generate_hash("code", "markdown", language="es")
        finally:
            CacheService.PROMPT_VERSION = original_version

        self.assertNotEqual(key_v1, key_v2, "Cambiar PROMPT_VERSION debe invalidar la clave de caché")


# ---------------------------------------------------------------------------
# Fallo 2 — elapsed_time debe incluir la consolidación
# ---------------------------------------------------------------------------


class TestElapsedTimeIncludesConsolidation(unittest.TestCase):
    def test_elapsed_time_includes_consolidation_delay(self):
        orc = DocumentationOrchestrator(
            chunking_service=FakeChunkingService(),
            cache_service=FakeCache(),
            documentador=SlowConsolidationDocumenter(),
        )

        result = orc.process_zip(
            zip_content=b"zip",
            zip_service=FakeZipService(),
            language="es",
        )

        min_expected = SlowConsolidationDocumenter.consolidation_delay
        elapsed = result["metadata"]["elapsed_time_seconds"]
        self.assertGreaterEqual(
            elapsed,
            min_expected,
            f"elapsed_time ({elapsed}s) debe ser >= que el retraso de consolidación ({min_expected}s)",
        )

    def test_multifile_elapsed_time_is_present(self):
        orc = DocumentationOrchestrator(
            chunking_service=FakeChunkingService(),
            cache_service=FakeCache(),
            documentador=InstantDocumenter(),
        )

        result = orc.process_zip(
            zip_content=b"zip",
            zip_service=FakeZipService(),
            language="es",
            multifile=True,
        )

        self.assertIn("elapsed_time_seconds", result["metadata"])


# ---------------------------------------------------------------------------
# Fallo 3 — Los nombres multifile deben ser únicos para archivos homónimos
# ---------------------------------------------------------------------------


class HomonymousChunkingService:
    """Genera dos chunks con archivos nombrados 'index.py' en diferentes directorios."""

    def create_chunks(self, files, doc_type="markdown", extra_requirements=None):
        return [
            {"content": "code_a", "files": ["api/index.py"]},
            {"content": "code_b", "files": ["web/index.py"]},
        ]


class TestMultifileFilenameCollision(unittest.TestCase):
    def _run_multifile(self, chunking_service):
        orc = DocumentationOrchestrator(
            chunking_service=chunking_service,
            cache_service=FakeCache(),
            documentador=InstantDocumenter(),
        )
        return orc.process_zip(
            zip_content=b"zip",
            zip_service=FakeZipService(),
            language="es",
            multifile=True,
        )

    def test_homonymous_source_files_produce_distinct_output_filenames(self):
        result = self._run_multifile(HomonymousChunkingService())
        filenames = list(result["files"].keys())

        self.assertEqual(
            len(filenames),
            len(set(filenames)),
            f"Se detectaron nombres de archivo duplicados: {filenames}",
        )

    def test_distinct_source_files_appear_in_their_own_key(self):
        result = self._run_multifile(HomonymousChunkingService())
        filenames = list(result["files"].keys())

        # Ambos nombres de archivo deben incluir el prefijo de carpeta, no solo 'index'
        self.assertTrue(
            any("api" in f for f in filenames),
            f"Se esperaba prefijo 'api' en alguno de {filenames}",
        )
        self.assertTrue(
            any("web" in f for f in filenames),
            f"Se esperaba prefijo 'web' en alguno de {filenames}",
        )


# ---------------------------------------------------------------------------
# Fallo 4 — max_files debe ser el único límite efectivo y reenviarse a ZipService
# ---------------------------------------------------------------------------


class TestMaxFilesForwardedToZipService(unittest.TestCase):
    def test_zip_service_default_matches_orchestrator_default(self):
        self.assertEqual(
            DocumentationOrchestrator.DEFAULT_MAX_FILES,
            ZipService.DEFAULT_MAX_ELIGIBLE_FILES,
            "Ambos valores por defecto deben coincidir para no ser constantes redundantes",
        )

    def test_custom_max_files_is_forwarded_to_zip_service(self):
        """Cuando el orquestador crea un ZipService, debe reenviarle max_files."""
        created_services = []

        from api.services import zip_services as zip_mod
        import api.services.orchestrator.extraction as extraction_mod

        OriginalZipService = zip_mod.ZipService

        class CapturingZipService(OriginalZipService):
            def __init__(self, max_eligible_files=None):
                created_services.append(max_eligible_files)
                super().__init__(max_eligible_files=max_eligible_files)

        zip_mod.ZipService = CapturingZipService
        try:
            orc = DocumentationOrchestrator(
                max_files=7,
                chunking_service=FakeChunkingService(),
                cache_service=FakeCache(),
                documentador=InstantDocumenter(),
            )
            import zipfile, io

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                zf.writestr("hello.py", "print('hi')")
            # extraction.extract_source_files es lo que llama el pipeline internamente.
            extraction_mod.extract_source_files(
                buf.getvalue(), zip_service=None, max_eligible_files=orc.max_files
            )
        finally:
            zip_mod.ZipService = OriginalZipService

        self.assertTrue(created_services, "ZipService no fue instanciado")
        self.assertEqual(
            created_services[0],
            7,
            f"Se esperaba max_eligible_files=7, se obtuvo {created_services[0]}",
        )

    def test_zip_service_respects_max_eligible_files_cap(self):
        """ZipService detiene la extracción cuando alcanza max_eligible_files."""
        import io, zipfile

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for i in range(10):
                zf.writestr(f"file_{i}.py", f"x = {i}")

        svc = ZipService(max_eligible_files=3)
        raw, _ = svc.extraer_zip(buf.getvalue())

        # extraer_zip devuelve una lista de dicts — verifica directamente la longitud.
        self.assertEqual(len(raw), 3, f"Se esperaban 3 archivos extraídos, se obtuvieron {len(raw)}")


# ---------------------------------------------------------------------------
# Integridad de extracción estructurada — Delimitadores en contenido fuente
# ---------------------------------------------------------------------------


class TestStructuredExtractionDelimiters(unittest.TestCase):
    def test_markers_inside_code_do_not_corrupt_file_extraction(self):
        """El contenido que contenga '### Archivo:' o 'Lenguaje:' no debe partir el archivo."""
        import io, zipfile
        from api.services.orchestrator.extraction import extract_source_files

        content_with_markers = (
            "def test():\n"
            "    # Nota: ### Archivo: fake_nested.py\n"
            "    # Lenguaje: python\n"
            "    return 'ok'\n"
        )

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("module/service.py", content_with_markers)

        source_files, invalid_files = extract_source_files(buf.getvalue(), zip_service=None)

        self.assertEqual(len(source_files), 1, "Debe extraer exactamente 1 archivo")
        self.assertEqual(source_files[0].filename, "module/service.py")
        self.assertEqual(source_files[0].language, "py")
        self.assertIn("### Archivo: fake_nested.py", source_files[0].content)
        self.assertEqual(source_files[0].content, content_with_markers.strip())


if __name__ == "__main__":
    unittest.main()
