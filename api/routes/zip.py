from flask import blueprints , request , jsonify
import logging
import time

from ..services.zip_services import ZipService
from ..services.documentation_orchestrator import DocumentationOrchestrator
from ..services.chunking_service import ChunkingService
from ..services.cache_service import CacheService, get_global_cache

logger = logging.getLogger(__name__)

zip_routes = blueprints.Blueprint('zip', __name__)

MAX_ZIP_SIZE = 10 * 1024 * 1024


@zip_routes.route('/preview-zip', methods=['POST'])
def preview_zip():
    zip_service= ZipService()
    file= request.files.get('file')
    if not file:
      return jsonify({"error": "No se proporcionó ningún archivo .zip"}),400
    filename = file.filename or ""
    if not filename.endswith(".zip"):
      return  jsonify({"error": "Solo se permiten archivos .zip"}),400
    contenido_bytes= file.read()
    codigo= zip_service.listar_contenido_zip(contenido_bytes)
    return jsonify(codigo)


@zip_routes.route('/upload-zip', methods=['POST'])
def upload_zip():
    """
    Endpoint para procesar archivos ZIP y generar documentación automática.
    
    Request:
        - file: Archivo .zip con código fuente
        - doc_type (optional): 'markdown', 'pdf', 'word' (default: markdown)
        - extra_requirements (optional): Requisitos adicionales para la documentación
    
    Response:
        - documentation: Documentación generada
        - metadata: Stats sobre procesamiento (archivos, chunks, cache, tiempo)
        - errors: Archivos inválidos si los hay
    """
    start_time = time.time()
    
    file = request.files.get('file')
    
    if not file:
        logger.warning("Request sin archivo")
        return jsonify({
            "error": "No se proporcionó ningún archivo .zip",
            "codigo_error": "NO_FILE"
        }), 400
    
    filename = file.filename or ""
    if not filename or not filename.endswith('.zip'):
        logger.warning(f"Archivo inválido: {filename}")
        return jsonify({
            "error": "Solo se permiten archivos .zip",
            "codigo_error": "INVALID_FILE_TYPE"
        }), 400
    
    zip_content = file.read()
    input_size = len(zip_content)
    
    logger.info(f"ZIP recibido: {filename}, tamaño: {input_size} bytes")
    
    if input_size > MAX_ZIP_SIZE:
        logger.warning(f"Archivo demasiado grande: {input_size} bytes")
        return jsonify({
            "error": f"Archivo demasiado grande. Máximo: {MAX_ZIP_SIZE / (1024*1024)}MB",
            "codigo_error": "FILE_TOO_LARGE"
        }), 400
    
    if input_size == 0:
        return jsonify({
            "error": "Archivo vacío",
            "codigo_error": "EMPTY_FILE"
        }), 400
    
    doc_type = request.form.get('doc_type', 'markdown')
    if doc_type not in ['markdown', 'pdf', 'word']:
        return jsonify({
            "error": "Tipo de documento inválido. Use: markdown, pdf o word",
            "codigo_error": "INVALID_DOC_TYPE"
        }), 400
    
    extra_requirements = request.form.get('extra_requirements', '')
    
    try:
        zip_service = ZipService()
        chunking_service = ChunkingService(
            max_chunk_size=8000,
            max_files_per_chunk=10,
            max_tokens_estimate=12000
        )
        cache_service = get_global_cache(
            max_size=100,
            ttl_seconds=3600,
            enable_lru=True
        )
        
        orchestrator = DocumentationOrchestrator(
            max_input_size=MAX_ZIP_SIZE,
            max_files=50,
            chunking_service=chunking_service,
            cache_service=cache_service
        )
        
        result = orchestrator.process_zip(
            zip_content=zip_content,
            doc_type=doc_type,
            extra_requirements=extra_requirements,
            zip_service=zip_service
        )
        
        elapsed = time.time() - start_time
        cache_stats = result['metadata'].get('cache_stats', {})
        
        logger.info(
            f"ZIP procesado exitosamente: {result['metadata']['total_files']} archivos, "
            f"{result['metadata']['total_chunks']} chunks, "
            f"cache hit: {cache_stats.get('hits', 0)}, "
            f"time: {elapsed:.2f}s"
        )
        
        return jsonify({
            "success": True,
            "documentation": result['documentation'],
            "metadata": {
                "total_files": result['metadata']['total_files'],
                "invalid_files_count": result['metadata']['invalid_files_count'],
                "total_chunks": result['metadata']['total_chunks'],
                "cache": {
                    "hits": cache_stats.get('hits', 0),
                    "misses": cache_stats.get('misses', 0),
                    "hit_rate_percent": cache_stats.get('hit_rate_percent', 0)
                },
                "elapsed_time_seconds": result['metadata']['elapsed_time_seconds'],
                "input_size_bytes": result['metadata']['input_size_bytes']
            },
            "errors": {
                "files": result['metadata'].get('invalid_files', []),
                "count": result['metadata'].get('invalid_files_count', 0)
            }
        })
        
    except ValueError as e:
        logger.error(f"Error de validación: {str(e)}")
        return jsonify({
            "error": str(e),
            "codigo_error": "VALIDATION_ERROR"
        }), 400
        
    except Exception as e:
        logger.error(f"Error procesando ZIP: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"Error al procesar el archivo: {str(e)}",
            "codigo_error": "PROCESSING_ERROR"
        }), 500
    

