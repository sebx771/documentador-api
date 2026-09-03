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
    # 8000: aprovecha la amplia ventana de contexto del modelo de chunking
    # (minimax-m3, 1M) reduciendo el número de requests diarias consumidas.
    DEFAULT_CHUNK_MAX_TOKENS = 8000
    DEFAULT_FILES_PER_CHUNK = 2

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

            # Si un archivo excede el límite, partirlo internamente
            if file_tokens > self.max_chunk_tokens:
                logger.warning(
                    f"Archivo '{file.get('filename', 'unknown')}' excede el límite "
                    f"de tokens individualmente ({file_tokens} tk > {self.max_chunk_tokens} tk). "
                    f"Dividiendo en sub-partes..."
                )
                sub_files = self._split_file(file, self.max_chunk_tokens)
                for sub_file in sub_files:
                    sub_tokens = self.estimate_tokens(sub_file["content"])

                    should_split = (
                        current_chunk["file_count"] >= self.max_files_per_chunk
                        or current_chunk["total_tokens"] + sub_tokens > self.max_chunk_tokens
                    )

                    if should_split and current_chunk["file_count"] > 0:
                        chunks.append(
                            self._finalize_chunk(current_chunk, doc_type, extra_requirements)
                        )
                        current_chunk = {"files": [], "total_tokens": 0, "file_count": 0}

                    current_chunk["files"].append(sub_file)
                    current_chunk["total_tokens"] += sub_tokens
                    current_chunk["file_count"] += 1
                continue

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

    def _split_file(self, file: Dict, max_tokens: int) -> List[Dict]:
        """Divide un archivo grande en sub-partes que quepan en max_tokens."""
        content = file.get("content", "")
        lines = content.split("\n")
        filename = file.get("filename", "unknown")
        language = file.get("language", "unknown")

        parts = []
        current_lines = []
        current_tokens = 0

        for line in lines:
            line_tokens = self.estimate_tokens(line + "\n")
            if current_tokens + line_tokens > max_tokens and current_lines:
                part_content = "\n".join(current_lines)
                part_filename = f"{filename} (parte {len(parts) + 1})"
                parts.append({
                    "content": part_content,
                    "filename": part_filename,
                    "language": language,
                })
                current_lines = []
                current_tokens = 0
            current_lines.append(line)
            current_tokens += line_tokens

        if current_lines:
            part_content = "\n".join(current_lines)
            part_filename = f"{filename} (parte {len(parts) + 1})"
            parts.append({
                "content": part_content,
                "filename": part_filename,
                "language": language,
            })

        logger.info(
            f"Archivo '{filename}' dividido en {len(parts)} partes "
            f"({self.estimate_tokens(content)} tk totales)"
        )
        return parts

    def estimate_tokens(self, text: str) -> int:
        """Estimación burda de tokens (aprox 4 caracteres por token)."""
        return len(text) // 4
