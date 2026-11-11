# 🏗️ EasyDocs Architecture

[Español](ARCHITECTURE.md) | English

## Overview

EasyDocs uses a **decoupled service architecture** organized by routes, controllers, a modular orchestration package (`api/services/orchestrator/`), AI provider adapters, and exporters.

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
        │              │ (Extracts files)   │               │
        │              └──────────────────────┘               │
        │                                                     │
        │              ┌──────────────────────┐              │
        │              │ ChunkingService      │              │
        │              │ (Splits into chunks) │              │
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
                          │ (File/.zip or JSON on GET /,  │
                          │  GET /api/download, preview,  │
                          │          and errors)          │
                          └───────────────────────────────┘
```

---

## 📦 Main Components

### 1. **Flask Application** (`api/main.py` + `api/logging_config.py`)
- REST server (`API_VERSION = "3.4.0"`) handling `GET /` and registering blueprints under `/api`
- CORS configuration for allowed origins (`ALLOWED_ORIGINS`)
- Global HTTP request size limit (`MAX_CONTENT_LENGTH = 15 MB` -> HTTP `413`)
- Centralized logging (`api/logging_config.py`) and global HTTP error handling (`404`, `413`, `405`, `500`)

### 2. **Routes and Controllers** (`api/routes/` + `api/controllers/`)

#### `download.py` -> `DownloadController`
- `GET /api/download`: returns usage schema, formats, and limits as JSON
- `POST /api/download/<file_type>`: accepts JSON (or file) with source code and `language`/`extra`
- Supports `file_type`: `markdown`, `pdf`, `docx`
- Protected by `ai_endpoint_limiter` (`10 req/min` per IP)

#### `zip.py` -> `ZipController`
- `POST /api/preview-zip`: validates and inspects eligible/ignored files without calling AI (`light_endpoint_limiter`: `30 req/min` per IP)
- `POST /api/upload-zip`: processes a full `.zip` and delegates to `DocumentationOrchestrator` (`ai_endpoint_limiter`: `10 req/min` per IP)
- Supports `doc_type`: `markdown`, `pdf`, `word`, **`multifile`**
- Returns a consolidated document (`.md`/`.pdf`/`.docx`) or `.zip` with N `.md` files (`multifile`)

### 3. **DocumentationOrchestrator** (`api/services/orchestrator/` + facade `api/services/documentation_orchestrator.py`)

The orchestrator is modularized under `api/services/orchestrator/` with typed domain models (`SourceFile`, `ChunkDocumentation`, `GenerationMetadata`, `SingleDocResult`, `MultifileResult`):
- `models.py` — Typed pipeline data structures
- `extraction.py` — Safe extraction and eligible file selection (`ZipService`)
- `generation.py` — Per-chunk generation with SHA-256 caching (`CacheService` + `DocumentadorIA`)
- `consolidation.py` — Token-budgeted multi-round hierarchical synthesis (`final_doc`) and late application of `extra_requirements`
- `results.py` — Result construction and multifile filenames using sanitized relative paths
- `pipeline.py` — `DocumentationOrchestrator.process_zip()` coordinator (with backwards-compatibility facade in `api/services/documentation_orchestrator.py`)

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
┌─ multifile=True? ──────────────────────┐
│                                        │
YES                                      NO
↓                                        ↓
results.py (sanitized paths)    consolidation.py (multi-round final_doc)
↓                                        ↓
Return MultifileResult          Apply Extra Requirements (apply_extra)
                                         ↓
                                Return SingleDocResult
```

### 4. **ChunkingService** (`api/services/chunking_service.py`)

Splits large codebases into processable chunks:

```
Input: List of files
   ↓
Groups by maximum size (50KB by default)
   ↓
Maximum 5 files per chunk
   ↓
Output: List of chunks
```

**Why it is needed:**
- Avoids exceeding Groq token limits
- Handles large projects reliably
- Enables future parallelization

### 5. **CacheService** (`api/services/cache_service.py`)

Stores results in **Redis**:

```
Input Code + language + PROMPT_VERSION → SHA256 Hash → Redis Key
                ↓
         Result in cache?
         ↙              ↖
       YES               NO
        │                │
     Return            Generate
     Cached             & Store
```

**Benefits:**
- Avoids reprocessing identical code
- Speeds up responses (100ms vs 4s)
- Distributed for serverless environments

### 6. **Ratelimiter** (`api/services/rate_limiter.py`)

Rate limit control with **Token Bucket + Redis**:

```
Token Bucket
┌──────────────┐
│ TOKEN POOL   │ (Refills every minute)
└──────────────┘
     ↑
 Requests come in
     ↓
Tokens available? → YES → Process → Deduct tokens
     ↓
    NO
     ↓
Wait or Reject
```

**Supports:**
- TPM (Tokens Per Minute) — Groq API limit
- RPM (Requests Per Minute) — General rate limit
- Burst factor — Allows controlled spikes

### 7. **DocumentadorIA** (`api/services/ai/ai_service.py`)

Generation engine supporting **multiple AI providers** through `BaseAIProvider`:

```
1. Detect Language
   └─→ Analyzes code (ES/EN heuristic)
   
2. Build Prompts
   ├─→ System Prompt (instructions + role)
   └─→ User Prompt (code + extra requirements)
   
3. Estimate Tokens
   └─→ 1 char ≈ 0.25 tokens (heuristic)
   
4. Check Rate Limit (Redis Token Bucket)
   └─→ Checks available TPM per model
   
5. Retry Queue
   ├─→ Primary model (final_doc or chunking)
   ├─→ Fallback
   └─→ Emergency
       └─→ Each model: 3 retries with backoff
   
6. Call Provider
   └─→ GroqProvider / OpenRouterProvider / GeminiProvider (.create_chat_completion())
   
7. Clean Response
   ├─→ Strips <think> tags
   └─→ Strips repeated chunk instructions
   
8. Return Markdown
```

**Supports:**
- Providers (`api/services/ai/provider/`): **Groq**, **OpenRouter**, and **Google Gemini** (conditionally initialized based on keys configured in `api/config.py`)
- Models (`api/services/ai/models.py`): role-based routing (`chunking`, `final_doc`, `fallback`, `emergency`)
- Languages: Spanish, English
- Output formats: Markdown, PDF, Word, Multifile `.zip`

### 8. **Exporters** (`api/export/` + `ZipService`)

Convert Markdown to final output formats:

| Exporter | Technology | Benefits |
|----------|------------|----------|
| PDF | `markdown-pdf` (`api/export/pdf_gen.py`) | Direct rendering from Markdown |
| DOCX | `python-docx` (`api/export/docx_gen.py`) | Editable, structured formatting |
| Markdown | Native | Versionable, readable |
| Multifile ZIP | `zipfile` | N packaged `.md` documents |

---

## 🔄 Data Flows

### Flow 1: Document from JSON (Fast)

```json
POST /api/download/markdown
{
  "code": "def hello(): print('hello')",
  "extra": "Add examples",
  "language": "en"
}
↓
DocumentadorIA.generar()
↓
Downloads file: documentacion_2024-....md
(MIME: text/markdown)
```
⏱️ **Expected time:** 1–3 seconds

> The `pdf` and `docx` formats on the same endpoint download `application/pdf` and `.docx` respectively. JSON is not returned on success.

### Flow 2: Project from ZIP — Consolidated (markdown, pdf, word)

```
POST /api/upload-zip
├─ file: project.zip
├─ doc_type: markdown   # or pdf, word
└─ language: en
   ↓
   ZipService.extraer_zip()
   ├─ 20 extracted files
   └─ 2 invalid
      ↓
      ChunkingService.create_chunks()
      ├─ Chunk 1: 5 files
      └─ Chunk 2: 5 files
         ↓
         For each chunk:
         ├─ Generate hash → check cache
         ├─ Miss → DocumentadorIA.generar()
         └─ Save to cache
            ↓
            Consolidate Documentation
            ├─ Merge sections
            └─ Apply Extra Requirements
               ↓
               Downloads the resulting file by doc_type:
               ├─ markdown → .md (text/markdown)
               ├─ pdf      → .pdf (application/pdf)
               └─ word     → .docx (application/vnd.openxmlformats-...)
```
⏱️ **Expected time:** 10–30 seconds

> Metadata (`total_files`, `total_chunks`, `cache_stats`, etc.) is only used internally for logging; it is not returned to the client alongside the file.

### Flow 3: Project from ZIP — Multifile

```
POST /api/upload-zip
├─ file: project.zip
├─ doc_type: multifile
└─ language: en
   ↓
   (same extraction and chunking as Flow 2)
         ↓
         For each chunk:
         ├─ DocumentadorIA.generar()
         └─ (no consolidation)
            ↓
            Generate filenames:
            ├─ Chunk 1 → main.py → "main.md"
            ├─ Chunk 2 → api.py + db.py → "api+db.md"
            └─ ...
               ↓
               ZipService.crear_zip()
               └─ In-memory .zip with N .md files
                  ↓
                  send_file(..., mimetype="application/zip")
```
⏱️ **Expected time:** 10–30 seconds (similar, without the extra consolidation step)

---

## 🛡️ Error Handling

### Validations

```
ZIP Input
├─ Per-IP rate limit exceeded → 429 Too Many Requests (Retry-After, X-RateLimit-*)
├─ Request > 15 MB → 413 Payload Too Large
├─ Not a ZIP / ZIP Bomb / Path Traversal / > 300 files / > 40 MB uncompressed? → 400 Bad Request
├─ No valid files? → 400 No Valid Files
└─ ✓ Valid → Process
     ├─ AI provider saturation → 429 Too Many Requests
     ├─ AI error with no available fallback → 500 Internal Server Error
     └─ Redis error → Operates without cache / fail-open rate limiter
```

### Fallbacks

1. **If primary AI fails** → Tries `fallback` and `emergency` (up to 3 retries with backoff per model)
2. **If Redis fails** → Operates without cache (slower) and in *fail-open* mode for rate limiting
3. **If all providers fail due to quota** → Returns HTTP `429` or `500` as JSON with `codigo_error`

---

## 📊 Design Decisions

| Decision | Reason | Rejected Alternatives |
|----------|--------|-----------------------|
| Redis for cache | Distributed + serverless-ready | In-memory dict (not persistent) |
| Redis for rate limiting | Shared across instances | In-memory token bucket |
| Multi-provider (Groq + OpenRouter + Gemini) | Role-based routing (`chunking`, `final_doc`, `fallback`, `emergency`) and quota resilience | Single provider |
| Automatic chunking + multi-round consolidation | Large projects without exceeding context windows | Processing everything in a single call |
| Multilingual | Global clients (ES/EN) | Spanish only |
| Docker PaaS + Vercel support | Docker PaaS supports up to 15 MB and long consolidations; Vercel handles lightweight loads | Serverless only (~4.5 MB cap and timeouts) |

---

## 🚀 Scalability

### Current Limits

| Factor | Limit | Notes |
|--------|-------|-------|
| HTTP request (`MAX_CONTENT_LENGTH`) | 15 MB | Configured in `api/main.py` (HTTP 413 if exceeded); Vercel enforces ~4.5 MB at its edge |
| Uncompressed ZIP size | 40 MB | Anti ZIP Bomb validation in `ZipService.validar_zip_seguro` |
| Total files in ZIP | 300 | Safety limit in `ZipService.MAX_FILES_COUNT` |
| Default eligible files | 50 | `ZipService.DEFAULT_MAX_ELIGIBLE_FILES` |
| Per-IP rate limiting | 10 req/min (AI), 30 req/min (preview) | `EndpointRateLimiter` with `Retry-After` and `X-RateLimit-*` headers |

### Future Improvements

- [ ] Parallel chunk processing
- [ ] Distributed cache (Redis Cluster)
- [ ] WebSocket for real-time progress
- [ ] Webhooks for notifications
- [ ] S3 storage for history
- [ ] Database for statistics

---

## 🔐 Security

### Secrets Management
- Environment variables (`GROQ_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `REDIS_URL`) defined in `.env` (see `.env.example`)
- Excluded from git via `.gitignore`
- Configured in the hosting dashboard (Docker PaaS / Vercel)

### Input Validation
- Valid `.zip` file verification and max HTTP body size (`15 MB`)
- *ZIP Bomb* protection (`40 MB` uncompressed, max `300` files)
- *Path Traversal* protection (blocks absolute paths and `..`)
- Relative path sanitization on `multifile` export

### Rate Limiting
- Per-model TPM limiting toward AI providers
- Per-IP rate limiting (`10 req/min` on `/api/download/<file_type>` and `/api/upload-zip`; `30 req/min` on `/api/preview-zip`)
- Abuse prevention on public deployments

---

## 📈 Monitoring

### Available Logs

```python
# INFO level
logger.info(f"ZIP recibido: {filename}, {size} bytes")
logger.info(f"Chunks creados: {len(chunks)}")
logger.info(f"Cache hit rate: {hit_rate}%")

# ERROR level
logger.error(f"Error en IA: {str(e)}")
```

### Returned Metrics

The API does not expose metrics in success responses. Metadata (`total_files`, `total_chunks`, `cache_stats`, `elapsed_time_seconds`, `input_size_bytes`, etc.) is computed in `ZipController`/`DownloadController` and recorded only in logs.

#### ZIP structure JSON response (`POST /api/preview-zip`)
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

#### Error responses (JSON)
```json
{
  "error": "Solo se permiten archivos .zip",
  "codigo_error": "INVALID_FILE_TYPE"
}
```

---

## 📚 References

- [Groq API Docs](https://console.groq.com/docs)
- [Redis Documentation](https://redis.io/documentation)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [markdown-pdf](https://pypi.org/project/markdown-pdf/)
- [Python-docx](https://python-docx.readthedocs.io/)
