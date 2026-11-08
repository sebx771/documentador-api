"""
Modelos de dominio para el pipeline de documentación.

Todas las etapas internas (extracción, generación, consolidación, resultados)
operan sobre estos tipos en lugar de diccionarios o cadenas planas, permitiendo
que los errores de acceso a campos se detecten en tiempo de definición y no en ejecución.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Capa de fuentes
# ---------------------------------------------------------------------------


@dataclass
class SourceFile:
    """Un archivo fuente extraído del ZIP, listo para ser fragmentado (chunked)."""

    filename: str
    language: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "filename": self.filename,
            "language": self.language,
            "content": self.content,
        }


# ---------------------------------------------------------------------------
# Capa de fragmentos (chunks)
# ---------------------------------------------------------------------------


@dataclass
class ChunkDocumentation:
    """Resultado del procesamiento de un fragmento a través de la capa de IA y caché."""

    chunk_index: int
    files: List[str]
    documentation: str
    cached: bool = False
    error: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_index": self.chunk_index,
            "files": self.files,
            "documentation": self.documentation,
            "cached": self.cached,
            "error": self.error,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ChunkDocumentation":
        return ChunkDocumentation(
            chunk_index=data.get("chunk_index", 0),
            files=data.get("files", []),
            documentation=data.get("documentation", ""),
            cached=data.get("cached", False),
            error=data.get("error", False),
        )


# ---------------------------------------------------------------------------
# Capa de salida / resultados
# ---------------------------------------------------------------------------


@dataclass
class GenerationMetadata:
    """Metadatos comunes adjuntos a cada respuesta del pipeline."""

    total_files: int
    invalid_files: List[str]
    total_chunks: int
    cache_stats: Dict[str, Any]
    elapsed_time_seconds: float
    input_size_bytes: int
    doc_type: str
    total_docs: Optional[int] = None  # Solo para modo multifile

    @property
    def invalid_files_count(self) -> int:
        return len(self.invalid_files)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "total_files": self.total_files,
            "invalid_files_count": self.invalid_files_count,
            "invalid_files": self.invalid_files,
            "total_chunks": self.total_chunks,
            "cache_stats": self.cache_stats,
            "elapsed_time_seconds": round(self.elapsed_time_seconds, 2),
            "input_size_bytes": self.input_size_bytes,
            "doc_type": self.doc_type,
        }
        if self.total_docs is not None:
            d["total_docs"] = self.total_docs
        return d


@dataclass
class SingleDocResult:
    """Resultado del pipeline para el modo de documento único."""

    documentation: str
    metadata: GenerationMetadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "documentation": self.documentation,
            "metadata": self.metadata.to_dict(),
        }


@dataclass
class MultifileResult:
    """Resultado del pipeline para el modo multifile."""

    files: Dict[str, str]
    metadata: GenerationMetadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files": self.files,
            "metadata": self.metadata.to_dict(),
        }
