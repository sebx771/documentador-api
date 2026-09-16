# 📚 EasyDocs

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-green?logo=flask)](https://flask.palletsprojects.com/)
[![Openrouter](https://img.shields.io/badge/Openrouter-free%20-yellow)](https://openrouter.com/)
[![Groq API](https://img.shields.io/badge/Groq-Llama%203.1-orange)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**EasyDocs** es un asistente de ingeniería de software impulsado por **IA** que automatiza la generación de documentación técnica. Transforma código fuente en documentación profesional en múltiples formatos.

🚀 **IA** con Groq + OpenRouter | 📄 **Formatos**: Markdown, PDF, Word, Multifile `.zip` | 🌍 **Multiidioma** (ES/EN) | ⚡ **Serverless-ready** (Vercel)

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
| **IA/LLM** | Groq API + OpenRouter |
| **Caché** | Redis 7.4.0 |
| **Exportación** | FPDF, python-docx, markdown-pdf |
| **Deployment** | Vercel Serverless |

---

## 🚀 Instalación Rápida

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

## 💻 Desarrollo

```bash
pip install -r requirements.txt
python -m flask --app api.main run --reload
```

## 🐳 Dockerización

Requiere Docker Desktop y un archivo `.env` con las claves de IA. Para levantar la API y Redis local:

```bash
docker compose up --build
```

La API estará disponible en `http://localhost:5000`. Para detener los servicios:

```bash
docker compose down
```

El `docker-compose.yml` usa Redis local. En un despliegue Docker con Upstash, configura `REDIS_URL` en el entorno de la plataforma y ejecuta solo la imagen construida con el `Dockerfile`.

Estructura principal:
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

