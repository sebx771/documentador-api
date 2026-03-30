from flask import Flask, send_file, request, jsonify , config , json
from utils import bytes , base
from datetime import datetime
from services.ai_services import DocumentadorIA
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_VERSION = "1.0.0"
doc = DocumentadorIA()

app = Flask(__name__)
app.json.sort_keys = False # esto hace que el JSON tenga el mismo orden que las claves de diccionarios

# Constantes de validación
MAX_CODE_LENGTH = 50000
MIN_CODE_LENGTH = 10

@app.route("/", methods=["GET"])
def welcome():
    return jsonify({
        "mensaje": "¡Bienvenido a EasyDocs API!",
        "version": API_VERSION,
        "endpoints": [
    {
        "ruta": "/descargar-md",
        "metodo": "POST",
        "descripcion": "Genera documentación Markdown"
    }
],
    })

@app.route('/descargar-md', methods=['POST'])
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
        
        is_valid, error_response = bytes.validar_codigo(codigo_fuente, logger, MIN_CODE_LENGTH, MAX_CODE_LENGTH)
        
        if not is_valid:
            return jsonify(error_response), 400
        
        

        logger.info(f"Generando documentación para código de {len(codigo_fuente)} caracteres")
        
        # Generar documentación
        contenido_ia = doc._crear_prompt(codigo_fuente, tipo="markdown")
        resp = doc.generar(contenido_ia)
        
        # Validar que la respuesta no esté vacía
        if not resp or not resp.strip():
            logger.error("La IA devolvió una respuesta vacía")
            return jsonify({
                "error": "No se pudo generar la documentación",
                "codigo_error": "EMPTY_RESPONSE"
            }), 500

        archivo_virtual = bytes.preparar_descarga(resp)
        
        logger.info("Documentación generada exitosamente")
        
        return send_file(
            archivo_virtual,
            mimetype='text/markdown',
            as_attachment=True,
            download_name=f'documentacion_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.md'
        )

    except ValueError as e:
      
        logger.error(f"Error de validación: {str(e)}")
        return jsonify({
            "error": str(e),
            "codigo_error": "VALIDATION_ERROR"
        }), 400

    except Exception as e:
        # Error inesperado
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Error interno del servidor al generar documentación",
            "codigo_error": "INTERNAL_ERROR"
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "error": "Endpoint no encontrado",
        "codigo_error": "NOT_FOUND"
    }), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({
        "error": "Método HTTP no permitido",
        "codigo_error": "METHOD_NOT_ALLOWED"
    }), 405

if __name__ == "__main__":
    app.run(debug=True)
