from flask import Flask, send_file, request, jsonify 
from utils import bytes , base ,validate
from datetime import datetime
from services.ai_services import DocumentadorIA
import logging
from routes.markdown import markdown_routes
from routes.pdf import pdf_routes

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_VERSION = "1.1.0"
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
            },
            {
                "ruta": "/descargar-pdf",
                "metodo": "POST",
                "descripcion": "Genera documentación PDF"
            }
        ]
,
    })

# Registrar rutas
app.register_blueprint(markdown_routes)
app.register_blueprint(pdf_routes)

# Manejo de errores
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
