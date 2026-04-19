from markdown_pdf import MarkdownPdf, Section
import io

class EasyDocsPDF:
    """
    Clase modernizada para convertir Markdown en PDF usando markdown-pdf.
    Soporta tablas, bloques de código y diseño responsivo basado en CSS.
    """
    
    def __init__(self):
        self.pdf = MarkdownPdf(toc_level=2)
        # Diseño moderno con CSS
        self.css = """
            @page {
                margin: 25mm;
            }
            body { 
                font-family: 'Helvetica', 'Arial', sans-serif; 
                line-height: 1.6; 
                color: #333; 
            }
            h1, h2 { 
                color: #1f497d; 
                border-bottom: 1px solid #eee; 
                padding-bottom: 8px;
                margin-top: 24px;
            }
            h3 {
                color: #2e75b6;
            }
            code { 
                background-color: #f4f4f4; 
                padding: 2px 4px; 
                border-radius: 3px; 
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
                color: #d63384;
            }
            pre { 
                background-color: #f8f9fa; 
                border-left: 4px solid #1f497d;
                padding: 12px; 
                overflow-x: auto;
                margin: 16px 0;
            }
            pre code { 
                background-color: transparent; 
                padding: 0; 
                color: #212529;
            }
            table { 
                width: 100%; 
                border-collapse: collapse; 
                margin: 20px 0; 
            }
            th { 
                background-color: #f2f2f2; 
                border: 1px solid #ddd; 
                padding: 10px; 
                text-align: left;
                font-weight: bold;
            }
            td { 
                border: 1px solid #ddd; 
                padding: 8px; 
            }
            tr:nth-child(even) {
                background-color: #fafafa;
            }
            .header {
                text-align: center;
                font-size: 10pt;
                color: #888;
                border-bottom: 0.5pt solid #ccc;
                margin-bottom: 20px;
                padding-bottom: 5px;
            }
        """

    def construir_desde_markdown(self, texto_md):
        """
        Convierte el Markdown en una sección del PDF con estilos modernos.
        """
        # Añadimos un encabezado visual al HTML
        header_html = '<div class="header">Reporte de Documentación Técnica - easyDocs</div>'
        
        # Combinamos el encabezado con el contenido (el contenido será parseado de MD a HTML por la librería)
        # Nota: La librería markdown-pdf procesa el texto de la Sección como Markdown.
        # Para incluir HTML puro, podemos usar etiquetas HTML dentro del MD si el parser lo permite
        # o simplemente confiar en que el parser maneja bien el contenido.
        
        contenido_completo = f"{header_html}\n\n{texto_md}"
        self.pdf.add_section(Section(contenido_completo), user_css=self.css)

    def output(self, dest='S'):
        """
        Retorna el contenido del PDF. 
        Para mantener compatibilidad con la firma anterior, aceptamos 'dest'.
        """
        buffer = io.BytesIO()
        self.pdf.save(buffer)
        return buffer.getvalue()