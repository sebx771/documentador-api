import io
from flask import Blueprint, request, jsonify, send_file
import logging
from ..controllers.zip_controller import ZipController

# Configurar logging
logger = logging.getLogger(__name__)

zip_routes = Blueprint('zip', __name__)
controller = ZipController()

@zip_routes.route('/preview-zip', methods=['POST'])
def preview_zip():
    file = request.files.get('file')
    result = controller.preview_zip(file)
    
    if result['type'] == 'json':
        return jsonify(result['data']), result.get('status', 200)
    
    return jsonify({"error": "Unexpected response type"}), 500

@zip_routes.route('/upload-zip', methods=['POST'])
def upload_zip():
    """
    Endpoint para procesar archivos ZIP y generar documentación automática.
    """
    file = request.files.get('file')
    doc_type = request.form.get('doc_type', 'markdown')
    extra_requirements = request.form.get('extra_requirements', '')
    
    # --- EXTRACCIÓN DE IDIOMA ---
    language = request.form.get('language') or request.headers.get('Accept-Language')
    if language:
        # Normalizar a los soportados: 'en' si contiene 'en', de lo contrario 'es'
        language = 'en' if 'en' in language.lower() else 'es'
        logger.info(f"Idioma detectado/forzado: {language}")

    result = controller.upload_zip(
        file=file,
        doc_type=doc_type,
        extra_requirements=extra_requirements,
        language=language
    )
    
    if result['type'] == 'json':
        return jsonify(result['data']), result.get('status', 200)
    elif result['type'] == 'file':
        return send_file(
            io.BytesIO(result['content']),
            mimetype=result['mimetype'],
            as_attachment=True,
            download_name=result['filename']
        )
    
    return jsonify({"error": "Unexpected response type"}), 500
