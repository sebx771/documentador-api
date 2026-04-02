from flask import Blueprint, request, jsonify, send_file, make_response
from utils import validate, bytes, get_request
from services.ai_services import DocumentadorIA
from export.pdf_gen import EasyDocsPDF
from datetime import datetime
import io
import logging

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

download_routes = Blueprint('download', __name__)


@download_routes.route('/download/<file_type>', methods=['POST'])
def download(file_type):
    """
    Endpoint unificado para descargar documentación en diferentes formatos.
    
    Args:
        file_type: Tipo de archivo a generar ('pdf' o 'markdown')
    """
    try:
        # Validar tipo de archivo
        if file_type not in ['pdf', 'markdown']:
            return jsonify({
                "error": "Tipo de archivo no válido. Use 'pdf' o 'markdown'",
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

        # Determinar si es archivo o JSON
        if hasattr(data, 'read'):
            # Es un archivo subido
            codigo_fuente = data.read().decode('utf-8')
        else:
            # Es JSON, verificar campo 'codigo'
            if 'codigo' not in data:
                logger.warning("Request sin campo 'codigo'")
                return jsonify({
                    "error": "El campo 'codigo' es requerido",
                    "codigo_error": "MISSING_FIELD"
                }), 400
            codigo_fuente = data.get('codigo', '')
        
        # Validar el código
        is_valid, error_response = validate.validar_codigo(
            codigo_fuente, 
            logger, 
            MIN_CODE_LENGTH, 
            MAX_CODE_LENGTH
        )
        
        if not is_valid:
            return jsonify(error_response), 400

        # Generar documentación con IA
        logger.info(f"Generando documentación {file_type} para el código recibido")
        p_markdown = doc._build_system_prompt(tipo="markdown")
        resultado_markdown = doc.generar(codigo_fuente, tipo="markdown", extra=extra)

        # Generar archivo según el tipo solicitado
        if file_type == 'markdown':
            return _generar_markdown(resultado_markdown)
        elif file_type == 'pdf':
            return _generar_pdf(resultado_markdown)

    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"Error interno del servidor al generar documentación {file_type}",
            "codigo_error": "INTERNAL_SERVER_ERROR"
        }), 500


def _generar_markdown(contenido):
    """Genera y retorna un archivo Markdown."""
    logger.info("Documentación Markdown generada exitosamente")
    archivo_virtual = bytes.preparar_descarga(contenido)
    
    response = make_response(send_file(
        archivo_virtual,
        mimetype='text/markdown',
        as_attachment=True,
        download_name=f'documentacion_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.md'
    ))
    response.headers["Content-Disposition"] = f"attachment; filename=documentacion_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.md"
    return response


def _generar_pdf(contenido):
    """Genera y retorna un archivo PDF."""
    logger.info("PDF generado exitosamente")
    
    # Crear el PDF
    pdf = EasyDocsPDF()
    pdf.add_page()
    pdf.construir_desde_markdown(contenido)
    
    # Preparar descarga en memoria
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    archivo_virtual = io.BytesIO(pdf_bytes)
    archivo_virtual.seek(0)
    
    return send_file(
        archivo_virtual,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'doc_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
    )
