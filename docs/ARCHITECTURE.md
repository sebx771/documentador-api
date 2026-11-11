# 🏗️ Arquitectura de EasyDocs

Español | [English](ARCHITECTURE.en.md)

## Visión General

EasyDocs utiliza una **arquitectura de servicios desacoplada** organizada por rutas, controladores, paquete modular de orquestación (`api/services/orchestrator/`), adaptadores de proveedores IA y exportadores.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Flask Application                        │
│              (api/main.py - REST API + CORS + 15MB cap)         │
└─────────────────┬───────────────────────────────┬───────────────┘
                  │                               │
          ┌───────▼─────────┐             ┌───────▼───────────┐
          │ Download Routes │             │    ZIP Routes     │
          │ (+ Rate Limit)  │             │  (+ Rate Limit)   │
          └───────┬─────────┘             └───────┬───────────┘
                  │                               │
          ┌───────▼──────────┐            ┌───────▼───────────┐
          │DownloadController│            │   ZipController   │
          └───────┬──────────┘            └───────┬───────────┘
                  │                               │
                  │               ┌───────────────▼───────────────┐
                  │               │   DocumentationOrchestrator   │
                  │               │ (api/services/orchestrator/)  │
                  │               └───────────────┬───────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        │              ┌──────────▼─────────┐               │
        │              │   ZipService       │               │
        │              │ (Extrae archivos)  │               │
        │              └──────────────────────┘               │
        │                                                     │
        │              ┌──────────────────────┐              │
        │              │ ChunkingService      │              │
        │              │ (Divide en chunks)   │              │
        │              └──────────────────────┘              │
        │                                                     │
        │              ┌──────────────────────┐              │
        │              │  CacheService        │              │
        │              │  (Redis)             │              │
        │              └──────────────────────┘              │
        │                                                     │
        │              ┌──────────────────────┐              │
        │              │ DocumentadorIA       │              │
        │              │(Groq/OpenRouter/Gem.)│              │
        │              └──────────────────────┘              │
        │                                                     │
        │              ┌──────────────────────┐              │
        │              │ Ratelimiter          │              │
        │              │ (Redis - TPM/RPM)    │              │
        └──────────────└──────────────────────┘              │
                                                              │
            ┌───────────────────┬───────────────────┬──────────┐
            │                   │                   │          │
        ┌───▼───────┐      ┌───▼───────┐      ┌───▼────┐    ┌──▼───────┐
        │markdown-  │      │ python-   │      │Markdown │    │ ZipService│
        │pdf (PDF)  │      │  docx     │      │Exporter │    │ .crear_zip│
        │           │      │(Word)     │      │         │    │(Multifile)│
        └───────────┘      └───────────┘      └─────────┘    └──────────┘
            │                   │                   │             │
            └───────────────────┼───────────────────┼─────────────┘
                                │                   │
                          ┌─────▼───────────────────▼─────┐
                          │         Response              │
                          │ (Archivo/.zip o JSON en GET /,│
                          │  GET /api/download, preview y │
                          │            errores)           │
                          └───────────────────────────────┘
```

---

## 📦 Componentes Principales

### 1. **Flask Application** (`api/main.py` + `api/logging_config.py`)
- Servidor REST (`API_VERSION = "3.4.0"`) que gestiona `GET /` y registra los blueprints bajo `/api`
- Configuración CORS para orígenes permitidos (`ALLOWED_ORIGINS`)
- Límite global de petición HTTP (`MAX_CONTENT_LENGTH = 15 MB` -> HTTP `413`)
- Logging centralizado (`api/logging_config.py`) y manejo global de errores HTTP (`404`, `413`, `405`, `500`)

### 2. **Routes y Controllers** (`api/routes/` + `api/controllers/`)

#### `download.py` -> `DownloadController`
- `GET /api/download`: devuelve esquema de uso, formatos y límites en JSON
- `POST /api/download/<file_type>`: acepta JSON (o archivo) con código fuente y `language`/`extra`
- Soporta `file_type`: `markdown`, `pdf`, `docx`
- Protegido por `ai_endpoint_limiter` (`10 req/min` por IP)

#### `zip.py` -> `ZipController`
- `POST /api/preview-zip`: valida e inspecciona archivos elegibles/ignorados sin llamar a IA (`light_endpoint_limiter`: `30 req/min` por IP)
- `POST /api/upload-zip`: procesa un `.zip` completo y delega en `DocumentationOrchestrator` (`ai_endpoint_limiter`: `10 req/min` por IP)
- Soporta `doc_type`: `markdown`, `pdf`, `word`, **`multifile`**
- Devuelve documento consolidado (`.md`/`.pdf`/`.docx`) o `.zip` con N archivos `.md` (`multifile`)

### 3. **DocumentationOrchestrator** (`api/services/orchestrator/` + fachada `api/services/documentation_orchestrator.py`)

El orquestador está modularizado en `api/services/orchestrator/` con modelos de dominio tipados (`SourceFile`, `ChunkDocumentation`, `GenerationMetadata`, `SingleDocResult`, `MultifileResult`):
- `models.py` — Estructuras tipadas del pipeline
- `extraction.py` — Extracción segura y selección de archivos elegibles (`ZipService`)
- `generation.py` — Generación por chunks con caché SHA-256 (`CacheService` + `DocumentadorIA`)
- `consolidation.py` — Síntesis jerárquica multirronda por presupuesto de tokens (`final_doc`) y aplicación tardía de `extra_requirements`
- `results.py` — Construcción de respuestas y nombres de archivo multifile por ruta relativa sanitizada
- `pipeline.py` — Coordinador `DocumentationOrchestrator.process_zip()` (con fachada de retrocompatibilidad en `api/services/documentation_orchestrator.py`)

```
ZIP Input
   ↓
Extract Files (extraction.py -> ZipService)
   ↓
Create Chunks (ChunkingService)
   ↓
Detect Language (DocumentadorIA)
   ↓
Process Chunks (generation.py -> CacheService + DocumentadorIA)
   ↓
┌─ ¿multifile=True? ─────────────────────┐
│                                       │
SÍ                                      NO
↓                                       ↓
results.py (rutas sanitizadas)  consolidation.py (multirronda final_doc)
↓                                       ↓
Return MultifileResult          Apply Extra Requirements (apply_extra)
                                        ↓
                                Return SingleDocResult
```

### 4. **ChunkingService** (`api/services/chunking_service.py`)

Divide código grande en chunks procesables:

```
Entrada: Lista de archivos
   ↓
Agrupa por tamaño máximo (50KB por defecto)
   ↓
Máximo 5 archivos por chunk
   ↓
Salida: Lista de chunks
```

**Por qué es necesario:**
- Evita exceder límites de tokens de Groq
- Procesa mejor proyectos grandes
- Permite paralelización futura

### 5. **CacheService** (`api/services/cache_service.py`)

Almacena resultados en **Redis**:

```
Input Code + language + PROMPT_VERSION → SHA256 Hash → Redis Key
                ↓
         ¿Resultado en cache?
         ↙              ↖
        SÍ               NO
        │                │
     Return            Generate
     Cached             & Store
```

**Ventajas:**
- Evita reprocesar código idéntico
- Acelera respuestas (100ms vs 4s)
- Distribuido para entornos serverless

### 6. **Ratelimiter** (`api/services/rate_limiter.py`)

Control de límites con **Token Bucket + Redis**:

```
Token Bucket
┌──────────────┐
│ TOKEN POOL   │ (Recarga cada minuto)
└──────────────┘
     ↑
 Requests come in
     ↓
¿Hay tokens? → SÍ → Process → Deduct tokens
     ↓
    NO
     ↓
Wait or Reject
```

**Soporta:**
- TPM (Tokens Per Minute) - Groq API limit
- RPM (Requests Per Minute) - Rate limit general
- Burst factor - Permite picos controlados

### 7. **DocumentadorIA** (`api/services/ai/ai_service.py`)

Motor de generación con **múltiples proveedores de IA** a través de `BaseAIProvider`:

```
1. Detect Language
   └─→ Analiza el código (heurística ES/EN)
   
2. Build Prompts
   ├─→ System Prompt (instrucciones + rol)
   └─→ User Prompt (código + requisitos extra)
   
3. Estimate Tokens
   └─→ 1 char ≈ 0.25 tokens (heurística)
   
4. Check Rate Limit (Redis Token Bucket)
   └─→ Verifica TPM disponible por modelo
   
5. Retry Queue
   ├─→ Modelo principal (final_doc o chunking)
   ├─→ Fallback
   └─→ Emergency
       └─→ Cada modelo: 3 reintentos con backoff
   
6. Call Provider
   └─→ GroqProvider / OpenRouterProvider / GeminiProvider (.create_chat_completion())
   
7. Clean Response
   ├─→ Elimina etiquetas <think>
   └─→ Elimina instrucciones de chunk repetidas
   
8. Return Markdown
```

**Soporta:**
- Proveedores (`api/services/ai/provider/`): **Groq**, **OpenRouter** y **Google Gemini** (inicialización condicional según claves presentes en `api/config.py`)
- Modelos (`api/services/ai/models.py`): ruteo por rol (`chunking`, `final_doc`, `fallback`, `emergency`)
- Idiomas: Español, Inglés
- Formatos de salida: Markdown, PDF, Word, Multifile .zip

### 8. **Exporters** (`api/export/` + `ZipService`)

Convierten Markdown a formatos finales:

| Exporter | Tecnología | Ventajas |
|----------|-----------|----------|
| PDF | `markdown-pdf` (`api/export/pdf_gen.py`) | Renderizado directo desde Markdown |
| DOCX | `python-docx` (`api/export/docx_gen.py`) | Editable, formato estructurado |
| Markdown | Nativo | Versionable, legible |
| Multifile ZIP | `zipfile` | N documentos .md empaquetados |

---

## 🔄 Flujos de Datos

### Flujo 1: Documento desde JSON (Rápido)

```json
POST /api/download/markdown
{
  "code": "def hello(): print('hello')",
  "extra": "Add examples",
  "language": "es"
}
↓
DocumentadorIA.generar()
↓
Descarga el archivo: documentacion_2024-....md
(MIME: text/markdown)
```
⏱️ **Tiempo esperado:** 1-3 segundos

> Los formatos `pdf` y `docx` del mismo endpoint descargan `application/pdf` y `.docx` respectivamente. No se devuelve JSON en éxito.

### Flujo 2: Proyecto desde ZIP — Consolidado (markdown, pdf, word)

```
POST /api/upload-zip
├─ file: proyecto.zip
├─ doc_type: markdown   # o pdf, word
└─ language: es
   ↓
   ZipService.extraer_zip()
   ├─ 20 archivos extraídos
   └─ 2 inválidos
      ↓
      ChunkingService.create_chunks()
      ├─ Chunk 1: 5 archivos
      └─ Chunk 2: 5 archivos
         ↓
         Para cada chunk:
         ├─ Generar hash → buscar cache
         ├─ Miss → DocumentadorIA.generar()
         └─ Guardar en cache
            ↓
            Consolidate Documentation
            ├─ Merge secciones
            └─ Apply Extra Requirements
               ↓
               Descarga el archivo resultante según doc_type:
               ├─ markdown → .md (text/markdown)
               ├─ pdf      → .pdf (application/pdf)
               └─ word     → .docx (application/vnd.openxmlformats-...)
```
⏱️ **Tiempo esperado:** 10-30 segundos

> La metadata (total_files, total_chunks, cache_stats, etc.) solo se usa internamente para logging; no se devuelve al cliente con el archivo.

### Flujo 3: Proyecto desde ZIP — Multifile

```
POST /api/upload-zip
├─ file: proyecto.zip
├─ doc_type: multifile
└─ language: es
   ↓
   (misma extracción y chunking que Flujo 2)
         ↓
         Para cada chunk:
         ├─ DocumentadorIA.generar()
         └─ (sin consolidación)
            ↓
            Generar nombres de archivo:
            ├─ Chunk 1 → main.py → "main.md"
            ├─ Chunk 2 → api.py + db.py → "api+db.md"
            └─ ...
               ↓
               ZipService.crear_zip()
               └─ .zip en memoria con N .md
                  ↓
                  send_file(..., mimetype="application/zip")
```
⏱️ **Tiempo esperado:** 10-30 segundos (similar, sin paso extra de consolidación)

---

## 🛡️ Manejo de Errores

### Validaciones

```
ZIP Input
├─ Rate limit por IP excedido → 429 Too Many Requests (Retry-After, X-RateLimit-*)
├─ Petición > 15 MB → 413 Payload Too Large
├─ ¿No es ZIP / ZIP Bomb / Path Traversal / > 300 archivos / > 40 MB descomprimidos? → 400 Bad Request
├─ ¿Sin archivos válidos? → 400 No Valid Files
└─ ✓ Válido → Procesar
     ├─ Saturación de proveedor IA → 429 Too Many Requests
     ├─ Error IA sin fallback disponible → 500 Internal Server Error
     └─ Error Redis → Opera sin caché / rate limiter fail-open
```

### Fallbacks

1. **Si falla IA primaria** → Intenta `fallback` y `emergency` (hasta 3 reintentos con backoff por modelo)
2. **Si falla Redis** → Opera sin caché (más lento) y en modo *fail-open* para rate limit
3. **Si todos los proveedores fallan por cuota** → Retorna HTTP `429` o `500` en JSON con `codigo_error`

---

## 📊 Decisiones de Diseño

| Decisión | Razón | Alternativas Rechazadas |
|----------|-------|------------------------|
| Redis para cache | Distribuido + serverless-ready | En-memory dict (no persiste) |
| Redis para rate limit | Compartido entre instancias | Token bucket en memoria |
| Multi-proveedor (Groq + OpenRouter + Gemini) | Ruteo por rol (`chunking`, `final_doc`, `fallback`, `emergency`) y tolerancia a cuotas | Proveedor único |
| Chunking automático + consolidación multirronda | Proyectos grandes sin exceder ventanas de contexto | Procesar todo en una sola llamada |
| Multiidioma | Clientes globales (ES/EN) | Solo español |
| Docker PaaS + soporte Vercel | Docker PaaS soporta hasta 15 MB y consolidaciones largas; Vercel queda para cargas livianas | Solo serverless (límite ~4.5 MB y timeouts) |

---

## 🚀 Escalabilidad

### Limitaciones Actuales

| Factor | Límite | Notas |
|--------|--------|-------|
| Petición HTTP (`MAX_CONTENT_LENGTH`) | 15 MB | Configurado en `api/main.py` (HTTP 413 si se excede); Vercel impone ~4.5 MB en su edge |
| Tamaño ZIP descomprimido | 40 MB | Validación anti ZIP Bomb en `ZipService.validar_zip_seguro` |
| Archivos totales en ZIP | 300 | Límite de seguridad en `ZipService.MAX_FILES_COUNT` |
| Archivos elegibles por defecto | 50 | `ZipService.DEFAULT_MAX_ELIGIBLE_FILES` |
| Rate limiting por IP | 10 req/min (IA), 30 req/min (preview) | `EndpointRateLimiter` con cabeceras `Retry-After` y `X-RateLimit-*` |

### Mejoras Futuras

- [ ] Procesamiento paralelo de chunks
- [ ] Caché distribuido (Redis Cluster)
- [ ] WebSocket para progreso en tiempo real
- [ ] Webhook para notificaciones
- [ ] Almacenamiento S3 para historiales
- [ ] Base de datos para estadísticas

---

## 🔐 Seguridad

### Gestión de Secretos
- Variables de entorno (`GROQ_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `REDIS_URL`) definidas en `.env` (referencia en `.env.example`)
- Excluidas de git mediante `.gitignore`
- Configuradas en el panel del hosting (Docker PaaS / Vercel)

### Validaciones de Input
- Validación de archivo `.zip` válido y tamaño máximo HTTP (`15 MB`)
- Protección contra *ZIP Bombs* (`40 MB` descomprimidos, máximo `300` archivos)
- Protección contra *Path Traversal* (bloqueo de rutas absolutas o con `..`)
- Sanitización de rutas relativas en exportación `multifile`

### Rate Limiting
- TPM limitado por modelo hacia los proveedores
- Rate limiting por IP (`10 req/min` en `/api/download/<file_type>` y `/api/upload-zip`; `30 req/min` en `/api/preview-zip`)
- Prevención de abuso en despliegues públicos

---

## 📈 Monitoreo

### Logs Disponibles

```python
# Nivel INFO
logger.info(f"ZIP recibido: {filename}, {size} bytes")
logger.info(f"Chunks creados: {len(chunks)}")
logger.info(f"Cache hit rate: {hit_rate}%")

# Nivel ERROR
logger.error(f"Error en IA: {str(e)}")
```

### Métricas Retornadas

La API no expone métricas en las respuestas de éxito. La metadata (total_files, total_chunks, cache_stats, elapsed_time_seconds, input_size_bytes, etc.) se calcula en `ZipController`/`DownloadController` pero solo se registra en logs.

#### Respuesta JSON de estructura del ZIP (`POST /api/preview-zip`)
```json
[
  {
    "file": "src/main.py",
    "language": "py",
    "valid": true,
    "size": "4.52kb"
  },
  {
    "file": "assets/logo.png",
    "language": "png",
    "valid": false,
    "size": "120.1kb"
  }
]
```

#### Respuestas de error (JSON)
```json
{
  "error": "Solo se permiten archivos .zip",
  "codigo_error": "INVALID_FILE_TYPE"
}
```

---

## 📚 Referencias

- [Groq API Docs](https://console.groq.com/docs)
- [Redis Documentation](https://redis.io/documentation)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Python FPDF](https://py-pdf.github.io/fpdf2/)
- [Python-docx](https://python-docx.readthedocs.io/)
