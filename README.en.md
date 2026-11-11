# 📚 EasyDocs

[Español](README.md) | English

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![Flask 3.1.3](https://img.shields.io/badge/Flask-3.1.3-green?logo=flask)](https://flask.palletsprojects.com/)
[![Groq API](https://img.shields.io/badge/Groq-API-orange)](https://groq.com/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-API-purple)](https://openrouter.ai/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini-blue)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**EasyDocs** is a Flask REST API that generates technical documentation from source code snippets or `.zip` archives using LLM providers (Groq, OpenRouter, and Google Gemini), exporting to Markdown, PDF, Word (`.docx`), or separate Markdown files (`multifile`).

---

## ✨ Features

- Bilingual documentation generation in **Spanish** and **English** (`language: "es" | "en"` or `Accept-Language` header).
- Output formats: **Markdown** (`.md`), **PDF** (`.pdf`), **Word** (`.docx`), and **Multifile** (`.zip` containing one `.md` per logical chunk).
- Role-based multi-provider AI routing (`chunking`, `final_doc`, `fallback`, `emergency`) across **Groq**, **OpenRouter**, and **Google Gemini**.
- **Redis** SHA-256 content-hash caching (keyed by content, language, and prompt version).
- Two-tier rate limiting: per-**IP** (`10 req/min` on AI generation endpoints, `30 req/min` on ZIP preview) and per-provider **TPM/RPM** token buckets.
- ZIP security validation: `15 MB` HTTP payload cap, `40 MB` uncompressed size cap, `300` max files per archive (`50` eligible source files per batch), and *Path Traversal* protection.
- Supported file extensions: `.py`, `.java`, `.go`, `.js`, `.ts`, `.php`, `.css`, `.html`, `.json`, `.xml`, `.yml`, `.yaml`, `.kt`.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Runtime** | Python 3.12+ |
| **Framework** | Flask 3.1.3 |
| **AI Providers** | `groq`, `openai` (OpenRouter), `google-genai` (Gemini) |
| **Cache & Rate Limiting** | Redis 7.4.0 |
| **Exporting** | `markdown-pdf`, `python-docx`, `zipfile` |
| **Deployment** | Docker Compose / PaaS / Vercel |

---

## 🚀 Quick Start (Docker)

```bash
git clone https://github.com/sebx771/documentador-api.git
cd documentador-api
cp .env.example .env
```

Set `REDIS_URL` and **at least one** AI provider key (`GROQ_API_KEY`, `OPENROUTER_API_KEY`, or `GEMINI_API_KEY`) in `.env`, then start the development stack:

```bash
docker compose -f docker-compose-dev.yml up --build
```

The API will be available at `http://localhost:5000`. For local installation without Docker (`venv` + Redis), production Docker (`docker-compose.yml`), Vercel, and PaaS deployment, see [docs/SETUP.en.md](docs/SETUP.en.md).

---

## 📖 Usage & Endpoints

| Method | Endpoint | Description | Success Response |
|---|---|---|---|
| `GET` | `/` | API version, endpoints, and supported formats | JSON |
| `GET` | `/api/download` | Schema and limits for `/api/download/<file_type>` | JSON |
| `POST` | `/api/download/<file_type>` | Generate docs from JSON (`file_type`: `markdown`, `pdf`, or `docx`) | File download |
| `POST` | `/api/upload-zip` | Process a `.zip` archive (`doc_type`: `markdown`, `pdf`, `word`, or `multifile`) | File or `.zip` download |
| `POST` | `/api/preview-zip` | Preview eligible and ignored files inside a `.zip` | JSON |

> Only `GET /`, `GET /api/download`, and `POST /api/preview-zip` return JSON on success. All error responses (`400`, `413`, `429`, `500`) return JSON with `error` and `codigo_error`.

### Generate documentation from JSON

```bash
curl -X POST http://localhost:5000/api/download/markdown \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello(): print(\"Hello\")", "language": "en", "extra": "Include a usage example"}'
```

### Process a ZIP project

```bash
curl -X POST http://localhost:5000/api/upload-zip \
  -F "file=@myproject.zip" \
  -F "doc_type=markdown" \
  -F "language=en" \
  -F "extra_requirements=Focus on endpoints and security"
```

Supported `doc_type` values: `markdown` (default), `pdf`, `word`, `multifile`.

### Preview a ZIP file

```bash
curl -X POST http://localhost:5000/api/preview-zip \
  -F "file=@myproject.zip"
```

---

## 🏗️ Architecture

EasyDocs separates HTTP routes, validation controllers, the modular `api/services/orchestrator/` package (extraction, chunk generation, and multi-round consolidation), AI provider adapters, and exporters.

See component diagrams, data flows, operational limits, and design decisions in [docs/ARCHITECTURE.en.md](docs/ARCHITECTURE.en.md).

---

## 🌍 Deployment (Summary)

- **Docker PaaS (recommended for large ZIP workloads):** deploy with `Dockerfile` or `docker-compose.yml` connected to an external Redis instance (`REDIS_URL`). Supports payloads up to `15 MB` and multi-round LLM consolidation without serverless timeouts.
- **Vercel Serverless:** configured via `vercel.json`. Keep in mind Vercel's ~4.5 MB request body ceiling and serverless execution timeouts for large ZIPs or multi-round synthesis.

Full deployment steps are documented in [docs/SETUP.en.md](docs/SETUP.en.md).

---

## 📚 Documentation

- [docs/SETUP.en.md](docs/SETUP.en.md) — Local installation, dev/prod Docker, Vercel, tests, and troubleshooting.
- [docs/ARCHITECTURE.en.md](docs/ARCHITECTURE.en.md) — Internal architecture (`v3.4.0`), data flows, error contracts, limits, and design decisions.
- [CHANGELOG.md](CHANGELOG.md) — Release history and changes.
- [README.md](README.md) — Main README in Spanish.

---

## 🤝 Contributing

1. Fork the repository and create a branch from `main`.
2. Run the test suite with `python test/run_tests.py`.
3. Commit using Conventional Commits and open a Pull Request.

---

## 📄 License

Distributed under the [MIT](LICENSE) License.

---

## 📞 Support

- Email: `sebascova18@gmail.com`
- Issues: [GitHub Issues](https://github.com/sebx771/documentador-api/issues)
