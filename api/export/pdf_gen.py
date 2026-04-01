from fpdf import FPDF

class EasyDocsPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, 'Reporte de Documentación Técnica - easyDocs', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def agregar_titulo_seccion(self, titulo):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 51, 102) 
        self.cell(0, 10, titulo, ln=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def agregar_parrafo(self, texto):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 5, texto, align='J')
        self.ln(3)

    def agregar_item_lista(self, texto):
        self.set_font('Arial', '', 11)
        self.cell(10, 5, chr(149), align='C') 
        self.multi_cell(0, 5, texto)
        self.ln(1)

    def construir_desde_markdown(self, texto_ia):
        lineas = texto_ia.split('\n')
        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue
            
            if linea.startswith("###"):
                titulo = linea.replace("###", "").strip()
                self.agregar_titulo_seccion(titulo)
            elif linea.startswith("-"):
                item = linea.replace("-", "", 1).strip()
                self.agregar_item_lista(item)
            else:
                self.agregar_parrafo(linea)