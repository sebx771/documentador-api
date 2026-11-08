import math
import unittest
from types import SimpleNamespace

from api.services.ai.ai_service import DocumentadorIA
from api.services.ai.models import models
from api.services.documentation_orchestrator import DocumentationOrchestrator


FINAL_DOCUMENT = """# Sistema de estacionamiento

## 1. Resumen Ejecutivo
Gestiona las operaciones de estacionamiento descritas en las fuentes.

## 2. Arquitectura de Componentes
El frontend consume la API, que coordina controladores, servicios y persistencia.

## 3. Lógica Central y Reglas de Negocio
Los flujos documentados conectan autenticación, operación y facturación.
"""


class FakeCache:
    def generate_hash(self, content, doc_type, extra_requirements=None, language=None):
        return content

    def get(self, cache_key):
        return None

    def set(self, cache_key, result):
        pass

    def get_stats(self):
        return {}


class FakeZipService:
    def extraer_zip(self, content):
        return (
            [
                {
                    "filename": "src/routes/example.js",
                    "language": "js",
                    "content": "const route = true;",
                }
            ],
            [],
        )


class FakeDocumenter:
    def __init__(self):
        self.events = []
        self.consolidation_inputs = []
        self.fail_generation = False

    def estimate_input_tokens(self, system_prompt, user_prompt):
        return math.ceil((len(system_prompt) + len(user_prompt)) / 4)

    def generar(self, **kwargs):
        if self.fail_generation:
            raise RuntimeError("provider unavailable")
        return "### Análisis del fragmento\nDescribe el módulo."

    def consolidate(self, docs, lang="es"):
        self.events.append("consolidate")
        self.consolidation_inputs.append(docs)
        if "RAW_DOCUMENT" in docs or "detalle" in docs:
            return "Resumen parcial"
        return FINAL_DOCUMENT

    def apply_extra(self, docs, extra, lang=None):
        self.events.append("apply_extra")
        return docs + f"\n\nRequisito aplicado: {extra}"


class FakeChunkingService:
    def create_chunks(self, files, doc_type="markdown", extra_requirements=None):
        return [
            {
                "content": "source code",
                "files": [file["filename"] for file in files],
            }
        ]


class TestDocumentationConsolidation(unittest.TestCase):
    def setUp(self):
        self.documenter = FakeDocumenter()
        self.orchestrator = DocumentationOrchestrator(
            chunking_service=FakeChunkingService(),
            cache_service=FakeCache(),
            documentador=self.documenter,
        )

    def _process(self, extra_requirements=None, multifile=False):
        return self.orchestrator.process_zip(
            zip_content=b"zip",
            extra_requirements=extra_requirements,
            zip_service=FakeZipService(),
            language="es",
            multifile=multifile,
        )

    def test_single_document_is_consolidated_without_extra_requirements(self):
        result = self._process()

        self.assertIn("Resumen Ejecutivo", result["documentation"])
        self.assertEqual(self.documenter.events, ["consolidate"])

    def test_extra_requirements_are_applied_after_consolidation(self):
        result = self._process(extra_requirements="Incluye ejemplos.")

        self.assertEqual(
            self.documenter.events, ["consolidate", "apply_extra"]
        )
        self.assertIn("Incluye ejemplos.", result["documentation"])

    def test_multifile_skips_global_consolidation(self):
        result = self._process(multifile=True)

        self.assertIn("files", result)
        self.assertEqual(self.documenter.events, [])

    def test_large_input_is_consolidated_in_batches_and_then_synthesized(self):
        self.orchestrator.CONSOLIDATION_MAX_INPUT_TOKENS = 50
        documents = [f"RAW_DOCUMENT {index} " + ("detalle " * 40) for index in range(3)]

        result = self.orchestrator._consolidate_documentation(
            [{"documentation": document} for document in documents],
            extra_requirements=None,
        )

        self.assertIn("Resumen Ejecutivo", result)
        self.assertGreater(len(self.documenter.consolidation_inputs), 1)
        self.assertIn("Resumen parcial", self.documenter.consolidation_inputs[-1])

    def test_failed_chunk_is_not_returned_as_successful_documentation(self):
        self.documenter.fail_generation = True

        with self.assertRaisesRegex(RuntimeError, "fragmentos: 1"):
            self._process()

        self.assertEqual(self.documenter.events, [])

    def test_failed_chunk_is_not_hidden_in_multifile_response(self):
        self.documenter.fail_generation = True

        with self.assertRaisesRegex(RuntimeError, "fragmentos: 1"):
            self._process(multifile=True)

        self.assertEqual(self.documenter.events, [])

    def test_final_document_must_include_required_sections(self):
        self.documenter.consolidate = lambda docs, lang="es": "# Documento\nSin secciones"

        with self.assertRaisesRegex(RuntimeError, "secciones requeridas"):
            self._process()

    def test_section_names_in_body_do_not_replace_required_headings(self):
        documentation = (
            "# Documento\nEl resumen ejecutivo, la arquitectura de componentes "
            "y la lógica central no están organizados en secciones."
        )

        with self.assertRaisesRegex(RuntimeError, "secciones requeridas"):
            self.orchestrator._validate_final_documentation(documentation, "es")


class TestConsolidationPrompts(unittest.TestCase):
    def setUp(self):
        self.documenter = DocumentadorIA.__new__(DocumentadorIA)

    def test_spanish_consolidation_prompt_includes_target_structure(self):
        system_prompt = self.documenter._build_system_prompt(
            "markdown", "es", is_consolidation=True
        )

        self.assertIn("## 1. Resumen Ejecutivo", system_prompt)
        self.assertIn("## 5. API y Permisos", system_prompt)
        self.assertIn("no entregues una colección de resúmenes", system_prompt)

    def test_consolidation_user_prompt_marks_input_as_documentation(self):
        user_prompt = self.documenter._build_user_prompt(
            "document content",
            None,
            "es",
            is_consolidation=True,
        )

        self.assertIn("<DOCUMENTACION_A_CONSOLIDAR>", user_prompt)
        self.assertNotIn("siguiente código", user_prompt)

    def test_english_structure_is_present_for_english_consolidation(self):
        system_prompt = self.documenter._build_system_prompt(
            "markdown", "en", is_consolidation=True
        )

        self.assertIn("## 1. Executive Summary", system_prompt)
        self.assertIn("## 5. API & Permissions", system_prompt)

    def test_consolidation_request_uses_larger_output_budget(self):
        class FakeProvider:
            max_tokens = None

            def create_chat_completion(self, **kwargs):
                self.max_tokens = kwargs["max_tokens"]
                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content=FINAL_DOCUMENT)
                        )
                    ]
                )

        provider = FakeProvider()
        documenter = DocumentadorIA.__new__(DocumentadorIA)
        documenter.providers = {"gemini": provider}
        documenter._model_to_provider = {
            models["final_doc"]["id"]: "gemini",
        }
        documenter.limiters = {}

        documenter.generar(
            codigo_fuente="Generated per-chunk documentation",
            tipo="markdown",
            model_role="final_doc",
            lang="es",
        )

        self.assertEqual(provider.max_tokens, 8192)


if __name__ == "__main__":
    unittest.main()
