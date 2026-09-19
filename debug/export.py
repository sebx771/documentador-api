import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.export.pdf_gen import EasyDocsPDF
from api.export.docx_gen import EasyDocsDOCX

sample_md = """
# Test Document
This is a test of the new export system.

## Code Block Test
```python
def hello_world():
    print("Hello, easyDocs!")
```

## Table Test
| Feature | Supported | Quality |
| :--- | :---: | ---: |
| Markdown | Yes | High |
| Tables | Yes | Modern |
| Code | Yes | Styled |

## List Test
* Item 1
* Item 2
* Item 3

## Typography Test
**Bold text**, *italic text*, and `inline code`.
"""

def test_pdf():
    print("Testing PDF generation...")
    try:
        pdf = EasyDocsPDF()
        pdf.construir_desde_markdown(sample_md)
        pdf_bytes = pdf.output()
        output_path = os.path.join(os.path.dirname(__file__), "test_output.pdf")
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)
        print(f"PDF saved to {output_path}")
    except Exception as e:
        print(f"Error testing PDF: {e}")
        import traceback
        traceback.print_exc()

def test_docx():
    print("Testing DOCX generation...")
    try:
        docx = EasyDocsDOCX()
        docx.agregar_encabezado()
        docx.construir_desde_markdown(sample_md)
        output_path = os.path.join(os.path.dirname(__file__), "test_output.docx")
        with open(output_path, "wb") as f:
            docx.guardar(f)
        print(f"DOCX saved to {output_path}")
    except Exception as e:
        print(f"Error testing DOCX: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf()
    test_docx()
