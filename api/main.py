from flask import Flask, jsonify 
import logging
from .routes.download import download_routes 
from .routes.zip import zip_routes



# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_VERSION = "1.1.0"
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
                "ruta": "/download/<file_type>",
                "metodo": "POST",
                "descripcion": "Genera documentación en el formato especificado (pdf o markdown)",
                "parametros": {
                    "file_type": "Tipo de archivo: 'pdf' o 'markdown'"
                }
            }
        ]
,
    })

# Registrar rutas
app.register_blueprint(download_routes, url_prefix='/api')
app.register_blueprint(zip_routes, url_prefix='/api')

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
