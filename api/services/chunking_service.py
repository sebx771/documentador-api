import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ChunkingService:
    """
    Service para dividir código en chunks manejables.
    Optimizado para serverless con límites configurables.
    """

    # Límite expresado en TOKENS (no caracteres).
    # Regla aproximada: 1 token ≈ 4 caracteres de código fuente.
    # El prompt del sistema añade ~500-800 tokens de overhead, por eso el
    # límite real debe ser bastante menor que el TPM del modelo.
    DEFAULT_CHUNK_MAX_TOKENS = 3000
    DEFAULT_FILES_PER_CHUNK = 3

    def __init__(self, max_chunk_tokens: int = None, max_files_per_chunk: int = None):
        self.max_chunk_tokens = max_chunk_tokens or self.DEFAULT_CHUNK_MAX_TOKENS
        self.max_files_per_chunk = max_files_per_chunk or self.DEFAULT_FILES_PER_CHUNK

    def create_chunks(
        self,
        files: List[Dict[str, Any]],
        doc_type: str = "markdown",
        extra_requirements: str = None,
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
        current_chunk = {"files": [], "total_tokens": 0, "file_count": 0}

        for file in files:
            content = file.get("content", "")
            file_tokens = self.estimate_tokens(content)

            # Advertir si un archivo individual ya supera el límite por sí solo
            if file_tokens > self.max_chunk_tokens:
                logger.warning(
                    f"Archivo '{file.get('filename', 'unknown')}' excede el límite "
                    f"de tokens individualmente ({file_tokens} tk > {self.max_chunk_tokens} tk). "
                    f"Se procesará solo en su propio chunk."
                )

            should_split = (
                current_chunk["file_count"] >= self.max_files_per_chunk
                or current_chunk["total_tokens"] + file_tokens > self.max_chunk_tokens
            )

            if should_split and current_chunk["file_count"] > 0:
                chunks.append(
                    self._finalize_chunk(current_chunk, doc_type, extra_requirements)
                )
                current_chunk = {"files": [], "total_tokens": 0, "file_count": 0}

            current_chunk["files"].append(file)
            current_chunk["total_tokens"] += file_tokens
            current_chunk["file_count"] += 1

        if current_chunk["file_count"] > 0:
            chunks.append(
                self._finalize_chunk(current_chunk, doc_type, extra_requirements)
            )

        logger.info(
            f"Chunking completado: {len(files)} archivos -> {len(chunks)} chunks "
            f"(max_files: {self.max_files_per_chunk}, max_tokens: {self.max_chunk_tokens})"
        )

        return chunks

    def _finalize_chunk(
        self, chunk_data: Dict, doc_type: str, extra_requirements: str
    ) -> Dict[str, Any]:
        """Finaliza un chunk calculando su hash y contenido combinado."""
        combined_content = "\n".join(
            f"### Archivo: {f.get('filename', 'unknown')}\nLenguaje: {f.get('language', 'unknown')}\n\n{f.get('content', '')}"
            for f in chunk_data["files"]
        )

        return {
            "content": combined_content,
            "file_count": chunk_data["file_count"],
            "total_tokens": chunk_data["total_tokens"],
            "files": [f.get("filename", "unknown") for f in chunk_data["files"]],
            "doc_type": doc_type,
            "extra_requirements": extra_requirements,
        }

    def estimate_tokens(self, text: str) -> int:
        """Estimación burda de tokens (aprox 4 caracteres por token)."""
        return len(text) // 4
