# 🏗️ Arquitectura de EasyDocs

## Visión General

EasyDocs utiliza una **arquitectura de servicios desacoplada** optimizada para procesamiento paralelo de documentación en entornos serverless. Cada componente es responsable de una función específica y se comunica a través de interfaces bien definidas.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Flask Application                        │
│                     (main.py - REST API)                        │
└─────────────────┬───────────────────────────────┬───────────────┘
                  │                               │
          ┌───────▼─────────┐         ┌──────────▼──────────┐
          │  Download Routes │         │   ZIP Routes        │
          │  (JSON input)    │         │  (File upload)      │
          └────────┬────────┘         └──────────┬──────────┘
                   │                             │
                   └──────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ Documentation Orchestrator │
                    │  (Coordinador Principal)   │
                    └─────────────┬──────────────┘
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
        │              │ (Groq/Llama 3.1)     │              │
        │              └──────────────────────┘              │
        │                                                     │
        │              ┌──────────────────────┐              │
        │              │ Ratelimiter          │              │
        │              │ (Redis - TPM/RPM)    │              │
        └──────────────└──────────────────────┘              │
                                                              │
            ┌───────────────────┬───────────────────┬──────────┐
            │                   │                   │          │
        ┌───▼───┐          ┌───▼───────┐      ┌───▼────┐    ┌──▼───────┐
        │ FPDF  │          │ python-   │      │Markdown │    │ ZipService│
        │Export │          │  docx     │      │Exporter │    │ .crear_zip│
        │(PDF)  │          │(Word)     │      │         │    │(Multifile)│
        └───────┘          └───────────┘      └─────────┘    └──────────┘
            │                   │                   │             │
            └───────────────────┼───────────────────┼─────────────┘
                                │                   │
                          ┌─────▼───────────────────▼─────┐
                          │         Response              │
                          │   (JSON file o .zip bytes)    │
                          └───────────────────────────────┘
```

---

## 📦 Componentes Principales

### 1. **Flask Application** (`api/main.py`)
- Servidor REST que gestiona todas las peticiones
- Configuración CORS para acceso desde frontend
- Rutas organizadas por blueprints
- Manejo global de errores HTTP

### 2. **Routes** (`api/routes/`)

#### `download.py`
- Endpoint: `POST /api/download/<type>`
- Acepta JSON con código fuente
- Genera documentación directamente sin ZIP
- Soporta: markdown, pdf, word

#### `zip.py`
- Endpoint: `POST /api/upload-zip`
- Procesa archivos ZIP completos
- Orquesta el flujo completo de generación
- Soporta `doc_type`: markdown, pdf, word, **multifile**
- Devuelve documentación consolidada (+ metadata) o .zip con N .md

### 3. **DocumentationOrchestrator** (`api/services/documentation_orchestrator.py`)

Es el **corazón de la aplicación**. Coordina el flujo:

```
ZIP Input
   ↓
Extract Files (ZipService)
   ↓
Create Chunks (ChunkingService)
   ↓
Detect Language (DocumentadorIA)
   ↓
Process Chunks (DocumentadorIA + Cache)
   ↓
┌─ ¿multifile=True? ─────────────────────┐
│                                       │
SÍ                                      NO
↓                                       ↓
Skip Consolidation              Consolidate Documentation
↓                                       ↓
Collect per-chunk docs          Apply Extra Requirements
↓                                       ↓
Return {"files": {...}}         Return {"documentation": "..."}
```

**Métodos Clave:**
- `process_zip()` - Punto de entrada principal (acepta `multifile=False`)
- `_extract_files()` - Extrae contenido del ZIP
- `_process_chunks()` - Genera documentación por chunk
- `_consolidate_documentation()` - Merge inteligente de resultados (solo modo no-multifile)
- `_generate_chunk_filename()` - Asigna nombre significativo a cada .md de chunk

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
Input Code → SHA256 Hash → Redis Key
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
   └─→ GroqProvider.create_chat_completion()
   
7. Clean Response
   ├─→ Elimina etiquetas <think>
   └─→ Elimina instrucciones de chunk repetidas
   
8. Return Markdown
```

**Soporta:**
- Proveedores: Groq (actual), OpenRouter (futuro)
- Modelos: ruteo por rol (chunking, final_doc, fallback, emergency)
- Idiomas: Español, Inglés
- Formatos de salida: Markdown, PDF, Word, Multifile .zip

### 8. **Exporters** (`api/export/` + `ZipService`)

Convierten Markdown a formatos finales:

| Exporter | Tecnología | Ventajas |
|----------|-----------|----------|
| FPDF | `fpdf` | Ligero, portátil, rápido |
| DOCX | `python-docx` | Editable, profesional |
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
{
  "documentation": "# Documentation...",
  "metadata": {...}
}
```
⏱️ **Tiempo esperado:** 1-3 segundos

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
               {
                 "documentation": "# Docs...",
                 "metadata": { "total_files": 20, ... }
               }
```
⏱️ **Tiempo esperado:** 10-30 segundos

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
├─ ¿No es ZIP? → 400 Bad Request
├─ ¿Muy grande (>10MB)? → 413 Payload Too Large
├─ ¿Sin archivos válidos? → 400 No Valid Files
└─ ✓ Válido → Procesar
     ├─ Error IA → 500 con fallback
     ├─ Error Redis → 500 sin cache
     └─ Error ZipService → 400 Invalid Format
```

### Fallbacks

1. **Si falla IA primaria** → Intenta modelo secundario
2. **Si falla Redis** → Opera sin cache (más lento)
3. **Si falla Groq** → Retorna error con instrucciones

---

## 📊 Decisiones de Diseño

| Decisión | Razón | Alternativas Rechazadas |
|----------|-------|------------------------|
| Redis para cache | Distribuido + serverless-ready | En-memory dict (no persiste) |
| Redis para rate limit | Compartido entre instancias | Token bucket en memoria |
| Groq + Llama | Velocidad + costo | OpenAI (más lento/caro) |
| Chunking automático | Proyectos grandes | Procesar todo de una (límite tokens) |
| Multiidioma | Clientes globales | Solo español (limitado) |
| Vercel Serverless | Escalabilidad + costo | VPS tradicional |

---

## 🚀 Escalabilidad

### Limitaciones Actuales

| Factor | Límite | Solución |
|--------|--------|----------|
| Tamaño ZIP | 10 MB | Aumentar si Groq lo permite |
| Archivos por ZIP | 50 | Configurar según memoria |
| Chunk size | 50 KB | Ajustar según tokens |
| TPM Groq | 6000 | Upgrade plan Groq |

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
- Variables de entorno (`GROQ_API_KEY`, `REDIS_URL`)
- NO incluidas en git
- Configuradas en Vercel dashboard

### Validaciones de Input
- Validación de tipo MIME (solo ZIP)
- Validación de tamaño máximo
- Sanitización de nombres de archivo
- Detección de malware (futuro)

### Rate Limiting
- TPM limitado por modelo
- RPM limitado por IP (futuro)
- Previene abuso API

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

#### Modo consolidado (markdown/pdf/word)
```json
{
  "documentation": "# Documentación...",
  "metadata": {
    "total_files": 20,
    "total_chunks": 4,
    "cache_stats": {
      "hits": 1,
      "misses": 3,
      "hit_rate_percent": 25
    },
    "elapsed_time_seconds": 15.3,
    "input_size_bytes": 524288
  }
}
```

#### Modo multifile
```json
{
  "files": {
    "main.md": "# Documentación de main...",
    "api+db.md": "# Documentación de api y db..."
  },
  "metadata": {
    "total_files": 20,
    "total_chunks": 4,
    "total_docs": 4,
    "cache_stats": { ... },
    "elapsed_time_seconds": 15.3,
    "input_size_bytes": 524288
  }
}
```

---

## 📚 Referencias

- [Groq API Docs](https://console.groq.com/docs)
- [Redis Documentation](https://redis.io/documentation)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Python FPDF](https://py-pdf.github.io/fpdf2/)
- [Python-docx](https://python-docx.readthedocs.io/)
