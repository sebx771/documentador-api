# Documentación del Proyecto

## Descripción general de la API
Servicio REST basado en Flask que permite generar documentación automática a partir de fragmentos de código fuente.  
Soporta tres formatos de salida: **PDF**, **Markdown** y **DOCX**.  
Incluye caché de resultados (hash de contenido + tipo + requisitos) para evitar llamadas redundantes a la IA.

Módulo Flask que expone dos rutas para trabajar con archivos **ZIP** que contienen código fuente.  
- `POST /preview-zip` devuelve la lista de archivos contenidos.  
- `POST /upload-zip` procesa el ZIP y genera documentación en **markdown**, **PDF** o **DOCX**.  

Se apoya en servicios de orquestación, chunking y caché para optimizar el procesamiento y reutilizar resultados.

El módulo **api.services.ai_services** expone la clase `DocumentadorIA`, que actúa como fachada para generar documentación técnica a partir de fragmentos de código fuente. Utiliza la API de Groq para invocar modelos de lenguaje (por defecto `llama-3.3-70b-versatile`) y un modelo secundario para aplicar ediciones adicionales.

`ZipService` brinda funcionalidades para inspeccionar y manipular archivos ZIP que contienen código fuente. El foco principal es listar el contenido del ZIP, filtrar por extensiones permitidas y carpetas/archivos ignorados, y validar cada elemento.

### Endpoints

#### `GET /download`
- **Propósito**: Información estática sobre el punto de descarga.
- **Respuesta** (`application/json`):
  ```json
  {
    "message": "Documentation download endpoint",
    "available_formats": ["pdf", "markdown", "docx"],
    "usage": {
      "pdf": {
        "method": "POST",
        "route": "/api/download/pdf",
        "description": "Genera un PDF con la documentación del código recibido",
        "body": {
          "code": "Source code to document (required)",
          "extra": "Additional requirements (optional)"
        }
      },
      "markdown": { /* idem */ },
      "docx": { /* idem */ }
    },
    "limits": {
      "max_code_length": 50000,
      "min_code_length": 10
    }
  }
  ```

#### `POST /download/<file_type>`
- **`<file_type>`**: `pdf`, `markdown` o `docx`.  
- **Cuerpo** (`application/json` o `multipart/form-data`):
  - `code` **(string, obligatorio)** – fragmento de código fuente a documentar.  
  - `extra` **(string, opcional)** – requisitos adicionales que la IA debe considerar.  
- **Flujo interno**:
  1. Validación del tipo de archivo.  
  2. Extracción de datos mediante `get_request.get_request_data`.  
  3. Validación de longitud mediante `validate.validar_codigo`.  
  4. Generación de **cache key** con `cache.generate_hash`.  
  5. Si la clave está en caché → se devuelve la documentación almacenada; de lo contrario, se invoca `DocumentadorIA.generar`.  
  6. Según `file_type`, se delega a:
     - `_generar_markdown`
     - `_generar_pdf`
     - `_generar_docx`
- **Respuesta**: Archivo adjunto (`Content‑Disposition: attachment`) con nombre `documentacion_YYYY-MM-DD_HH-MM.<ext>`.

**Ejemplo de petición (Python requests)**:
```python
import requests

url = "http://localhost:5000/api/download/pdf"
payload = {"code": "def foo(): pass", "extra": "incluye ejemplos"}
r = requests.post(url, json=payload)

with open("doc.pdf", "wb") as f:
    f.write(r.content)
```

---

### Servicios internos
| Servicio / Módulo | Responsabilidad | Funciones clave |
|-------------------|-----------------|-----------------|
| `DocumentadorIA` (services/ai_services) | Interfaz con modelo de IA que genera documentación en formato Markdown. | `generar(codigo, tipo="markdown", extra="")` |
| `CacheService` (services/cache_service) | Caché en memoria (posible backend Redis). | `generate_hash(content, doc_type, extra_requirements)`, `get(key)`, `set(key, value)`, `get_stats()` |
| `EasyDocsPDF` (export/pdf_gen) | Conversor de Markdown → PDF usando FPDF. | `add_page()`, `construir_desde_markdown(md)` |
| `EasyDocsDOCX` (export/docx_gen) | Conversor de Markdown → DOCX usando python‑docx. | `agregar_encabezado()`, `construir_desde_markdown(md)`, `guardar(stream)` |
| `validate` (utils) | Reglas de negocio sobre longitud y contenido del código. | `validar_codigo(codigo, logger, min_len, max_len)` |
| `bytes_utils` (utils) | Preparación de objetos `BytesIO` para `send_file`. | `preparar_descarga(bytes_or_str)` |
| `get_request` (utils) | Normaliza la extracción de datos de `request`. | `get_request_data(request)` |

---

### Guía de integración
1. **Instalar dependencias** (asumiendo `requirements.txt` incluye Flask, requests, etc.):
   ```bash
   pip install -r requirements.txt
   ```

2. **Registrar el Blueprint** en la aplicación Flask principal:
   ```python
   from flask import Flask
   from api.routes.download import download_routes

   app = Flask(__name__)
   app.register_blueprint(download_routes, url_prefix="/api")
   ```

3. **Consumir el endpoint** desde cualquier cliente HTTP.  
   - **Headers recomendados**: `Content-Type: application/json` (o `multipart/form-data` si se envía archivo).  
   - **Manejo de errores**: inspeccionar código de estado y campo `codigo_error` en la respuesta JSON.

4. **Ejemplo completo (Node.js – fetch)**:
   ```javascript
   const payload = {
     code: "function sum(a,b){return a+b;}",
     extra: "añade tabla de ejemplos"
   };

   fetch('http://localhost:5000/api/download/markdown', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify(payload)
   })
   .then(res => {
     if (!res.ok) throw new Error(`HTTP ${res.status}`);
     return res.blob();
   })
   .then(blob => {
     const url = window.URL.createObjectURL(blob);
     const a = document.createElement('a');
     a.href = url;
     a.download = 'documentacion.md';
     a.click();
   })
   .catch(console.error);
   ```

---

### Códigos de error
| Código HTTP | `codigo_error` | Condición | Mensaje devuelto |
|-------------|----------------|-----------|------------------|
| 400 | `INVALID_FILE_TYPE` | `file_type` no es `pdf`, `markdown` o `docx`. | `"Tipo de archivo no válido. Use 'pdf' , 'markdown' o 'docx"` |
| 400 | `INVALID_CONTENT_TYPE` | El cuerpo de la petición no es JSON ni archivo. | `"El request debe ser JSON o contener un archivo"` |
| 400 | `MISSING_FIELD` | Falta el campo `codigo` en el JSON. | `"El campo 'codigo' es requerido"` |
| 400 | *validación personalizada* | `validate.validar_codigo` detecta longitud fuera de rango. | Contenido del diccionario devuelto por `validar_codigo`. |
| 500 | `INTERNAL_SERVER_ERROR` | Excepción inesperada durante generación o envío. | `"Error interno del servidor al generar documentación <file_type>"` |

---

## Servicios involucrados
| Servicio | Responsabilidad |
|----------|-----------------|
| `ZipService` | Operaciones de inspección y extracción de contenido ZIP (`listar_contenido_zip`). |
| `ChunkingService` | Divide el código en fragmentos manejables (máx. 8000 bytes, 10 archivos por chunk, estimación de 12 000 tokens). |
| `CacheService` (obtenido vía `get_global_cache`) | Almacena resultados intermedios; configurado con capacidad 100 y política LRU. |
| `DocumentationOrchestrator` | Orquesta el flujo completo: validación, chunking, caché y generación de documentación. |
| `EasyDocsPDF` / `EasyDocsDOCX` | Convertidores de markdown a PDF y DOCX respectivamente. |
| `bytes_utils.preparar_descarga` | Envuelve bytes en un objeto `io.BytesIO` listo para `send_file`. |

---

## Endpoints (métodos públicos)
| Método | Parámetros | Tipo de retorno | Descripción |
|--------|------------|----------------|-------------|
| `generar(codigo_fuente: str, tipo: str, extra: str = None, is_chunk: bool = False) -> str` | `codigo_fuente`: fragmento de código a documentar.<br>`tipo`: `'markdown'`, `'pdf'` o `'word'`.<br>`extra`: texto opcional con requisitos adicionales.<br>`is_chunk`: indica si el fragmento se procesa bajo modo *chunk*. | `str` con la documentación generada. | Orquesta la construcción de los prompts, la llamada a la API de Groq y la gestión de errores. |
| `apply_extra(docs: str, extra: str = None) -> str` |