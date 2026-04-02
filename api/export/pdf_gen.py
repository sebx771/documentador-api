from fpdf import FPDF
import re

class EasyDocsPDF(FPDF):
    """
    Clase refinada para exorcizar el Markdown y manifestarlo en el plano físico del PDF.
    He eliminado 'FpdfInherit' porque ya estás heredando de FPDF directamente.
    """
    
    def header(self):
        # Encabezado con energía institucional
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, 'Reporte de Documentación Técnica ', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        # Sello de pie de página para rastrear el flujo de páginas
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def construir_desde_markdown(self, texto_md):
        """
        Ritual de Transmutación: Convierte el caos del Markdown en orden PDF.
        """
        lineas = texto_md.split('\n')
        en_bloque_codigo = False

        for linea in lineas:
            # 1. El Dominio del Código (```)
            # Si detectamos las comillas triples, entramos o salimos del estado de vacío
            if linea.strip().startswith('```'):
                en_bloque_codigo = not en_bloque_codigo
                continue 
            
            if en_bloque_codigo:
                self.set_font('Courier', '', 10)
                self.set_fill_color(240, 240, 240) # Fondo gris de protección
                # Imprimimos el código con un ligero margen para que no toque los bordes
                self.multi_cell(0, 5, linea, fill=True)
                continue

            # 2. Exorcismo de Títulos (##)
            if linea.strip().startswith('##'):
                self.ln(5) # Espacio de respeto antes del título
                self.set_font('Arial', 'B', 14)
                self.set_text_color(31, 73, 125) 
                
                # Eliminamos los restos de la maldición '##'
                titulo_limpio = re.sub(r'^#+\s*', '', linea)
                self.multi_cell(0, 10, titulo_limpio)
                
                self.set_text_color(0, 0, 0) # Retorno al equilibrio (negro)
                self.ln(2)
                continue

            # 3. Purificación de Caracteres (Negritas, Itálicas y Código inline)
            # Eliminamos **, *, ` y los # que sobran
            linea_limpia = re.sub(r'\*\*|\*|`|#', '', linea)

            # 4. Barrera contra Tablas de Markdown (|---|)
            # Si la línea es solo decorativa de tabla, la desintegramos
            if re.match(r'^[\s|:-]*$', linea_limpia) and '|' in linea:
                continue
            
            # Limpiamos las barras laterales si es una fila de datos para que sea legible
            linea_limpia = linea_limpia.replace('|', '  ').strip()

            # 5. Manifestación del Cuerpo del Texto
            self.set_font('Arial', '', 11)
            if not linea_limpia:
                self.ln(3) # Salto de línea por vacío
            else:
                # Dibujamos el texto final ya purificado
                self.multi_cell(0, 7, linea_limpia)