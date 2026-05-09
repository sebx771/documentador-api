from flask import Blueprint, request, jsonify, send_file
from ..utils import get_request
from ..controllers.download_controller import get_download_info, process_download

download_routes = Blueprint('download', __name__)

@download_routes.route('/download',methods=['GET'])
def download_info():
    data = get_download_info()
    return jsonify(data)

@download_routes.route('/download/<file_type>', methods=['POST'])
def download(file_type):
    # Obtener datos del request
    data, extra = get_request.get_request_data(request)
    
    # Extraer código fuente
    if hasattr(data, 'read'):
        codigo_fuente = data.read().decode('utf-8')
    else:
        codigo_fuente = data.get('codigo', '')
    
    # Extraer idioma
    language = data.get('language') if isinstance(data, dict) else None
    language = language or request.headers.get('Accept-Language')
    if language:
        language = 'en' if 'en' in language.lower() else 'es'
    
    result = process_download(file_type, codigo_fuente, extra, language)
    
    if result['type'] == 'json':
        return jsonify(result['data']), result.get('status', 200)
    elif result['type'] == 'file':
        return send_file(
            result['content'],
            mimetype=result['mimetype'],
            as_attachment=True,
            download_name=result['filename']
        )
