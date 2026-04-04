# EasyDocs API - Documentación Técnica Completa

## 1. Descripción General

### 1.1 Definición y Alcance
EasyDocs API es una aplicación web diseñada para generar documentación técnica automática a partir de código fuente. La API ofrece endpoints para subir archivos ZIP y descargar documentación en diferentes formatos (Markdown, PDF, Word).

### 1.2 Arquitectura General
La arquitectura de EasyDocs API se compone de:
- **Archivo principal**: `main.py` - Punto de entrada de la aplicación
- **Servicios**: Carpeta `services/` - Lógica de negocio
- **Rutas**: Carpeta `routes/` - Endpoints de la API
- **Utilidades**: Carpeta `utils/` - Funciones helper

---

## 2. Estructura de Archivos

```
proyecto/
├── main.py                      # Punto de entrada
├── api/
│   ├── main.py                 # Aplicación Flask
│   ├── routes/
│   │   ├── download.py       # Endpoints /download
│   │   └── zip.py            # Endpoints /upload-zip, /preview-zip
│   ├── services/
│   │   ├── ai_services.py    # DocumentadorIA (Groq)
│   │   ├── cache_service.py  # Cache con Redis
│   │   ├── chunking_service.py # División en chunks
│   │   ├── documentation_orchestrator.py # Orquestador
│   │   └── zip_services.py  # Extracción de ZIP
│   ├── utils/
│   │   ├── bytes_utils.py
│   │   ├── get_request.py
│   │   └── validate.py
│   └── export/
│       └── pdf_gen.py       # Generador de PDF
└── requirements.txt
```

---

## 3. Servicios

### 3.1 DocumentadorIA (`ai_services.py`)
**Propósito**: Generar documentación técnica usando IA (Groq - Llama 3.3)

**Componentes**:
- `client`: Conexión a API de Groq
- `model`: Modelo de lenguaje (`llama-3.3-70b-versatile`)
- `PROMPT_CONFIGS`: Configuraciones por tipo de documento

**Métodos**:
- `generar(codigo_fuente, tipo, extra)`: Genera documentación

### 3.2 CacheService (`cache_service.py`)
**Propósito**: Cache con Redis para evitar llamadas redundantes a la IA

**Características**:
- TTL: 24 horas (86400 segundos)
- Hash: SHA256(content|doc_type|extra)
- Almacenamiento: Redis

**Métodos**:
- `generate_hash(content, doc_type, extra_requirements)`: Genera clave única
- `get(cache_key)`: Recupera del cache
- `set(cache_key, result)`: Guarda en cache
- `get_stats()`: Devuelve estadísticas (hits, misses, hit_rate)

### 3.3 ChunkingService (`chunking_service.py`)
**Propósito**: Dividir archivos grandes en chunks manejables

**Características**:
- Máximo 10 archivos por chunk
- Máximo 8000 caracteres por chunk
- Estimación: ~4 caracteres por token

**Métodos**:
- `create_chunks(files, doc_type, extra_requirements)`: Crea chunks

### 3.4 DocumentationOrchestrator (`documentation_orchestrator.py`)
**Propósito**: Orquestar todo el proceso de documentación

**Flujo**:
1. Extraer archivos del ZIP (`ZipService`)
2. Dividir en chunks (`ChunkingService`)
3. Verificar cache (`CacheService`)
4. Generar documentación (`DocumentadorIA`)
5. Guardar en cache
6. Consolidar resultados

### 3.5 ZipService (`zip_services.py`)
**Propósito**: Extraer código de archivos ZIP

**Extensiones permitidas**:
`.py`, `.java`, `.go`, `.js`, `.ts`, `.php`, `.css`, `.html`, `.json`, `.xml`, `.yml`, `.yaml`

**Carpetas ignoradas**:
`node_modules`, `.git`, `__pycache__`, `.venv`

---

## 4. Endpoints

### 4.1 `/upload-zip` (POST)
**Descripción**: Procesa archivo ZIP y genera documentación

**Parámetros**:
- `file`: Archivo ZIP (máx 10MB)
- `doc_type`: Tipo de salida (markdown, pdf, word)
- `extra_requirements`: Requisitos adicionales

**Respuesta**:
```json
{
  "success": true,
  "documentation": "...",
  "metadata": {
    "total_files": 10,
    "invalid_files_count": 0,
    "total_chunks": 6,
    "cache": {
      "hits": 2,
      "misses": 4,
      "hit_rate_percent": 33.33
    },
    "elapsed_time_seconds": 2.5
  },
  "errors": {
    "files": [],
    "count": 0
  }
}
```

### 4.2 `/preview-zip` (POST)
**Descripción**: Vista previa del contenido de un ZIP

**Parámetros**:
- `file`: Archivo ZIP

### 4.3 `/download/<file_type>` (POST)
**Descripción**: Genera documentación para código proporcionado

**Parámetros**:
- `codigo`: Código fuente (JSON)
- `extra`: Requisitos adicionales

**Tipos válidos**: `pdf`, `markdown`

### 4.4 `/download` (GET)
**Descripción**: Información sobre endpoints disponíveis

---

## 5. Lógica de Negocio

### 5.1 Validaciones
- Archivo ZIP debe ser válido y no mayor a 10MB
- Máximo 50 archivos por ZIP
- Código fuente entre 10 y 50000 caracteres
- Tipo de documento debe ser válido

### 5.2 Caché
- Keys basadas en SHA256 del contenido + tipo + extra
- TTL de 24 horas
- Estadísticas: hits, misses, hit_rate_percent

### 5.3 Chunking
- División por cantidad de archivos (máx 10)
- División por tamaño (máx 8000 chars)
- Procesamiento independiente por chunk

---

## 6. Guía de Integración

### 6.1 Subir archivo ZIP
```bash
curl -X POST "https://documentador-api.vercel.app/api/upload-zip" \
  -F "file=@proyecto.zip" \
  -F "doc_type=markdown" \
  -F "extra_requirements=Incluye ejemplos"
```

### 6.2 Generar documentación
```bash
curl -X POST "https://documentador-api.vercel.app/api/download/markdown" \
  -H "Content-Type: application/json" \
  -d '{"codigo": "function suma(a, b) { return a + b; }"}'
```

### 6.3 Usar en Python
```python
from api.services.ai_services import DocumentadorIA

doc = DocumentadorIA()
resultado = doc.generar("código fuente", "markdown", "extra")
print(resultado)
```

---

## 7. Variables de Entorno

| Variable | Descripción |
| --- | --- |
| `GROQ_API_KEY` | Clave de API de Groq |
| `REDIS_URL` | URL de Redis (ej: redis://localhost:6379) |
| `API_VERSION` | Versión de la API |
| `MAX_CODE_LENGTH` | Longitud máxima del código (50000) |
| `MIN_CODE_LENGTH` | Longitud mínima del código (10) |
| `MAX_ZIP_SIZE` | Tamaño máximo del ZIP (10MB) |

---

## 8. Códigos de Error

| Código | Descripción |
| --- | --- |
| `NO_FILE` | No se proporcionó archivo |
| `INVALID_FILE_TYPE` | Archivo no es ZIP válido |
| `FILE_TOO_LARGE` | Archivo mayor a 10MB |
| `EMPTY_FILE` | Archivo está vacío |
| `INVALID_DOC_TYPE` | Tipo de documento inválido |
| `INVALID_CONTENT_TYPE` | Request JSON inválido |
| `MISSING_FIELD` | Falta campo obligatorio |
| `VALIDATION_ERROR` | Error de validación |
| `PROCESSING_ERROR` | Error al procesar |
| `INTERNAL_SERVER_ERROR` | Error interno del servidor |

---

## 9. Rendimiento

### 9.1 Con Cache
- Primera request: ~5-7 segundos (llamada a Groq)
- Requests siguientes: <1 segundo (cache hit)

### 9.2 Sin Cache
- Cada request: ~5-7 segundos

### 9.3 Chunking
- Archivos grandes se dividen en chunks
- Procesamiento paralelo cuando es posible
- Consolidación al final

---

## 10. Tecnologías

- **Python 3.12+**: Lenguaje base
- **Flask**: Framework web
- **Groq (Llama 3.3)**: IA para documentación
- **Redis**: Cache serverless
- **FPDF**: Generación de PDF
- **Vercel**: Despliegue serverless