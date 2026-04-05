import re
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

class EasyDocsDOCX:
    """
    Clase para convertir Markdown  en un documento de Word (.docx).
    Ubicación: export/docx_gen.py
    """
    def __init__(self):
        self.doc = Document()
        self._configurar_estilos_base()

    def _configurar_estilos_base(self):
        """Configura la fuente y el tamaño base del doc."""
        style = self.doc.styles['Normal']
        font = style.font
        font.name = 'Arial'
        font.size = Pt(11)

    def agregar_encabezado(self):
        """Añade el sello institucional en la parte superior."""
        section = self.doc.sections[0]
        header = section.header
        # Si el encabezado está vacío, accedemos al primer párrafo
        p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        p.text = "Reporte de Documentación Técnica - easyDocs"
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Estilo para el texto del encabezado
        run = p.runs[0]
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(128, 128, 128)

    def construir_desde_markdown(self, texto_md):
        """ interpreta el Markdown y lo plasma en el documento."""
        lineas = texto_md.split('\n')
        en_bloque_codigo = False

        for linea in lineas:
            # 1. Detección de Bloques de Código (```)
            if linea.strip().startswith('```'):
                en_bloque_codigo = not en_bloque_codigo
                continue

            if en_bloque_codigo:
                self._agregar_linea_codigo(linea)
                continue

            # 2. Transformación de Títulos (##)
            if linea.strip().startswith('##'):
                titulo_limpio = re.sub(r'^#+\s*', '', linea)
                h = self.doc.add_heading(titulo_limpio, level=1)
                # Aplicamos el color azul institucional
                run = h.runs[0] if h.runs else h.add_run(titulo_limpio)
                run.font.color.rgb = RGBColor(31, 73, 125)
                run.font.name = 'Arial'
                continue

            # 3. Limpieza de residuos de Markdown
            # Eliminamos **, *, ` y símbolos # sueltos
            linea_limpia = re.sub(r'\*\*|\*|`|#', '', linea)

            # 4. Defensa contra tablas Markdown residuales (|---|)
            if re.match(r'^[\s|:-]*$', linea_limpia) and '|' in linea:
                continue
            
            linea_limpia = linea_limpia.replace('|', '  ').strip()

            # 5. Escritura del cuerpo del texto
            if not linea_limpia:
                self.doc.add_paragraph("") # Espacio en blanco
            else:
                p = self.doc.add_paragraph(linea_limpia)
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    def _agregar_linea_codigo(self, texto):
        """Añade una línea de código con fuente mono y fondo gris."""
        p = self.doc.add_paragraph()
        # Eliminamos el espacio entre párrafos de código para que parezca un bloque unido
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.space_before = Pt(0)
        
        run = p.add_run(texto)
        run.font.name = 'Courier New'
        run.font.size = Pt(9)
        
        #  XML para aplicar sombreado gris al párrafo
        shd = OxmlElement('w:shd')
        shd.set(qn('w:val'), 'clear')
        shd.set(qn('w:color'), 'auto')
        shd.set(qn('w:fill'), 'F0F0F0') # Gris claro
        p._element.get_or_add_pPr().append(shd)

    def guardar(self, output_stream):
        """Exporta el documento al flujo de bytes final."""
        self.doc.save(output_stream)