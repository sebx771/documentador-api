from flask import Blueprint, request, jsonify, send_file, make_response
from ..utils import validate, bytes_utils, get_request 
from ..services.ai_services import DocumentadorIA
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
    


download_routes = Blueprint('download', __name__)

@download_routes.route('/download',methods=['GET'])
def download_info():
    """"""
    return jsonify({
        "message": "Endpoint para descargar documentación",
        "available_formats": ["pdf", "markdown", "docx"],
        "usage": {
            "pdf": {
                "method": "POST",
                "route": "api/download/pdf",
                "description": "Genera un PDF con la documentación del código proporcionado"
            },
            "markdown": {
                "method": "POST",
                "route": "api/download/markdown",
                "description": "Genera un archivo Markdown con la documentación del código proporcionado"
            },
            "docx": {
                "method": "POST",
                "route": "api/download/docx",
                "description": "Genera un archivo Word (.docx) con la documentación del código proporcionado"
            }
        }
    })

@download_routes.route('/download/<file_type>', methods=['POST'])
def download(file_type):
    docs= documentador_ia()
    start_time = time.time()
    """
    Endpoint unificado para descargar documentación en diferentes formatos.
    
    Args:
        file_type: Tipo de archivo a generar ('pdf' o 'markdown')
    """
    try:
        # Validar tipo de archivo
        if file_type not in ['pdf', 'markdown', 'docx']:
            return jsonify({
                "error": "Tipo de archivo no válido. Use 'pdf' , 'markdown' o 'docx",
                "codigo_error": "INVALID_FILE_TYPE"
            }), 400

        # Obtener datos del request usando la utilidad
        data, extra = get_request.get_request_data(request)
        
        if data is None:
            logger.warning("Request sin contenido válido")
            return jsonify({
                "error": "El request debe ser JSON o contener un archivo",
                "codigo_error": "INVALID_CONTENT_TYPE"
            }), 400

        
        if hasattr(data, 'read'):
            # Es un archivo subido
            codigo_fuente = data.read().decode('utf-8')
        else:
            
            if 'codigo' not in data:
                logger.warning("Request sin campo 'codigo'")
                return jsonify({
                    "error": "El campo 'codigo' es requerido",
                    "codigo_error": "MISSING_FIELD"
                }), 400
            codigo_fuente = data.get('codigo', '')

        #debug
        logger.info(f"tipo de request{" file" if request.files else " json"}")
        logger.info(f"extra={extra}")
        # Validar el código
        is_valid, error_response = validate.validar_codigo(
            codigo_fuente, 
            logger, 
            MIN_CODE_LENGTH, 
            MAX_CODE_LENGTH
        )
        
        if not is_valid:
            return jsonify(error_response), 400

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
            resultado_markdown = docs.generar(codigo_fuente, tipo="markdown", extra=extra_str)
            
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
        return jsonify({
            "error": f"Error interno del servidor al generar documentación {file_type}",
            "codigo_error": "INTERNAL_SERVER_ERROR"
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
    pdf.add_page()
    pdf.construir_desde_markdown(contenido)
    
    # Preparar descarga en memoria
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    archivo_virtual = bytes_utils.preparar_descarga(pdf_bytes)
    
    return send_file(
        archivo_virtual,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'documentacion_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
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
