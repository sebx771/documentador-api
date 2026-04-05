import logging
import time
from typing import List, Dict, Any

from .chunking_service import ChunkingService
from .cache_service import CacheService
from .ai_services import DocumentadorIA

logger = logging.getLogger(__name__)


class DocumentationOrchestrator:
    """
    Orquestador principal que coordina:
    - Extracción de ZIP
    - Chunking de archivos
    - Cache por hash
    - Generación de documentación
    - Consolidación de resultados
    """

    DEFAULT_MAX_INPUT_SIZE = 10 * 1024 * 1024
    DEFAULT_MAX_FILES = 50

    def __init__(
        self,
        max_input_size: int = None,
        max_files: int = None,
        chunking_service: ChunkingService = None,
        cache_service: CacheService = None,
        documentador: DocumentadorIA = None
    ):
        self.max_input_size = max_input_size or self.DEFAULT_MAX_INPUT_SIZE
        self.max_files = max_files or self.DEFAULT_MAX_FILES
        
        self.chunking_service = chunking_service or ChunkingService()
        self.cache_service = cache_service or CacheService()
        self.documentador = documentador or DocumentadorIA()

    def process_zip(
        self,
        zip_content: bytes,
        doc_type: str = "markdown",
        extra_requirements: str = None,
        zip_service=None
    ) -> Dict[str, Any]:
        """
        Procesa un ZIP y genera documentación consolidada.
        
        Args:
            zip_content: Bytes del archivo ZIP
            doc_type: Tipo de documento (markdown, pdf, word)
            extra_requirements: Requisitos adicionales
            zip_service: Instancia de ZipService (inyectada para testing)
        
        Returns:
            Dict con documentación, metadata y errores
        """
        start_time = time.time()
        
        logger.info(f"Iniciando procesamiento de ZIP ({len(zip_content)} bytes)")
        
        input_size = len(zip_content)
        if input_size > self.max_input_size:
            raise ValueError(
                f"Archivo demasiado grande: {input_size} bytes "
                f"(máximo: {self.max_input_size} bytes)"
            )

        files, invalid_files = self._extract_files(zip_content, zip_service)
        
        if not files:
            raise ValueError("No se encontraron archivos válidos para documentar")

        logger.info(f"Archivos extraídos: {len(files)} válidos, {len(invalid_files)} inválidos")

        chunks = self.chunking_service.create_chunks(
            files=files,
            doc_type=doc_type,
            extra_requirements=extra_requirements
        )
        
        logger.info(f"Chunks creados: {len(chunks)}")

        chunk_results = self._process_chunks(chunks, doc_type, extra_requirements)

        final_documentation = self._consolidate_documentation(chunk_results)

        elapsed_time = time.time() - start_time
        cache_stats = self.cache_service.get_stats()

        logger.info(
            f"Procesamiento completado: {len(files)} archivos, "
            f"{len(chunks)} chunks, tiempo: {elapsed_time:.2f}s, "
            f"cache hit rate: {cache_stats.get('hit_rate_percent', 0)}%"
        )

        return {
            "documentation": final_documentation,
            "metadata": {
                "total_files": len(files),
                "invalid_files_count": len(invalid_files),
                "invalid_files": invalid_files,
                "total_chunks": len(chunks),
                "cache_stats": cache_stats,
                "elapsed_time_seconds": round(elapsed_time, 2),
                "input_size_bytes": input_size,
                "doc_type": doc_type
            }
        }

    def _extract_files(
        self,
        zip_content: bytes,
        zip_service
    ) -> tuple:
        """Extrae archivos del ZIP usando el servicio existente."""
        from .zip_services import ZipService
        
        service = zip_service or ZipService()
        
        raw_content, invalid_files = service.extraer_zip(zip_content)
        
        if not raw_content:
            return [], invalid_files
        
        files = self._parse_extracted_content(raw_content)
        
        return files, invalid_files

    def _parse_extracted_content(self, raw_content: str) -> List[Dict[str, str]]:
        """Convierte el contenido extraído en lista de diccionarios."""
        files = []
        
        sections = raw_content.split("### Archivo:")
        
        for section in sections:
            if not section.strip():
                continue
            
            try:
                lines = section.split("\n", 1)
                if len(lines) < 2:
                    continue
                
                header = lines[0].strip()
                content = lines[1] if len(lines) > 1 else ""
                
                parts = header.split("Lenguaje:")
                filename = parts[0].strip()
                language = parts[1].strip() if len(parts) > 1 else "unknown"
                
                if content.strip():
                    files.append({
                        "filename": filename,
                        "language": language,
                        "content": content.strip()
                    })
                    
            except Exception as e:
                logger.warning(f"Error parseando sección: {str(e)}")
                continue
        
        return files

    def _process_chunks(
        self,
        chunks: List[Dict],
        doc_type: str,
        extra_requirements: str
    ) -> List[Dict]:
        """Procesa cada chunk, usando cache cuando es posible."""
        results = []
        
        for idx, chunk in enumerate(chunks):
            logger.info(f"Procesando chunk {idx + 1}/{len(chunks)} ({chunk.get('file_count', 0)} archivos)")
            
            cache_key = self.cache_service.generate_hash(
                content=chunk["content"],
                doc_type=doc_type,
                extra_requirements=extra_requirements
            )
            
            cached_result = self.cache_service.get(cache_key)
            
            if cached_result:
                logger.info(f"Chunk {idx + 1}: usando resultado cacheado")
                results.append(cached_result)
                continue
            
            try:
                doc_result = self.documentador.generar(
                    codigo_fuente=chunk["content"],
                    tipo=doc_type,
                    extra=extra_requirements
                )
                
                result = {
                    "chunk_index": idx,
                    "files": chunk.get("files", []),
                    "documentation": doc_result,
                    "cached": False
                }
                
                self.cache_service.set(cache_key, result)
                results.append(result)
                
                logger.info(f"Chunk {idx + 1}: documentación generada ({len(doc_result)} caracteres)")
                
            except Exception as e:
                logger.error(f"Error procesando chunk {idx + 1}: {str(e)}")
                results.append({
                    "chunk_index": idx,
                    "files": chunk.get("files", []),
                    "documentation": f"Error al generar documentación: {str(e)}",
                    "error": True,
                    "cached": False
                })
        
        return results

    def _consolidate_documentation(self, chunk_results: List[Dict]) -> str:
        """Consolida la documentación de múltiples chunks."""
        if not chunk_results:
            return "No se pudo generar documentación."
        
        if len(chunk_results) == 1:
            return chunk_results[0].get("documentation", "")
        
        sections = []
        
        for result in chunk_results:
            files = result.get("files", [])
            docs = result.get("documentation", "")

            section = f"\n\n{docs}"
            section += f"## Fuentes: {', '.join(files[:5])}"
            if len(files) > 5:
                section += f" ... y {len(files) - 5} más"
            section += f"\n\n{docs}"
            
            sections.append(section)
        
        return "\n\n\n".join(sections)