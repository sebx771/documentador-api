from flask import blueprints , request , jsonify , send_file , make_response
import logging
import time
from datetime import datetime
import io

from ..utils import bytes_utils
from ..export.pdf_gen import EasyDocsPDF
from ..export.docx_gen import EasyDocsDOCX
from ..services.zip_services import ZipService
from ..services.documentation_orchestrator import DocumentationOrchestrator
from ..services.chunking_service import ChunkingService
from ..services.cache_service import  get_global_cache



# Configurar logging

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
    
    # --- EXTRACCIÓN DE IDIOMA ---
    language = request.form.get('language') or request.headers.get('Accept-Language')
    if language:
        # Normalizar a los soportados: 'en' si contiene 'en', de lo contrario 'es'
        language = 'en' if 'en' in language.lower() else 'es'
        logger.info(f"Idioma forzado por cliente: {language}")
    
    try:
        zip_service = ZipService()
        chunking_service = ChunkingService()
        cache_service = get_global_cache(
            max_size=100,
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
            zip_service=zip_service,
            language=language
        )
        
        elapsed = time.time() - start_time
        cache_stats = result['metadata'].get('cache_stats', {})
        
        logger.info(
            f"ZIP procesado exitosamente: {result['metadata']['total_files']} archivos, "
            f"{result['metadata']['total_chunks']} chunks, "
            f"cache hit: {cache_stats.get('hits', 0)}, "
            f"time: {elapsed:.2f}s"
            f"error: {result['metadata'].get('invalid_files', [])}"
            f"doc_type: {doc_type}"
        )
        if doc_type == 'markdown':
            return _generar_markdown(result['documentation'], cache_stats, elapsed)
        if doc_type == 'pdf':
            return _generar_pdf(result['documentation'], cache_stats, elapsed)
        if doc_type == 'word':
            return _generar_docx(result['documentation'], cache_stats, elapsed)
        
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
    

def _generar_markdown(contenido, cache_stats=None, elapsed_time=0.0, from_cache=False):
    """Genera y retorna un archivo Markdown."""
    logger.info(f"Documentación Markdown generada exitosamente (cache: {from_cache}, time: {elapsed_time:.2f}s)")
    logger.info(f"Cache stats: {cache_stats}")
    archivo_virtual = bytes_utils.preparar_descarga(contenido)
    
    response = make_response(send_file(
        archivo_virtual,
        mimetype='text/markdown',
        as_attachment=True,
        download_name=f'documentacion_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.md'
    ))
    response.headers["Content-Disposition"] = f"attachment; filename=documentacion_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.md"
    return response


def _generar_pdf(contenido, cache_stats=None, elapsed_time=0.0, from_cache=False):
    """Genera y retorna un archivo PDF."""
    logger.info(f"PDF generado exitosamente (cache: {from_cache}, time: {elapsed_time:.2f}s)")
    logger.info(f"Cache stats: {cache_stats}")
    
    # Crear el PDF
    pdf = EasyDocsPDF()

    pdf.construir_desde_markdown(contenido)
    
    # Preparar descarga en memoria
    pdf_bytes = pdf.output(dest='S')
    archivo_virtual = bytes_utils.preparar_descarga(pdf_bytes)
    
    
    return send_file(
        archivo_virtual,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'doc_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
    )  

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
    output_stream.seek(0)
    
    return send_file(
        output_stream,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        as_attachment=True,
        download_name=f'doc_{datetime.now().strftime("%Y%m%d_%H%M")}.docx'
    )
