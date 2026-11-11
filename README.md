# 📚 EasyDocs

Español | [English](README.en.md)

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![Flask 3.1.3](https://img.shields.io/badge/Flask-3.1.3-green?logo=flask)](https://flask.palletsprojects.com/)
[![Groq API](https://img.shields.io/badge/Groq-API-orange)](https://groq.com/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-API-purple)](https://openrouter.ai/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini-blue)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**EasyDocs** es una API REST en Flask que genera documentación técnica a partir de fragmentos de código fuente o proyectos empaquetados en `.zip`, utilizando modelos de lenguaje (Groq, OpenRouter y Google Gemini) y exportación en Markdown, PDF, Word (`.docx`) o archivos Markdown separados (`multifile`).

---

## ✨ Características

- Generación de documentación técnica en **español** e **inglés** (`language: "es" | "en"` o cabecera `Accept-Language`).
- Formatos de salida: **Markdown** (`.md`), **PDF** (`.pdf`), **Word** (`.docx`) y **Multifile** (`.zip` con un `.md` por grupo lógico de archivos).
- Enrutamiento multi-proveedor por rol (`chunking`, `final_doc`, `fallback`, `emergency`) con **Groq**, **OpenRouter** y **Google Gemini**.
- Caché en **Redis** por hash SHA-256 (incluye código, idioma y versión de prompt).
- Rate limiting en dos niveles: por **IP** (`10 req/min` en generación IA, `30 req/min` en previsualización) y por **TPM/RPM** hacia los proveedores.
- Validación de seguridad en archivos `.zip`: límite de `15 MB` por petición HTTP, `40 MB` descomprimidos, máximo `300` archivos en el ZIP (`50` elegibles por lote) y bloqueo de *Path Traversal*.
- Extensiones soportadas: `.py`, `.java`, `.go`, `.js`, `.ts`, `.php`, `.css`, `.html`, `.json`, `.xml`, `.yml`, `.yaml`, `.kt`.

---

## 🛠️ Stack Tecnológico

| Componente | Tecnología |
|---|---|
| **Runtime** | Python 3.12+ |
| **Framework** | Flask 3.1.3 |
| **Proveedores IA** | `groq`, `openai` (OpenRouter), `google-genai` (Gemini) |
| **Caché y Rate Limiting** | Redis 7.4.0 |
| **Exportación** | `markdown-pdf`, `python-docx`, `zipfile` |
| **Deployment** | Docker Compose / PaaS / Vercel |

---

## 🚀 Inicio Rápido (Docker)

```bash
git clone https://github.com/sebx771/documentador-api.git
cd documentador-api
cp .env.example .env
```

Configura en `.env` `REDIS_URL` y **al menos una** clave de proveedor IA (`GROQ_API_KEY`, `OPENROUTER_API_KEY` o `GEMINI_API_KEY`), y levanta el entorno de desarrollo:

```bash
docker compose -f docker-compose-dev.yml up --build
```

La API quedará disponible en `http://localhost:5000`. Para instalación local sin Docker (`venv` + Redis), Docker en producción (`docker-compose.yml`), Vercel y despliegue en PaaS, consulta [docs/SETUP.md](docs/SETUP.md).

---

## 📖 Uso y Endpoints

| Método | Endpoint | Descripción | Respuesta en éxito |
|---|---|---|---|
| `GET` | `/` | Información de versión, endpoints y formatos | JSON |
| `GET` | `/api/download` | Esquema y límites de `/api/download/<file_type>` | JSON |
| `POST` | `/api/download/<file_type>` | Genera documentación desde JSON (`file_type`: `markdown`, `pdf` o `docx`) | Descarga de archivo |
| `POST` | `/api/upload-zip` | Procesa un `.zip` (`doc_type`: `markdown`, `pdf`, `word` o `multifile`) | Descarga de archivo o `.zip` |
| `POST` | `/api/preview-zip` | Previsualiza archivos elegibles e ignorados dentro de un `.zip` | JSON |

> Solo `GET /`, `GET /api/download` y `POST /api/preview-zip` devuelven JSON en éxito. Todas las respuestas de error (`400`, `413`, `429`, `500`) devuelven JSON con `error` y `codigo_error`.

### Generar documentación desde JSON

```bash
curl -X POST http://localhost:5000/api/download/markdown \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello(): print(\"Hello\")", "language": "es", "extra": "Incluir ejemplo de uso"}'
```

### Procesar un proyecto ZIP

```bash
curl -X POST http://localhost:5000/api/upload-zip \
  -F "file=@myproject.zip" \
  -F "doc_type=markdown" \
  -F "language=es" \
  -F "extra_requirements=Enfocarse en endpoints y seguridad"
```

Valores admitidos para `doc_type`: `markdown` (por defecto), `pdf`, `word`, `multifile`.

### Previsualizar un archivo ZIP

```bash
curl -X POST http://localhost:5000/api/preview-zip \
  -F "file=@myproject.zip"
```

---

## 🏗️ Arquitectura

EasyDocs separa las rutas HTTP, los controladores de validación, el paquete modular `api/services/orchestrator/` (extracción, generación por chunks y consolidación multirronda), los clientes de proveedores IA y los exportadores.

Consulta los diagramas, flujos de datos, límites y decisiones de diseño en [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

---

## 🌍 Despliegue (Resumen)

- **Docker PaaS (recomendado para proyectos ZIP grandes):** usa `Dockerfile` o `docker-compose.yml` con un Redis externo (`REDIS_URL`). Soporta cargas de hasta `15 MB` y consolidaciones largas sin restricciones serverless.
- **Vercel Serverless:** configurado mediante `vercel.json`. Ten en cuenta el límite de cuerpo HTTP de Vercel (~4.5 MB) y los timeouts de ejecución serverless para ZIPs grandes o síntesis multirronda.

Los pasos detallados están en [docs/SETUP.md](docs/SETUP.md).

---

## 📚 Documentación

- [docs/SETUP.md](docs/SETUP.md) — Instalación local, Docker desarrollo/producción, Vercel, tests y solución de problemas.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Arquitectura interna (`v3.4.0`), flujos, contratos de error, límites y decisiones técnicas.
- [CHANGELOG.md](CHANGELOG.md) — Historial de versiones y cambios.
- [README.en.md](README.en.md) — Documentación principal en inglés.

---

## 🤝 Contribuir

1. Haz fork del repositorio y crea una rama desde `main`.
2. Ejecuta la suite de pruebas con `python test/run_tests.py`.
3. Haz commit siguiendo Conventional Commits y abre un Pull Request.

---

## 📄 Licencia

Distribuido bajo licencia [MIT](LICENSE).

---

## 📞 Soporte

- Correo: `sebascova18@gmail.com`
- Issues: [GitHub Issues](https://github.com/sebx771/documentador-api/issues)
