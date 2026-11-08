"""
Capa de generación: documentación de fragmentos consciente de la caché.

Gestiona la lectura y escritura en caché, las llamadas al modelo de IA ante fallos de caché
(misses) y la generación de nombres de archivo resistentes a colisiones para el modo multifile.
"""


from __future__ import annotations

import hashlib
import logging
import os
from typing import List, Optional

from .models import ChunkDocumentation

logger = logging.getLogger(__name__)


def process_chunks(
    chunks: List[dict],
    doc_type: str,
    extra_requirements: Optional[str],
    language: str,
    cache_service,
    documentador,
) -> List[ChunkDocumentation]:
    """Genera documentación para cada fragmento, consultando primero la caché.

    Args:
        chunks: Salida de :meth:`ChunkingService.create_chunks` — cada elemento
            contiene ``content`` (str) y ``files`` (lista de rutas de archivos).
        doc_type: Formato de documentación solicitado por el invocador.
        extra_requirements: Directivas opcionales de texto libre enviadas a la IA.
        language: Código ISO de idioma utilizado tanto para los prompts de la IA como para la clave de caché.
        cache_service: Backend de caché que expone ``generate_hash``, ``get`` y ``set``.
        documentador: Backend de IA que expone ``generar``.

    Returns:
        Una lista de :class:`ChunkDocumentation` por cada chunk recibido, en el mismo orden.
        Los fragmentos que fallaron con excepción se incluyen con ``error=True``
        para que el invocador decida cómo manejarlos.
    """
    results: List[ChunkDocumentation] = []

    for idx, chunk in enumerate(chunks):
        logger.debug("Procesando chunk %d/%d", idx + 1, len(chunks))

        cache_key = cache_service.generate_hash(
            content=chunk["content"],
            doc_type=doc_type,
            extra_requirements=extra_requirements,
            language=language,
        )

        cached = cache_service.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit para chunk %d", idx + 1)
            results.append(ChunkDocumentation.from_dict(cached))
            continue

        try:
            doc_text = documentador.generar(
                codigo_fuente=chunk["content"],
                tipo=doc_type,
                extra=extra_requirements,
                is_chunk=True,
                lang=language,
            )
            result = ChunkDocumentation(
                chunk_index=idx,
                files=chunk.get("files", []),
                documentation=doc_text,
                cached=False,
            )
            cache_service.set(cache_key, result.to_dict())
            results.append(result)

        except Exception as exc:
            logger.error("Error procesando chunk %d: %s", idx + 1, exc)
            results.append(
                ChunkDocumentation(
                    chunk_index=idx,
                    files=chunk.get("files", []),
                    documentation=f"Error: {exc}",
                    error=True,
                )
            )

    return results


def raise_for_failed_chunks(chunk_results: List[ChunkDocumentation]) -> None:
    """Lanza :class:`RuntimeError` si algún fragmento terminó con error.

    Utiliza numeración en base 1 para los fragmentos en el mensaje para coincidir con los logs de depuración.
    """
    failed = [
        r.chunk_index
        for r in chunk_results
        if r.error
    ]
    if failed:
        raise RuntimeError(
            "No se pudo generar documentación para los fragmentos: "
            + ", ".join(str(i + 1) for i in failed)
        )


def chunk_output_filename(result: ChunkDocumentation, index: int) -> str:
    """Devuelve un nombre de archivo de salida resistente a colisiones para *result*.

    Utiliza la ruta relativa completa (reemplazando separadores de directorios por ``__``)
    de los primeros dos archivos fuente para que archivos con el mismo nombre base
    pero en carpetas distintas produzcan claves diferentes.
    """
    if not result.files:
        return f"chunk_{index + 1:03d}.md"

    parts: List[str] = []
    for filepath in result.files[:2]:
        safe = filepath.replace("\\", "/").strip("/").replace("/", "__")
        name = os.path.splitext(safe)[0]
    # este condicional evita que se creen nombres de archivos muy largos xd
        if len(name) > 50:
            file_hash = hashlib.md5(filepath.encode()).hexdigest()[:6]
            name = f"{name[:43]}__{file_hash}"
        parts.append(name)

    extra = len(result.files) - 2
    if extra > 0:
        return f"{'+'.join(parts)}+{extra}more.md"
    return f"{'+'.join(parts)}.md"
