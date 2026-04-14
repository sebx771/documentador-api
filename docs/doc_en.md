# Documentation for Project API

## API Overview
The Project API provides a set of endpoints for managing documentation generation, caching, and ZIP file processing. It supports generating documentation in multiple formats (Markdown, PDF, DOCX) from source code fragments.

## Endpoints

### 1. `POST /api/download/pdf`
- **HTTP Method:** `POST`
- **Path:** `/api/download/pdf`
- **Description:** Generates documentation in PDF format from source code.
- **Parameters:**
  - `codigo` (JSON): Source code.
  - `extra` (JSON): Additional requirements.
- **Example:**
```http
POST /api/download/pdf HTTP/1.1
Content-Type: application/json

{
  "codigo": "def hello():\n    print('Hello, world!')",
  "extra": "Include usage examples"
}
```

### 2. `POST /api/download/<file_type>`
- **HTTP Method:** `POST`
- **Path:** `/api/download/<file_type>` (replace `<file_type>` with `markdown`, `pdf`, or `docx`)
- **Description:** Generates documentation in the specified format from source code.
- **Parameters:**
  - `codigo` (JSON): Source code.
  - `extra` (JSON): Additional requirements.
- **Example:**
```http
POST /api/download/markdown HTTP/1.1
Content-Type: application/json

{
  "codigo": "def hello():\n    print('Hello, world!')",
  "extra": "Include usage examples"
}
```

### 3. `POST /preview-zip`
- **HTTP Method:** `POST`
- **Path:** `/preview-zip`
- **Description:** Previews the contents of a ZIP file.
- **Parameters:**
  - `file` (multipart/form-data): ZIP file.
- **Example:**
```http
POST /preview-zip HTTP/1.1
Content-Type: multipart/form-data; boundary=---XYZ

---XYZ
Content-Disposition: form-data; name="file"; filename="project.zip"
Content-Type: application/zip

<binary zip data>
---XYZ--
```

### 4. `POST /upload-zip`
- **HTTP Method:** `POST`
- **Path:** `/upload-zip`
- **Description:** Generates documentation from a ZIP file.
- **Parameters:**
  - `file` (multipart/form-data): ZIP file.
  - `doc_type` (multipart/form-data): Documentation type (Markdown, PDF, Word).
  - `extra_requirements` (multipart/form-data): Additional requirements.
- **Example:**
```http
POST /upload-zip HTTP/1.1
Content-Type: multipart/form-data; boundary=---ABC

---ABC
Content-Disposition: form-data; name="file"; filename="project.zip"
Content-Type: application/zip

<binary zip data>
---ABC
Content-Disposition: form-data; name="doc_type"

pdf
---ABC
Content-Disposition: form-data; name="extra_requirements"

Include architecture diagram and usage examples.
---ABC--
```

## Services Explanation

### 1. `DocumentationOrchestrator`
Coordinates the extraction of ZIP files, generation of chunks, caching, and orchestration of AI for consolidated documentation.

### 2. `ZipService`
Provides functionalities for listing and validating ZIP file contents, filtering unwanted folders and files.

### 3. `CacheService`
Manages distributed caching using Redis, supporting TTL and LRU policies.

### 4. `ChunkingService`
Divides collections of files into chunks with controlled size.

### 5. `DocumentadorIA`
Generates documentation using an AI model.

## Integration Guide

### 1. Initialize Cache
```python
from api.services.cache_service import get_global_cache

cache = get_global_cache(
    max_size=200,
    ttl_seconds=43200,
    enable_lru=True
)
```

### 2. Generate Documentation
```python
from api.services.ai_services import DocumentadorIA

doc_gen = DocumentadorIA(
    model="llama-3.3-70b-versatile",
    ex_model="meta-llama/llama-4-scout-17b-16e-instruct"
)

markdown_doc = doc_gen.generar(
    codigo_fuente="def suma(a, b):\n    return a + b",
    tipo="markdown",
    extra="Incluye un ejemplo de uso en JSON.",
    is_chunk=False
)
```

### 3. Process ZIP File
```python
from api.services.zip_services import ZipService

zip_service = ZipService()
codigo_valido, codigo_invalidos = zip_service.extraer_zip(zip_bytes)

print("Archivos procesados:", len(codigo_valido))
print("Archivos descartados:", len(codigo_invalidos))
```

## Error Codes

### 1. `INVALID_FILE_TYPE`
- **Description:** Invalid file type.
- **HTTP Status Code:** 400

### 2. `EMPTY_FILE`
- **Description:** Empty file.
- **HTTP Status Code:** 400

### 3. `INVALID_DOC_TYPE`
- **Description:** Invalid documentation type.
- **HTTP Status Code:** 400

### 4. `PROCESSING_ERROR`
- **Description:** Processing error.
- **HTTP Status Code:** 500

### 5. `VALIDATION_ERROR`
- **Description:** Validation error.
- **HTTP Status Code:** 400