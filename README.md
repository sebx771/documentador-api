# 📚 EasyDocs

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-green?logo=flask)](https://flask.palletsprojects.com/)
[![Groq API](https://img.shields.io/badge/Groq-Llama%203.1-orange)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI/CD](https://github.com/yourusername/proyecto_py/workflows/CI%2FCD/badge.svg)](https://github.com/yourusername/proyecto_py/actions)

**EasyDocs** es un asistente de ingeniería de software impulsado por **Inteligencia Artificial** que automatiza la generación de documentación técnica. Transforma código fuente en documentación detallada, profesional y lista para entregar en múltiples formatos.

🚀 **Servicio AI** con Groq API | 📄 **Múltiples formatos** (Markdown, PDF, Word, Multifile .zip) | 🌍 **Multiidioma** (ES/EN) | ⚡ **Serverless-ready** (Vercel)

---

## 📋 Tabla de Contenidos

- [Características](#características)
- [Stack Tecnológico](#stack-tecnológico)
- [Instalación Rápida](#instalación-rápida)
- [Uso](#uso)
- [Configuración](#configuración)
- [Arquitectura](#arquitectura)
- [API Endpoints](#api-endpoints)
- [Desarrollo](#desarrollo)
- [Mejoras futuras](#mejoras-futuras)
- [Deployment](#deployment)
- [Documentación](#documentación)
- [Contributing](#contributing)
- [License](#license)

---

## Características

✅ **Análisis Automático de Código** - Detecta lenguajes y patrones automáticamente  
✅ **Generación Inteligente** - Crea documentación detallada y coherente  
✅ **Múltiples Formatos** - Exporta a Markdown, PDF, Word  
✅ **Multiidioma** - Soporta Español e Inglés automáticamente  
✅ **Caché Inteligente** - Reutiliza resultados por hash de contenido  
✅ **Rate Limiting** - Control de tokens con Redis (TPM/RPM)  
✅ **Procesamiento de ZIPs** - Procesa proyectos completos automáticamente  
✅ **Chunking Automático** - Divide proyectos grandes en secciones manejables  
✅ **Salida Multifile** - Genera un .zip con N documentos .md (uno por módulo) desde proyectos ZIP  

---

## 🛠️ Stack Tecnológico

| Componente | Herramienta | Versión |
|-----------|-----------|---------|
| **Runtime** | Python | 3.12+ |
| **Framework Web** | Flask | 3.1.3 |
| **IA/LLM** | Groq API (Llama 3.1) | Latest |
| **Caché** | Redis | 7.4.0 |
| **Exportación** | FPDF, python-docx | Latest |
| **Deployment** | Vercel Serverless | Python Runtime |

---

## 🚀 Instalación Rápida

### 1. **Clonar el repositorio**
```bash
git clone https://github.com/sebx771/proyecto_py.git
cd proyecto_py
```

### 2. **Crear entorno virtual**
```bash
python -m venv venv

# En Windows:
venv\Scripts\activate

# En macOS/Linux:
source venv/bin/activate
```

### 3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

### 4. **Configurar variables de entorno**
```bash
cp .env.example .env
```

Edita `.env` y completa:
```env
GROQ_API_KEY=your_groq_api_key_here
REDIS_URL=redis://localhost:6379
FLASK_ENV=development
```

### 5. **Ejecutar aplicación**
```bash
python -m api.main
```

La API estará disponible en `http://localhost:5000`

---

## 📖 Uso

### Opción 1: Enviar Código Directo (JSON)

```bash
curl -X POST http://localhost:5000/api/download/markdown \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def hello():\n    print(\"Hello World\")",
    "extra": "Add docstring examples",
    "language": "es"
  }'
```

### Opción 2: Procesar ZIP Completo

```bash
curl -X POST http://localhost:5000/api/upload-zip \
  -F "file=@myproject.zip" \
  -F "doc_type=markdown" \
  -F "language=es"
```

### Opción 3: Multifile (ZIP de documentos .md)

```bash
curl -X POST http://localhost:5000/api/upload-zip \
  -F "file=@myproject.zip" \
  -F "doc_type=multifile" \
  -F "language=es"
```
Devuelve un `.zip` con un archivo `.md` por cada chunk de archivos relacionados.

### Opción 4: Previsualizar ZIP

```bash
curl -X POST http://localhost:5000/api/preview-zip \
  -F "file=@myproject.zip"
```

### Respuesta Exitosa

Los endpoints de generación no devuelven JSON: descargan directamente el archivo generado.

- `/api/download/<type>` → **archivo** (`.md`, `.pdf` o `.docx`, según `type`)
- `/api/upload-zip` con `doc_type` en `markdown|pdf|word` → **archivo** de documentación consolidada
- `/api/upload-zip` con `doc_type=multifile` → **.zip** con un `.md` por cada chunk

Los únicos endpoints que devuelven JSON como respuesta normal son `GET /`, `GET /api/download` (información) y `POST /api/preview-zip` (estructura del ZIP).

**Respuesta JSON (casos de error), por ejemplo:**
```json
{
  "error": "Tipo de archivo no válido. Use 'pdf', 'markdown' o 'docx'",
  "codigo_error": "INVALID_FILE_TYPE"
}
```

---

## ⚙️ Configuración

### Variables de Entorno Requeridas

```env
# Groq API (obligatorio)
GROQ_API_KEY=sk_xxx

# Redis (obligatorio para rate limiting)
REDIS_URL=redis://localhost:6379

# Flask (opcional)
FLASK_ENV=development
DEBUG=True
```

### Archivos de Configuración

- `.env` - Variables privadas (NO incluir en git)
- `.env.example` - Template de variables (incluir en git)
- `vercel.json` - Configuración para deployment en Vercel

---

## 🏗️ Arquitectura

La aplicación sigue una **arquitectura de servicios desacoplada**:

```
Flask App
    ↓
Routes (ZIP/Download)
    ↓
DocumentationOrchestrator (orquestador)
    ├── ZipService (extracción)
    ├── ChunkingService (división de código)
    ├── CacheService (Redis)
    ├── DocumentadorIA (generación con Groq)
    └── Ratelimiter (control TPM/RPM)
    ↓
Exporters (PDF, Word, Markdown)
```

Para detalles completos, consulta [ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 🔌 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Welcome message y documentación de API (JSON) |
| `GET` | `/api/download` | Información de los endpoints de descarga (JSON) |
| `POST` | `/api/download/<type>` | Genera documentación desde JSON y descarga el archivo (`.md`, `.pdf` o `.docx`) |
| `POST` | `/api/upload-zip` | Procesa ZIP y descarga la documentación (`.md`, `.pdf`, `.docx` o `.zip` multifile) |
| `POST` | `/api/preview-zip` | Previsualiza estructura del ZIP (JSON) |

Para documentación interactiva, inicia la API y accede a `http://localhost:5000/`

---

## 💻 Desarrollo

### Estructura del Proyecto

```
proyecto_py/
├── api/
│   ├── main.py              # Punto de entrada Flask
│   ├── routes/              # Endpoints
│   │   ├── download.py
│   │   └── zip.py
│   ├── services/            # Lógica de negocio
│   │   ├── documentation_orchestrator.py
│   │   ├── chunking_service.py
│   │   ├── cache_service.py
│   │   ├── rate_limiter.py
│   │   └── ai/
│   │       ├── ai_service.py
│   │       ├── models.py
│   │       ├── prompts/
│   │       └── provider/
│   │           ├── base_provider.py
│   │           ├── groq_provider.py
│   │           └── structures.py
│   ├── export/              # Exportadores
│   │   ├── pdf_gen.py
│   │   └── docx_gen.py
│   └── utils/               # Utilidades
├── test/                    # Tests
├── docs/                    # Documentación
├── requirements.txt
├── .env.example
└── vercel.json
```

### Instalar en modo desarrollo

```bash
pip install -r requirements.txt
```


### Ejecutar con hot-reload

```bash
python -m flask --app api.main run --reload
```

---

## Mejoras futuras

Este repo ya contempla mejoras previstas, incluyendo:

- Integrar `api/services/endpoint_rate_limiter.py` para **rate limiting por endpoint** (actualmente el servicio está listo para futuras integraciones).
- Añadir una sección real de **Testing con pytest** una vez que el proyecto tenga esa capa como requisito documentado e integrado.

> Nota: en este momento, el README no mantiene una guía de testing basada en pytest como “configuración obligatoria” (aunque existan archivos de prueba en `test/`).


---

## 🌍 Deployment

### En Vercel

1. **Push a GitHub**
```bash
git push origin main
```

2. **Configurar en Vercel Dashboard**
   - Importar repositorio
   - Agregar variables de entorno (`GROQ_API_KEY`, `REDIS_URL`)
   - Deploy

3. **Verificar deployment**
```bash
curl https://tu-proyecto.vercel.app/
```

---

## 📚 Documentación

- [**Documentación Técnica (ES)**](docs/doc_es.md) - Componentes y servicios
- [**Technical Documentation (EN)**](docs/doc_en.md) - Components and services  
- [**ARCHITECTURE.md**](docs/ARCHITECTURE.md) - Diagrama y flujos
- [**SETUP.md**](docs/SETUP.md) - Guía de instalación detallada

---

## 🤝 Contributing

Las contribuciones son bienvenidas. Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

Por favor asegúrate que:
- ✅ El código pasa los tests
- ✅ Incluyes docstrings
- ✅ Sigues PEP 8
- ✅ Actualizas la documentación

---

## 📄 License

Este proyecto está bajo la licencia [MIT](LICENSE). Ver archivo LICENSE para más detalles.

---

## 📞 Soporte

- 📧 Email: sebascova18@gmail.com
- 🐙 GitHub Issues: [Reportar bug](https://github.com/Sebito771/documentador-api/issues)
- 💬 Discussions: [Hacer pregunta](https://github.com/Sebito771/documentador-api/discussions)


