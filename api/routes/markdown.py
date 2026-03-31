from flask import Blueprint, request, jsonify , send_file , make_response
from utils import base , validate , bytes
from services.ai_services import DocumentadorIA
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_VERSION = "1.0.0"
MAX_CODE_LENGTH = 50000
MIN_CODE_LENGTH = 10
doc = DocumentadorIA()

markdown_routes = Blueprint('markdown', __name__)


@markdown_routes.route('/descargar-md', methods=['POST'])
def descargar_md():
    try:
        # Validar que el request tenga JSON
        if not request.is_json:
            logger.warning("Request sin contenido JSON")
            return jsonify({
                "error": "El request debe ser JSON",
                "codigo_error": "INVALID_CONTENT_TYPE"
            }), 400

        data = request.get_json()
        # Validar que exista el campo 'codigo'
        if 'codigo' not in data:
            logger.warning("Request sin campo 'codigo'")
            return jsonify({
                "error": "El campo 'codigo' es requerido",
                "codigo_error": "MISSING_FIELD"
            }), 400
        codigo_b64 = data.get('codigo', '')
        codigo_fuente = base.base64_to_string(codigo_b64)
        is_valid, error_response = validate.validar_codigo(codigo_fuente, logger, MIN_CODE_LENGTH, MAX_CODE_LENGTH)
        if not is_valid:
            return jsonify(error_response), 400
        
        logger.info("Generando documentación Markdown para el código recibido")
        p_markdown = doc._crear_prompt(codigo_fuente,tipo="markdown")
        resultado_markdown = doc.generar(p_markdown)
        archivo_virtual = bytes.preparar_descarga(resultado_markdown)
        
        logger.info("Documentación Markdown generada exitosamente")
        response= make_response( send_file(
            archivo_virtual,
            mimetype='text/markdown',
            as_attachment=True,
            download_name=f'documentacion_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.md'
        ))
        response.headers["Content-Dispotition"]= f"attachment; filename=documentacion_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.md"
        return response
    except Exception as e:
        # Error inesperado
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Error interno del servidor al generar documentación Markdown",
            "codigo_error": "INTERNAL_SERVER_ERROR"
        }), 500