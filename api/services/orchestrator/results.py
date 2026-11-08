"""
Capa de resultados: ensamblado de metadatos y formateo de la respuesta final.

Centraliza la construcción de :class:`GenerationMetadata`,
:class:`SingleDocResult` y :class:`MultifileResult` para que ambas ramas del pipeline
(documento único y multifile) compartan campos de metadatos idénticos.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .generation import chunk_output_filename
from .models import (
    ChunkDocumentation,
    GenerationMetadata,
    MultifileResult,
    SingleDocResult,
)


def build_metadata(
    *,
    total_files: int,
    invalid_files: List[str],
    total_chunks: int,
    cache_stats: Dict,
    elapsed_time_seconds: float,
    input_size_bytes: int,
    doc_type: str,
    total_docs: Optional[int] = None,
) -> GenerationMetadata:
    """Construye una instancia de :class:`GenerationMetadata` a partir de las métricas del pipeline."""
    return GenerationMetadata(
        total_files=total_files,
        invalid_files=invalid_files,
        total_chunks=total_chunks,
        cache_stats=cache_stats,
        elapsed_time_seconds=elapsed_time_seconds,
        input_size_bytes=input_size_bytes,
        doc_type=doc_type,
        total_docs=total_docs,
    )


def build_single_result(
    *,
    documentation: str,
    total_files: int,
    invalid_files: List[str],
    total_chunks: int,
    cache_stats: Dict,
    elapsed_time_seconds: float,
    input_size_bytes: int,
    doc_type: str,
) -> SingleDocResult:
    """Devuelve un :class:`SingleDocResult` listo para ser serializado como respuesta HTTP."""
    metadata = build_metadata(
        total_files=total_files,
        invalid_files=invalid_files,
        total_chunks=total_chunks,
        cache_stats=cache_stats,
        elapsed_time_seconds=elapsed_time_seconds,
        input_size_bytes=input_size_bytes,
        doc_type=doc_type,
    )
    return SingleDocResult(documentation=documentation, metadata=metadata)


def build_multifile_result(
    *,
    chunk_results: List[ChunkDocumentation],
    total_files: int,
    invalid_files: List[str],
    total_chunks: int,
    cache_stats: Dict,
    elapsed_time_seconds: float,
    input_size_bytes: int,
    doc_type: str,
) -> MultifileResult:
    """Devuelve un :class:`MultifileResult` mapeando nombres de archivo de salida a documentación."""
    files_dict: Dict[str, str] = {}
    for idx, result in enumerate(chunk_results):
        filename = chunk_output_filename(result, idx)
        files_dict[filename] = result.documentation

    metadata = build_metadata(
        total_files=total_files,
        invalid_files=invalid_files,
        total_chunks=total_chunks,
        cache_stats=cache_stats,
        elapsed_time_seconds=elapsed_time_seconds,
        input_size_bytes=input_size_bytes,
        doc_type=doc_type,
        total_docs=len(files_dict),
    )
    return MultifileResult(files=files_dict, metadata=metadata)
