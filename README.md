# 📚 EasyDocs

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-green?logo=flask)](https://flask.palletsprojects.com/)
[![Openrouter](https://img.shields.io/badge/Openrouter-free%20-yellow)](https://openrouter.com/)
[![Groq API](https://img.shields.io/badge/Groq-Llama%203.1-orange)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**EasyDocs** es un asistente de ingeniería de software impulsado por **IA** que automatiza la generación de documentación técnica. Transforma código fuente en documentación profesional en múltiples formatos.

🚀 **IA** con Groq + OpenRouter + Gemini| 📄 **Formatos**: Markdown, PDF, Word, Multifile `.zip` | 🌍 **Multiidioma** (ES/EN) | ⚡ **Serverless-ready** (Vercel)

---

## Características

✅ Generación inteligente de documentación  
✅ Múltiples formatos de exportación  
✅ Multiidioma y multi-proveedor AI  
✅ Caché inteligente con Redis  
✅ Rate limiting (TPM/RPM)  
✅ Procesamiento de ZIPs y chunking automático  
✅ Soporte multi-lenguaje: Python, Java, JS, Kotlin  

---

## 🛠️ Stack Tecnológico

| Componente | Herramienta |
|-----------|-----------|
| **Runtime** | Python 3.12+ |
| **Framework** | Flask 3.1.3 |
| **IA/LLM** | Groq API + OpenRouter + Gemini |
| **Caché** | Redis 7.4.0 |
| **Exportación** | FPDF, python-docx, markdown-pdf |
| **Deployment** | Vercel Serverless |

---

## 🚀 Instalación Rápida

### Con Docker (recomendado) (desarrollo)

```bash
git clone https://github.com/sebx771/proyecto_py.git
cd proyecto_py
cp .env.example .env
```

Configura `GROQ_API_KEY` (y las demás claves de IA que quieras usar) en `.env`. Luego levanta la API y Redis:

```bash
docker compose -f docker-compose-dev.yml up --build
```

La API estará disponible en `http://localhost:5000`. Para detenerla, ejecuta `docker compose -f docker-compose-dev.yml down`.

### Docker (produccion)

```bash
docker compose -f docker-compose-dev.yml down
```

El `docker-compose.yml` de producción no levanta Redis y lee `REDIS_URL` desde `.env` o desde las variables del hosting. Para usar Upstash, configura allí su URL `rediss://`.



### Sin Docker

Si no tienes Docker, instala y levanta Redis por separado y configura `REDIS_URL` en `.env`. Después instala las dependencias y ejecuta la API:

```bash
git clone https://github.com/sebx771/proyecto_py.git
cd proyecto_py
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env
python -m api.main
```

Variables de entorno necesarias:
```env
GROQ_API_KEY=tu_api_key
REDIS_URL=redis://localhost:6379/0
# Opcional:
OPENROUTER_API_KEY=tu_api_key
```

---

## 📖 Uso

### Enviar código directo (JSON)
```bash
curl -X POST http://localhost:5000/api/download/markdown \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello(): print(\"Hello\")", "language": "es"}'
```

### Procesar ZIP
```bash
curl -X POST http://localhost:5000/api/upload-zip \
  -F "file=@myproject.zip" \
  -F "doc_type=markdown|pdf|word|multifile"
```

### Previsualizar ZIP
```bash
curl -X POST http://localhost:5000/api/preview-zip \
  -F "file=@myproject.zip"
```

> Los endpoints de generación descargan el archivo directamente. Solo `GET /`, `GET /api/download` y `POST /api/preview-zip` devuelven JSON.

---

## 🔌 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Info de la API (JSON) |
| `POST` | `/api/download/<type>` | Genera doc desde JSON (`.md`, `.pdf`, `.docx`) |
| `POST` | `/api/upload-zip` | Procesa ZIP (`.md`, `.pdf`, `.docx` o `.zip` multifile) |
| `POST` | `/api/preview-zip` | Previsualiza estructura del ZIP (JSON) |

---

## 🏗️ Arquitectura

Servicios desacoplados: Flask → Routes → Controllers → DocumentationOrchestrator → Servicios (Zip, Chunking, Cache, IA, Rate Limiter) → Exporters.

Detalles en [ARCHITECTURE.md](docs/ARCHITECTURE.md).

---


## Estructura principal:

```
api/
├── main.py                 # Entrypoint Flask
├── config.py               # Configuración centralizada
├── routes/                 # Blueprints
├── controllers/            # Lógica de controladores
├── services/               # Lógica de negocio
│   └── ai/                 # Proveedores y prompts
├── export/                 # PDF, DOCX, Markdown
└── utils/                  # Utilidades
```

---

## 🌍 Deployment

1. Push a GitHub
2. Importar en Vercel y configurar variables (`GROQ_API_KEY`, `REDIS_URL`, `OPENROUTER_API_KEY`)
3. Deploy automático


## Deployment con Docker
1 Push a Github
2 escoger tu Paas con soporte para docker (ej , railway , northflank)
3 levanta docker y agrega las variables de entorno AI y Redis

---

## 📚 Documentación

- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [SETUP.md](docs/SETUP.md)
- [CHANGELOG.md](CHANGELOG.md)
- [doc_es.md](docs/doc_es.md) / [doc_en.md](docs/doc_en.md)

---

## 🤝 Contributing

1. Fork y crea una rama
2. Commit y push
3. Abre un Pull Request

---

## 📄 License

MIT

---

## 📞 Soporte

📧 sebascova18@gmail.com | 🐙 [Issues](https://github.com/sebx771/documentador-api/issues)
