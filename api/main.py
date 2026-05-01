from flask import Flask, jsonify 
import logging
from .routes.download import download_routes 
from .routes.zip import zip_routes
from flask_cors import CORS

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_VERSION = "2.3.1"
app = Flask(__name__)
CORS(app)
app.json.sort_keys = False # esto hace que el JSON tenga el mismo orden que las claves de diccionarios



@app.route("/", methods=["GET"])
def welcome():
    return jsonify({
        "message": "Welcome to EasyDocs API!",
        "version": API_VERSION,
        "endpoints": [
            {
                "path": "/api/download",
                "method": "GET",
                "description": "Information about documentation download endpoints"
            },
            {
                "path": "/api/download/<file_type>",
                "method": "POST",
                "description": "Generates documentation in the specified format (pdf, markdown or docx)",
                "parameters": {
                    "file_type": "File type: 'pdf', 'markdown' or 'docx'",
                    "body": {
                        "code": "Source code to document (string)",
                        "extra": "Additional requirements (optional, string)",
                        "language": "Target language: 'es' or 'en' (optional, string or Accept-Language header)"
                    }
                }
            },
            {
                "path": "/api/preview-zip",
                "method": "POST",
                "description": "Preview contents of a ZIP file without generating documentation",
                "parameters": {
                    "file": "ZIP file to preview (form-data)"
                }
            },
            {
                "path": "/api/upload-zip",
                "method": "POST",
                "description": "Process a ZIP file and generate consolidated documentation",
                "parameters": {
                    "file": "ZIP file with source code (form-data)",
                    "doc_type": "Document type: 'markdown', 'pdf' or 'word' (optional)",
                    "extra_requirements": "Additional requirements for documentation (optional)",
                    "language": "Target language: 'es' or 'en' (optional, string or Accept-Language header)"
                }
            }
        ],
        "supported_formats": ["markdown", "pdf", "word"],
        "features": [
            "Intelligent cache by content hash",
            "Multilanguage support (Python/Java/JS)",
            "Automatic chunking for large projects",
            "Documentation generation in multiple formats"
        ]
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
