from datetime import datetime
import logging
import time
import io


from ..export.pdf_gen import EasyDocsPDF
from ..export.docx_gen import EasyDocsDOCX
from ..services.zip_services import ZipService
from ..services.documentation_orchestrator import DocumentationOrchestrator
from ..services.chunking_service import ChunkingService
from ..services.cache_service import get_global_cache

# Configurar logging
logger = logging.getLogger(__name__)

MAX_ZIP_SIZE = 10 * 1024 * 1024


class ZipController:
    def __init__(self):
        self.zip_service = ZipService()
        self.chunking_service = ChunkingService()
        self.cache_service = get_global_cache(max_size=100, enable_lru=True)
        self.orchestrator = DocumentationOrchestrator(
            max_input_size=MAX_ZIP_SIZE,
            max_files=50,
            chunking_service=self.chunking_service,
            cache_service=self.cache_service,
        )

    def preview_zip(self, file):
        """
        Lista el contenido de un archivo ZIP.
        """
        if not file:
            return {
                "type": "json",
                "data": {"error": "No se proporcionó ningún archivo .zip"},
                "status": 400,
            }

        filename = file.filename or ""
        if not filename.endswith(".zip"):
            return {
                "type": "json",
                "data": {"error": "Solo se permiten archivos .zip"},
                "status": 400,
            }

        try:
            contenido_bytes = file.read()
            codigo = self.zip_service.listar_contenido_zip(contenido_bytes)
            return {"type": "json", "data": codigo, "status": 200}
        except Exception as e:
            logger.error(f"Error en preview_zip: {str(e)}")
            return {
                "type": "json",
                "data": {"error": f"Error al leer el archivo ZIP: {str(e)}"},
                "status": 500,
            }

    def upload_zip(
        self, file, doc_type="markdown", extra_requirements="", language=None
    ):
        """
        Procesa un archivo ZIP y genera documentación.
        """
        start_time = time.time()

        if not file:
            logger.warning("Petición sin archivo")
            return {
                "type": "json",
                "data": {
                    "error": "No se proporcionó ningún archivo .zip",
                    "codigo_error": "NO_FILE",
                },
                "status": 400,
            }

        filename = file.filename or ""
        if not filename or not filename.endswith(".zip"):
            logger.warning(f"Archivo inválido: {filename}")
            return {
                "type": "json",
                "data": {
                    "error": "Solo se permiten archivos .zip",
                    "codigo_error": "INVALID_FILE_TYPE",
                },
                "status": 400,
            }

        zip_content = file.read()
        input_size = len(zip_content)

        logger.info(f"ZIP recibido: {filename}, tamaño: {input_size} bytes")

        if input_size > MAX_ZIP_SIZE:
            logger.warning(f"Archivo demasiado grande: {input_size} bytes")
            return {
                "type": "json",
                "data": {
                    "error": f"Archivo demasiado grande. Máximo: {MAX_ZIP_SIZE / (1024*1024)}MB",
                    "codigo_error": "FILE_TOO_LARGE",
                },
                "status": 400,
            }

        if input_size == 0:
            return {
                "type": "json",
                "data": {"error": "Archivo vacío", "codigo_error": "EMPTY_FILE"},
                "status": 400,
            }

        if doc_type not in ["markdown", "pdf", "word", "multifile"]:
            return {
                "type": "json",
                "data": {
                    "error": "Tipo de documento inválido. Use: markdown, pdf, word o multifile",
                    "codigo_error": "INVALID_DOC_TYPE",
                },
                "status": 400,
            }

        try:
            is_multifile = doc_type == "multifile"
            result = self.orchestrator.process_zip(
                zip_content=zip_content,
                doc_type=doc_type,
                extra_requirements=extra_requirements,
                zip_service=self.zip_service,
                language=language,
                multifile=is_multifile,
            )

            elapsed = time.time() - start_time
            cache_stats = result["metadata"].get("cache_stats", {})

            logger.info(
                f"ZIP procesado exitosamente: {result['metadata']['total_files']} archivos, "
                f"{result['metadata']['total_chunks']} chunks, "
                f"hits de cache: {cache_stats.get('hits', 0)}, "
                f"tiempo: {elapsed:.2f}s"
            )

            if doc_type == "multifile":
                return self._generar_zip_multifile(
                    result["files"], cache_stats, elapsed
                )
            elif doc_type == "markdown":
                return self._generar_markdown(
                    result["documentation"], cache_stats, elapsed
                )
            elif doc_type == "pdf":
                return self._generar_pdf(result["documentation"], cache_stats, elapsed)
            elif doc_type == "word":
                return self._generar_docx(result["documentation"], cache_stats, elapsed)

        except ValueError as e:
            logger.error(f"Error de validación: {str(e)}")
            return {
                "type": "json",
                "data": {"error": str(e), "codigo_error": "VALIDATION_ERROR"},
                "status": 400,
            }

        except Exception as e:
            logger.error(f"Error procesando ZIP: {str(e)}", exc_info=True)
            return {
                "type": "json",
                "data": {
                    "error": f"Error al procesar el archivo: {str(e)}",
                    "codigo_error": "PROCESSING_ERROR",
                },
                "status": 500,
            }

    def _generar_markdown(
        self, contenido, cache_stats=None, elapsed_time=0.0, from_cache=False
    ):
        """Genera y retorna un archivo Markdown."""
        logger.info(
            f"Documentación Markdown generada exitosamente (cache: {from_cache}, tiempo: {elapsed_time:.2f}s)"
        )
        logger.info(f"Estadísticas de cache: {cache_stats}")

        if isinstance(contenido, str):
            contenido = contenido.encode("utf-8")

        return {
            "type": "file",
            "content": contenido,
            "mimetype": "text/markdown",
            "filename": f'documentacion_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.md',
        }

    def _generar_pdf(
        self, contenido, cache_stats=None, elapsed_time=0.0, from_cache=False
    ):
        """Genera y retorna un archivo PDF."""
        logger.info(
            f"PDF generado exitosamente (cache: {from_cache}, tiempo: {elapsed_time:.2f}s)"
        )
        logger.info(f"Estadísticas de cache: {cache_stats}")

        pdf = EasyDocsPDF()
        pdf.construir_desde_markdown(contenido)
        pdf_bytes = pdf.output(dest="S")

        return {
            "type": "file",
            "content": pdf_bytes,
            "mimetype": "application/pdf",
            "filename": f'doc_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf',
        }

    def _generar_docx(
        self, contenido, cache_stats=None, elapsed_time=0.0, from_cache=False
    ):
        """Genera y retorna un archivo DOCX."""
        logger.info(
            f"DOCX generado exitosamente (cache: {from_cache}, tiempo: {elapsed_time:.2f}s)"
        )
        logger.info(f"Estadísticas de cache: {cache_stats}")

        docx = EasyDocsDOCX()
        docx.agregar_encabezado()
        docx.construir_desde_markdown(contenido)

        output_stream = io.BytesIO()
        docx.guardar(output_stream)
        content_bytes = output_stream.getvalue()

        return {
            "type": "file",
            "content": content_bytes,
            "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "filename": f'doc_{datetime.now().strftime("%Y%m%d_%H%M")}.docx',
        }

    def _generar_zip_multifile(
        self, files_dict, cache_stats=None, elapsed_time=0.0
    ):
        logger.info(
            f"Multifile ZIP generado exitosamente ({len(files_dict)} documentos, "
            f"tiempo: {elapsed_time:.2f}s)"
        )
        logger.info(f"Estadísticas de cache: {cache_stats}")

        zip_bytes = self.zip_service.crear_zip(files_dict)

        return {
            "type": "file",
            "content": zip_bytes,
            "mimetype": "application/zip",
            "filename": f'documentacion_multifile_{datetime.now().strftime("%Y%m%d_%H%M")}.zip',
        }
