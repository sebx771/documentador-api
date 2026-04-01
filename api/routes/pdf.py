from flask import Blueprint, request, jsonify, send_file
from utils import base, validate
from services.ai_services import DocumentadorIA
from export.pdf_gen import EasyDocsPDF
from datetime import datetime
import io
import logging

# Configuración inicial
pdf_routes = Blueprint('pdf', __name__)
doc = DocumentadorIA()
logger = logging.getLogger(__name__)

# Constantes necesarias para la validación
MAX_CODE_LENGTH = 50000
MIN_CODE_LENGTH = 10

@pdf_routes.route('/descargar-pdf', methods=['POST'])
def descargar_pdf():
    try:
        # 1. Obtener y decodificar datos
        data = request.get_json()
        if not data or 'codigo' not in data:
            return jsonify({"error": "Falta el campo 'codigo'", "codigo_error": "MISSING_FIELD"}), 400

        codigo_b64 = data.get('codigo', '')
        codigo_fuente = base.base64_to_string(codigo_b64)

        # 2. Validar el código (Usando tu utilidad)
        is_valid, error_response = validate.validar_codigo(
            codigo_fuente, 
            logger, 
            MIN_CODE_LENGTH, 
            MAX_CODE_LENGTH
        )

        if not is_valid:
            logger.warning(f"Validación fallida: {error_response}")
            return jsonify(error_response), 400

        # 3. Generar documentación con IA
        logger.info("Generando documentación PDF...")
        p_markdown = doc._crear_prompt(codigo_fuente, tipo="markdown")
        resultado_ia = doc.generar(p_markdown)

        # 4. Crear el PDF
        pdf = EasyDocsPDF()
        pdf.add_page()
        pdf.construir_desde_markdown(resultado_ia)

        # 5. Preparar descarga en memoria
       # Convertimos el string a bytes usando latin-1
        pdf_bytes = pdf.output(dest='S').encode('latin-1') 
        archivo_virtual = io.BytesIO(pdf_bytes)
        archivo_virtual.seek(0)

        logger.info("PDF generado exitosamente")

        return send_file(
            archivo_virtual,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'doc_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
        )

    except Exception as e:
        logger.error(f"Error en PDF: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Error interno al generar PDF",
            "codigo_error": "INTERNAL_ERROR"
        }), 500