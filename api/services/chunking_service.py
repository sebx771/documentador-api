import hashlib
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ChunkingService:
    """
    Service para dividir código en chunks manejables.
    Optimizado para serverless con límites configurables.
    """

    DEFAULT_CHUNK_MAX_SIZE = 8000
    DEFAULT_FILES_PER_CHUNK = 10
    DEFAULT_MAX_TOKENS = 12000

    def __init__(
        self,
        max_chunk_size: int = None,
        max_files_per_chunk: int = None,
        max_tokens_estimate: int = None
    ):
        self.max_chunk_size = max_chunk_size or self.DEFAULT_CHUNK_MAX_SIZE
        self.max_files_per_chunk = max_files_per_chunk or self.DEFAULT_FILES_PER_CHUNK
        self.max_tokens_estimate = max_tokens_estimate or self.DEFAULT_MAX_TOKENS

    def create_chunks(
        self,
        files: List[Dict[str, Any]],
        doc_type: str = "markdown",
        extra_requirements: str = None
    ) -> List[Dict[str, Any]]:
        """
        Crea chunks de archivos distribuidos por tamaño y cantidad.
        
        Args:
            files: Lista de diccionarios con keys 'content', 'filename', 'language'
            doc_type: Tipo de documento (markdown, pdf, word)
            extra_requirements: Requisitos adicionales para el hash
        
        Returns:
            Lista de chunks, cada uno con archivos y metadata
        """
        if not files:
            logger.warning("No hay archivos para crear chunks")
            return []

        chunks = []
        current_chunk = {
            "files": [],
            "total_size": 0,
            "file_count": 0
        }

        for file in files:
            content = file.get("content", "")
            file_size = len(content)

            should_split = (
                current_chunk["file_count"] >= self.max_files_per_chunk or
                current_chunk["total_size"] + file_size > self.max_chunk_size
            )

            if should_split and current_chunk["file_count"] > 0:
                chunks.append(self._finalize_chunk(current_chunk, doc_type, extra_requirements))
                current_chunk = {
                    "files": [],
                    "total_size": 0,
                    "file_count": 0
                }

            current_chunk["files"].append(file)
            current_chunk["total_size"] += file_size
            current_chunk["file_count"] += 1

        if current_chunk["file_count"] > 0:
            chunks.append(self._finalize_chunk(current_chunk, doc_type, extra_requirements))

        logger.info(
            f"Chunking completado: {len(files)} archivos -> {len(chunks)} chunks "
            f"(max_files: {self.max_files_per_chunk}, max_size: {self.max_chunk_size})"
        )

        return chunks

    def _finalize_chunk(
        self,
        chunk_data: Dict,
        doc_type: str,
        extra_requirements: str
    ) -> Dict[str, Any]:
        """Finaliza un chunk calculando su hash y contenido combinado."""
        combined_content = "\n".join(
            f"### Archivo: {f.get('filename', 'unknown')}\nLenguaje: {f.get('language', 'unknown')}\n\n{f.get('content', '')}"
            for f in chunk_data["files"]
        )

        return {
            "content": combined_content,
            "file_count": chunk_data["file_count"],
            "total_size": chunk_data["total_size"],
            "files": [f.get("filename", "unknown") for f in chunk_data["files"]],
            "doc_type": doc_type,
            "extra_requirements": extra_requirements
        }

    def estimate_tokens(self, text: str) -> int:
        """Estimación burda de tokens (aprox 4 caracteres por token)."""
        return len(text) // 4