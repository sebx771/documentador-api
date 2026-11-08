"""
Capa de extracción: puente entre ZipService y List[SourceFile].

Elimina el protocolo basado en marcadores de texto (delimitadores ``### Archivo:``)
que se utilizaba anteriormente para transferir archivos entre ZipService y el orquestador.
Cada archivo es ahora un registro tipado ``SourceFile``; los errores de parseo
son explícitos y no se silencian mediante un bloque genérico ``except Exception``.
"""

from __future__ import annotations

import logging
from typing import List, Tuple

from .models import SourceFile

logger = logging.getLogger(__name__)


def extract_source_files(
    zip_content: bytes,
    zip_service,
    max_eligible_files: int | None = None,
) -> Tuple[List[SourceFile], List[str]]:
    """Extrae archivos fuente elegibles a partir de *zip_content*.

    Args:
        zip_content: Bytes en crudo del archivo ZIP.
        zip_service: Instancia de :class:`ZipService` (o fake compatible).
            Si es *None*, se crea una instancia por defecto con *max_eligible_files*.
        max_eligible_files: Límite reenviado a :class:`ZipService` cuando se instancia
            internamente. Se ignora si *zip_service* se pasa explícitamente.

    Returns:
        Una tupla ``(source_files, invalid_files)``. *invalid_files* es una lista
        de mensajes de error legibles para aquellos archivos que no pudieron leerse.

    Raises:
        ValueError: Propagado desde :class:`ZipService` ante bombas ZIP, intentos de
            path traversal o archivos corruptos.
    """
    from ..zip_services import ZipService

    service: ZipService = zip_service or ZipService(
        max_eligible_files=max_eligible_files
    )
    raw_files, invalid_files = service.extraer_zip(zip_content)

    source_files: List[SourceFile] = []
    for entry in raw_files:
        filename = entry.get("filename", "").strip()
        language = entry.get("language", "unknown").strip()
        content = entry.get("content", "").strip()

        if not filename:
            logger.warning("Entrada sin nombre de archivo omitida durante la extracción")
            continue
        if not content:
            logger.debug("Archivo '%s' omitido: contenido vacío tras limpieza", filename)
            continue

        source_files.append(SourceFile(filename=filename, language=language, content=content))

    return source_files, invalid_files
