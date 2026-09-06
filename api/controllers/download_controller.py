from ..services.ai import DocumentadorIA
from ..services.cache_service import get_global_cache
from ..export.pdf_gen import EasyDocsPDF
from ..export.docx_gen import EasyDocsDOCX
from datetime import datetime
import io
import logging
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constantes para validación
MAX_CODE_LENGTH = 50000
MIN_CODE_LENGTH = 10


class DownloadController:
    def __init__(self):
        self.doc = DocumentadorIA()
        self.cache = get_global_cache(max_size=100)
        self.max_code_length = MAX_CODE_LENGTH
        self.min_code_length = MIN_CODE_LENGTH

    def get_download_info(self):
        """Endpoint de información para la descarga de documentación"""
        return {
            "message": "Documentation download endpoint",
            "formats": ["pdf", "markdown", "docx"],
            "usage": {
                "pdf": {
                    "method": "POST",
                    "path": "/api/download/pdf",
                    "description": "Generates a PDF with the documentation of the provided code",
                    "body": {
                        "code": "Source code to document (required)",
                        "extra": "Additional requirements (optional)",
                    },
                },
                "markdown": {
                    "method": "POST",
                    "path": "/api/download/markdown",
                    "description": "Generates a Markdown file with the documentation of the provided code",
                    "body": {
                        "code": "Source code to document (required)",
                        "extra": "Additional requirements (optional)",
                    },
                },
                "docx": {
                    "method": "POST",
                    "path": "/api/download/docx",
                    "description": "Generates a Word file (.docx) with the documentation of the provided code",
                    "body": {
                        "code": "Source code to document (required)",
                        "extra": "Additional requirements (optional)",
                    },
                },
            },
            "limits": {
                "max_code_length": self.max_code_length,
                "min_code_length": self.min_code_length,
            },
        }

    def process_download(self, file_type, codigo_fuente, extra, language):
        """
        Procesa la descarga de documentación en diferentes formatos.

        Args:
            file_type: Tipo de archivo ('pdf', 'markdown', 'docx')
            codigo_fuente: Cadena con el código fuente
            extra: Requisitos adicionales
            language: Preferencia de idioma ('en', 'es', o None)
        """
        start_time = time.time()
        try:
            # Validar tipo de archivo
            if file_type not in ["pdf", "markdown", "docx"]:
                return {
                    "type": "json",
                    "data": {
                        "error": "Tipo de archivo no válido. Use 'pdf', 'markdown' o 'docx'",
                        "codigo_error": "INVALID_FILE_TYPE",
                    },
                    "status": 400,
                }

            # Validar el código
            from ..utils import validate

            is_valid, error_response = validate.validar_codigo(
                codigo_fuente, logger, self.min_code_length, self.max_code_length
            )

            if not is_valid:
                return {"type": "json", "data": error_response, "status": 400}

            # Cache: generar hash y buscar en Redis
            extra_str = (extra or "").strip().lower()
            cache_key = self.cache.generate_hash(
                content=codigo_fuente, doc_type=file_type, extra_requirements=extra_str
            )

            cached_result = self.cache.get(cache_key)

            logger.info(f"Key de cache: {cache_key[:16]}...")

            if cached_result:
                logger.info(f"Cache HIT para código: {len(codigo_fuente)} caracteres")
                resultado_markdown = cached_result.get("documentation", "")
                from_cache = True
            else:
                logger.info(f"Cache MISS, generando con IA...")
                # Generar documentación con IA
                logger.info(
                    f"Generando documentación {file_type} para el código recibido"
                )
                resultado_markdown = self.doc.generar(
                    codigo_fuente, tipo="markdown", extra=extra_str, lang=language
                )

                self.cache.set(
                    cache_key,
                    {"documentation": resultado_markdown, "file_type": file_type},
                )
                from_cache = False

            elapsed_time = time.time() - start_time
            cache_stats = self.cache.get_stats()

            # Generar archivo según el tipo solicitado
            if file_type == "markdown":
                return self._generar_markdown(
                    resultado_markdown, cache_stats, elapsed_time, from_cache
                )
            elif file_type == "pdf":
                return self._generar_pdf(
                    resultado_markdown, cache_stats, elapsed_time, from_cache
                )
            elif file_type == "docx":
                return self._generar_docx(
                    resultado_markdown, cache_stats, elapsed_time, from_cache
                )

        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}", exc_info=True)
            return {
                "type": "json",
                "data": {
                    "error": f"Error interno del servidor al generar documentación {file_type}",
                    "codigo_error": "INTERNAL_SERVER_ERROR",
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

        # Crear el PDF
        pdf = EasyDocsPDF()
        pdf.construir_desde_markdown(contenido)

        # Preparar descarga en memoria
        pdf_bytes = pdf.output(dest="S")

        return {
            "type": "file",
            "content": pdf_bytes,
            "mimetype": "application/pdf",
            "filename": f'documentacion_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf',
        }

    def _generar_docx(
        self, contenido, cache_stats=None, elapsed_time=0.0, from_cache=False
    ):
        """Genera y retorna un archivo DOCX."""
        logger.info(
            f"DOCX generado exitosamente (cache: {from_cache}, tiempo: {elapsed_time:.2f}s)"
        )
        logger.info(f"Estadísticas de cache: {cache_stats}")

        # Crear el DOCX
        docx = EasyDocsDOCX()
        docx.agregar_encabezado()
        docx.construir_desde_markdown(contenido)

        # Preparar descarga en memoria
        output_stream = io.BytesIO()
        docx.guardar(output_stream)
        content_bytes = output_stream.getvalue()

        return {
            "type": "file",
            "content": content_bytes,
            "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "filename": f'doc_{datetime.now().strftime("%Y%m%d_%H%M")}.docx',
        }
