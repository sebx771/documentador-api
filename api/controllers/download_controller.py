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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes para validación
MAX_CODE_LENGTH = 50000
MIN_CODE_LENGTH = 10

# Inicializar servicios
doc = DocumentadorIA()
cache = get_global_cache(max_size=100)

def documentador_ia():
    global doc
    if  doc is None:
        doc = DocumentadorIA()
    return doc


def get_download_info():
    """Information endpoint for documentation download"""
    return {
        "message": "Documentation download endpoint",
        "available_formats": ["pdf", "markdown", "docx"],
        "usage": {
            "pdf": {
                "method": "POST",
                "route": "/api/download/pdf",
                "description": "Generates a PDF with documentation for the provided code",
                "body": {
                    "code": "Source code to document (required)",
                    "extra": "Additional requirements (optional)"
                }
            },
            "markdown": {
                "method": "POST",
                "route": "/api/download/markdown",
                "description": "Generates a Markdown file with documentation for the provided code",
                "body": {
                    "code": "Source code to document (required)",
                    "extra": "Additional requirements (optional)"
                }
            },
            "docx": {
                "method": "POST",
                "route": "/api/download/docx",
                "description": "Generates a Word (.docx) file with documentation for the provided code",
                "body": {
                    "code": "Source code to document (required)",
                    "extra": "Additional requirements (optional)"
                }
            }
        },
        "limits": {
            "max_code_length": MAX_CODE_LENGTH,
            "min_code_length": MIN_CODE_LENGTH
        }
    }


def process_download(file_type, codigo_fuente, extra, language):
    docs = documentador_ia()
    
    start_time = time.time()
    """
    Process download for documentation in different formats.
    
    Args:
        file_type: File type ('pdf', 'markdown', 'docx')
        codigo_fuente: Source code string
        extra: Additional requirements
        language: Language preference ('en', 'es', or None)
    """
    try:
        # Validar tipo de archivo
        if file_type not in ['pdf', 'markdown', 'docx']:
            return {
                'type': 'json',
                'data': {
                    "error": "Tipo de archivo no valido. Use 'pdf' , 'markdown' o 'docx",
                    "codigo_error": "INVALID_FILE_TYPE"
                },
                'status': 400
            }

        # Validar el código
        from ..utils import validate
        is_valid, error_response = validate.validar_codigo(
            codigo_fuente, 
            logger, 
            MIN_CODE_LENGTH, 
            MAX_CODE_LENGTH
        )
        
        if not is_valid:
            return {
                'type': 'json',
                'data': error_response,
                'status': 400
            }

        # Cache: generar hash y buscar en Redis
        extra_str = (extra or "").strip().lower()
        cache_key = cache.generate_hash(
            content=codigo_fuente,
            doc_type=file_type,
            extra_requirements=extra_str
        )
        
        cached_result = cache.get(cache_key)
        
        logger.info(f"Cache key: {cache_key[:16]}...")
        
        if cached_result:
            logger.info(f"Cache HIT para código: {len(codigo_fuente)} chars")
            resultado_markdown = cached_result.get("documentation", "")
            from_cache = True
        else:
            logger.info(f"Cache MISS, generando con IA...")
            # Generar documentación con IA
            logger.info(f"Generando documentación {file_type} para el código recibido")
            resultado_markdown = docs.generar(codigo_fuente, tipo="markdown", extra=extra_str, lang=language)
            
            cache.set(cache_key, {
                "documentation": resultado_markdown,
                "file_type": file_type
            })
            from_cache = False

        elapsed_time = time.time() - start_time
        cache_stats = cache.get_stats()

        # Generar archivo según el tipo solicitado
        if file_type == 'markdown':
            return _generar_markdown(resultado_markdown, cache_stats, elapsed_time, from_cache)
        elif file_type == 'pdf':
            return _generar_pdf(resultado_markdown, cache_stats, elapsed_time, from_cache)
        elif file_type == 'docx':
            return _generar_docx(resultado_markdown, cache_stats, elapsed_time, from_cache)

    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        return {
            'type': 'json',
            'data': {
                "error": f"Error interno del servidor al generar documentación {file_type}",
                "codigo_error": "INTERNAL_SERVER_ERROR"
            },
            'status': 500
        }

def _generar_markdown(contenido, cache_stats=None, elapsed_time=0.0, from_cache=False):
    """Genera y retorna un archivo Markdown."""
    logger.info(f"Documentación Markdown generada exitosamente (cache: {from_cache}, time: {elapsed_time:.2f}s)")
    logger.info(f"Cache stats: {cache_stats}")
    from ..utils import bytes_utils
    content_bytes = bytes_utils.preparar_descarga(contenido)
    
    return {
        'type': 'file',
        'content': content_bytes,
        'mimetype': 'text/markdown',
        'filename': f'documentacion_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.md'
    }

def _generar_pdf(contenido, cache_stats=None, elapsed_time=0.0, from_cache=False):
    """Genera y retorna un archivo PDF."""
    logger.info(f"PDF generado exitosamente (cache: {from_cache}, time: {elapsed_time:.2f}s)")
    logger.info(f"Cache stats: {cache_stats}")
    
    # Crear el PDF
    pdf = EasyDocsPDF()
    pdf.construir_desde_markdown(contenido)
    
    # Preparar descarga en memoria
    pdf_bytes = pdf.output(dest='S')
    from ..utils import bytes_utils
    content_bytes = bytes_utils.preparar_descarga(pdf_bytes)
    
    return {
        'type': 'file',
        'content': content_bytes,
        'mimetype': 'application/pdf',
        'filename': f'documentacion_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
    }
    

def _generar_docx(contenido, cache_stats=None, elapsed_time=0.0, from_cache=False):
    """Genera y retorna un archivo DOCX."""
    logger.info(f"DOCX generado exitosamente (cache: {from_cache}, time: {elapsed_time:.2f}s)")
    logger.info(f"Cache stats: {cache_stats}")
    
    # Crear el DOCX
    docx = EasyDocsDOCX()
    docx.agregar_encabezado()
    docx.construir_desde_markdown(contenido)
    
    # Preparar descarga en memoria
    output_stream = io.BytesIO()
    docx.guardar(output_stream)
    content_bytes = output_stream.getvalue()
    
    return {
        'type': 'file',
        'content': content_bytes,
        'mimetype': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'filename': f'doc_{datetime.now().strftime("%Y%m%d_%H%M")}.docx'
    }
