"""
Coordinador del pipeline: orquestador simplificado y desacoplado.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from ..cache_service import CacheService
from ..chunking_service import ChunkingService
from ..ai import DocumentadorIA
from .consolidation import (
    DEFAULT_MAX_INPUT_TOKENS,
    DEFAULT_MAX_ROUNDS,
    consolidate_chunks,
)
from .extraction import extract_source_files
from .generation import process_chunks, raise_for_failed_chunks
from .results import build_multifile_result, build_single_result

logger = logging.getLogger(__name__)


class DocumentationOrchestrator:
    """Coordina el pipeline completo de documentación para un payload ZIP.

    Permite inyectar fakes o mocks para cualquier dependencia en tests; cada función
    de etapa puede importarse y probarse de forma aislada.
    """

    DEFAULT_MAX_INPUT_SIZE = 10 * 1024 * 1024  # 10 MB
    DEFAULT_MAX_FILES = 50

    def __init__(
        self,
        max_input_size: Optional[int] = None,
        max_files: Optional[int] = None,
        chunking_service: Optional[ChunkingService] = None,
        cache_service: Optional[CacheService] = None,
        documentador: Optional[DocumentadorIA] = None,
    ) -> None:
        self.max_input_size: int = max_input_size or self.DEFAULT_MAX_INPUT_SIZE
        self.max_files: int = max_files or self.DEFAULT_MAX_FILES

        self.chunking_service: ChunkingService = chunking_service or ChunkingService()
        self.cache_service: CacheService = cache_service or CacheService()
        self.documentador: DocumentadorIA = documentador or DocumentadorIA()

        # Parámetros ajustables de consolidación — modificables en tests o subclases si fuera necesario.
        self.consolidation_max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS
        self.max_consolidation_rounds: int = DEFAULT_MAX_ROUNDS

    # ------------------------------------------------------------------
    # API Pública
    # ------------------------------------------------------------------

    def process_zip(
        self,
        zip_content: bytes,
        doc_type: str = "markdown",
        extra_requirements: Optional[str] = None,
        zip_service=None,
        language: Optional[str] = None,
        multifile: bool = False,
    ) -> Dict[str, Any]:
        """Procesa *zip_content* y retorna la documentación generada.

        Args:
            zip_content: Bytes en crudo del ZIP provenientes de la petición HTTP.
            doc_type: Formato de salida (``"markdown"``, ``"pdf"``, ``"word"``…).
            extra_requirements: Directivas de texto libre añadidas al prompt de la IA.
            zip_service: Instancia opcional de :class:`ZipService` (útil en tests
                para evitar parsear un archivo ZIP real).
            language: Fuerza un idioma específico de salida (``"es"``, ``"en"``…).
                Si es *None*, el idioma se detecta automáticamente a partir del código fuente.
            multifile: Si es *True*, retorna un documento por cada fragmento en vez de
                un único documento consolidado.

        Returns:
            ``{"documentation": str, "metadata": dict}`` para el modo de documento único,
            o ``{"files": dict[str, str], "metadata": dict}`` para el modo multifile.

        Raises:
            ValueError: Si el ZIP excede el tamaño límite o no contiene archivos válidos.
            RuntimeError: Si falla la generación de algún fragmento o si la consolidación
                no produce un documento válido.
        """
        start_time = time.time()
        input_size = len(zip_content)

        logger.debug("Iniciando procesamiento de ZIP (%d bytes)", input_size)

        if input_size > self.max_input_size:
            raise ValueError(
                f"Archivo demasiado grande: {input_size} bytes "
                f"(máximo: {self.max_input_size} bytes)"
            )

        # --- Etapa 1: extraer ------------------------------------------------
        source_files, invalid_files = extract_source_files(
            zip_content, zip_service, max_eligible_files=self.max_files
        )
        if not source_files:
            raise ValueError("No se encontraron archivos válidos para documentar")

        logger.debug(
            "Archivos extraídos: %d válidos, %d inválidos",
            len(source_files),
            len(invalid_files),
        )

        # --- Etapa 2: chunkear -----------------------------------------------
        # ChunkingService trabaja con diccionarios planos; convertimos SourceFile → dict.
        file_dicts = [sf.to_dict() for sf in source_files]
        chunks = self.chunking_service.create_chunks(
            files=file_dicts,
            doc_type=doc_type,
            extra_requirements=extra_requirements,
        )
        logger.debug("Chunks creados: %d", len(chunks))

        # --- Etapa 3: detectar idioma ----------------------------------------
        if language:
            detected_lang = language
            logger.debug("Idioma forzado vía parámetros: %s", detected_lang)
        else:
            sample = chunks[0]["content"] if chunks else ""
            detected_lang = self.documentador.detect_language(sample, extra_requirements)
            logger.debug(
                "Coherencia de idioma establecida (Smart Detection): %s", detected_lang
            )

        # --- Etapa 4: generar ------------------------------------------------
        chunk_results = process_chunks(
            chunks=chunks,
            doc_type=doc_type,
            extra_requirements=extra_requirements,
            language=detected_lang,
            cache_service=self.cache_service,
            documentador=self.documentador,
        )
        raise_for_failed_chunks(chunk_results)

        # --- Etapa 5a: construir resultado multifile -------------------------
        if multifile:
            elapsed = time.time() - start_time
            result = build_multifile_result(
                chunk_results=chunk_results,
                total_files=len(source_files),
                invalid_files=invalid_files,
                total_chunks=len(chunks),
                cache_stats=self.cache_service.get_stats(),
                elapsed_time_seconds=elapsed,
                input_size_bytes=input_size,
                doc_type=doc_type,
            )
            logger.debug(
                "Multifile completado: %d archivos, %d chunks -> %d documentos, %.2fs",
                len(source_files),
                len(chunks),
                len(result.files),
                elapsed,
            )
            return result.to_dict()

        # --- Etapa 5b: consolidar y construir resultado único ----------------
        final_documentation = consolidate_chunks(
            chunk_results=chunk_results,
            extra_requirements=extra_requirements,
            language=detected_lang,
            documentador=self.documentador,
            max_input_tokens=self.consolidation_max_input_tokens,
            max_rounds=self.max_consolidation_rounds,
        )

        elapsed = time.time() - start_time
        result_single = build_single_result(
            documentation=final_documentation,
            total_files=len(source_files),
            invalid_files=invalid_files,
            total_chunks=len(chunks),
            cache_stats=self.cache_service.get_stats(),
            elapsed_time_seconds=elapsed,
            input_size_bytes=input_size,
            doc_type=doc_type,
        )
        logger.debug(
            "Procesamiento completado: %d archivos, %d chunks, %.2fs",
            len(source_files),
            len(chunks),
            elapsed,
        )
        return result_single.to_dict()

    # ------------------------------------------------------------------
    # Métodos conservados para retrocompatibilidad con tests existentes
    # ------------------------------------------------------------------

    def _consolidate_documentation(
        self, chunk_results, extra_requirements, language="es"
    ) -> str:
        """Capa fina de compatibilidad que delega a :func:`consolidation.consolidate_chunks`."""
        from .models import ChunkDocumentation as _CD

        # Acepta tanto objetos tipados como diccionarios del formato anterior.
        typed = [
            r if isinstance(r, _CD) else _CD.from_dict(r)
            for r in chunk_results
        ]
        return consolidate_chunks(
            chunk_results=typed,
            extra_requirements=extra_requirements,
            language=language,
            documentador=self.documentador,
            max_input_tokens=self.consolidation_max_input_tokens,
            max_rounds=self.max_consolidation_rounds,
        )

    def _validate_final_documentation(self, documentation: str, language: str) -> None:
        """Capa fina de compatibilidad que delega a :func:`consolidation.validate_sections`."""
        from .consolidation import validate_sections

        validate_sections(documentation, language)

    # Expone la constante de presupuesto bajo el nombre anterior para que los tests
    # que modifican ``orchestrator.CONSOLIDATION_MAX_INPUT_TOKENS`` sigan funcionando.
    @property
    def CONSOLIDATION_MAX_INPUT_TOKENS(self) -> int:  # noqa: N802
        return self.consolidation_max_input_tokens

    @CONSOLIDATION_MAX_INPUT_TOKENS.setter
    def CONSOLIDATION_MAX_INPUT_TOKENS(self, value: int) -> None:  # noqa: N802
        self.consolidation_max_input_tokens = value
