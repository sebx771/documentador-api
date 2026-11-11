# 🛠️ Guía de Instalación Detallada

Español | [English](SETUP.en.md)

## Requisitos Previos

- **Python 3.12+** ([descargar](https://www.python.org/downloads/))
- **Git** ([descargar](https://git-scm.com/))
- **Redis** (local, en Docker o en la nube como Upstash)
- **Al menos una clave de proveedor IA:**
  - `GROQ_API_KEY` ([console.groq.com](https://console.groq.com/))
  - `OPENROUTER_API_KEY` ([openrouter.ai](https://openrouter.ai/))
  - `GEMINI_API_KEY` ([aistudio.google.com](https://aistudio.google.com/))

---

## Instalación Local

### Paso 1: Clonar el Repositorio

```bash
git clone https://github.com/sebx771/documentador-api.git
cd documentador-api
```

### Paso 2: Crear Entorno Virtual

**En Windows (PowerShell/CMD):**
```powershell
python -m venv venv
venv\Scripts\activate
```

**En macOS/Linux (Bash/Zsh):**
```bash
python3 -m venv venv
source venv/bin/activate
```

Deberías ver `(venv)` en el prompt de la terminal.

### Paso 3: Actualizar pip

```bash
pip install --upgrade pip
```

### Paso 4: Instalar Dependencias

```bash
pip install -r requirements.txt
```
asegurate que el interprete de python que usa el entorno virtual sea el correcto.

**Dependencias principales:**
- `Flask` 3.1.3 — Framework web
- `groq` 1.1.2, `openai` 3.7.0 (OpenRouter), `google-genai` 2.24.0 (Gemini) — SDKs de proveedores IA
- `redis` 7.4.0 — Cliente Redis (caché y rate limiting)
- `markdown-pdf` 1.13.1 — Exportación PDF
- `python-docx` — Exportación Word (`.docx`)

### Paso 5: Configurar Variables de Entorno

#### Opción A: Crear `.env` manual

```bash
# En Windows
type nul > .env

# En macOS/Linux
touch .env
```

#### Opción B: Copiar desde template

```bash
cp .env.example .env
```

#### Editar `.env`

Usa [`.env.example`](../.env.example) como referencia. El arranque (`api/config.py`) exige **al menos una** clave de proveedor IA (`GROQ_API_KEY`, `OPENROUTER_API_KEY` o `GEMINI_API_KEY`) más `REDIS_URL`:

```env
GROQ_API_KEY="api_key_aqui"
OPENROUTER_API_KEY="api_key_aqui"
GEMINI_API_KEY="api_key_aqui"
REDIS_URL="redis://localhost:6379/0"
DEBUG="false"
```

**Dónde obtener las claves de IA:**
- **Groq:** [console.groq.com](https://console.groq.com)
- **OpenRouter:** [openrouter.ai](https://openrouter.ai)
- **Google Gemini:** [aistudio.google.com](https://aistudio.google.com)

**Cómo obtener `REDIS_URL`:**

**Opción 1: Redis Local**
```bash
# Instalar Redis
# Windows: https://github.com/microsoftarchive/redis/releases
# macOS: brew install redis
# Linux: sudo apt-get install redis-server

# Iniciar Redis
redis-server

# Verificar conexión
redis-cli ping
# Deberías ver: PONG

# Usar en .env:
REDIS_URL=redis://localhost:6379/0
```

**Opción 2: Redis en la Nube (Recomendado para producción)**
- [Upstash](https://upstash.com/) (gratuito 10,000 comandos/día)

### Paso 6: Verificar Instalación

```bash
# Verificar Python
python --version
# Output: Python 3.12.x

# Verificar venv activo
which python
# Output: /ruta/al/venv/bin/python (macOS/Linux)
# O: ruta\a\venv\Scripts\python.exe (Windows)

# Verificar dependencias
pip list
```

### Paso 7: Ejecutar la Aplicación

```bash
# Opción 1: Ejecutar directamente
python -m api.main

# Opción 2: Con Flask CLI
flask --app api.main run --reload

# Output esperado:
# WARNING in flask.app: This is a development server. Do not use it in production.
# Running on http://127.0.0.1:5000
# Press CTRL+C to quit
```

Accede a `http://localhost:5000` en tu navegador.

---

## Dockerización

Con Docker Desktop instalado y un archivo `.env` configurado, puedes levantar la API junto con Redis local para desarrollo:

```powershell
docker compose -f docker-compose-dev.yml up --build
```

La API quedará disponible en `http://localhost:5000`. Para detener los contenedores:

```powershell
docker compose -f docker-compose-dev.yml down
```

El `docker-compose-dev.yml` levanta la API junto con Redis local para desarrollo. Para producción, `docker-compose.yml` levanta únicamente la API (con Gunicorn en el puerto `5000`) y lee `REDIS_URL` desde `.env` o desde las variables del hosting (por ejemplo, una URL `rediss://` de Upstash):

```powershell
docker compose -f docker-compose.yml up -d --build
```

Para detener el stack de producción:

```powershell
docker compose -f docker-compose.yml down
```

---

## Instalación para Desarrollo

### Instalar Herramientas de Desarrollo

```bash
pip install -r requirements.txt
```

### Ejecutar Tests

La suite de pruebas unitarias y de integración está en `test/`:

```bash
python test/run_tests.py
```

### Configurar pre-commit hooks (opcional)

```bash
pip install pre-commit
pre-commit install
```




### Linting y Formateo

```bash
# Formateo automático
black api/
```

---

## Instalación en Vercel (Producción)

### Prerrequisitos

- Repositorio en GitHub
- Cuenta en [Vercel](https://vercel.com)
- Variables de entorno listos

### Pasos

> **Nota sobre límites serverless:** Vercel impone un límite de cuerpo HTTP de ~4.5 MB y timeouts de ejecución por función. Para cargas ZIP de hasta `15 MB` o consolidaciones multirronda largas, usa despliegue con Docker PaaS (`Dockerfile` o `docker-compose.yml`).

#### 1. Push del Código a GitHub

```bash
git push origin main
```

#### 2. Importar en Vercel

1. Ir a [vercel.com](https://vercel.com)
2. Click en "New Project"
3. Conectar GitHub repository
4. Seleccionar `documentador-api`
5. Click "Import"

#### 3. Configurar Variables de Entorno

En Vercel Dashboard → Settings → Environment Variables, configura `REDIS_URL` (ej. Upstash `rediss://...`) y las claves de IA que uses (`GROQ_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`):

```env
GROQ_API_KEY=tu_clave_groq
OPENROUTER_API_KEY=tu_clave_openrouter
GEMINI_API_KEY=tu_clave_gemini
REDIS_URL=rediss://...
DEBUG=false
```

#### 4. Deploy

- Vercel detectará automáticamente `vercel.json`
- Ejecutará `pip install -r requirements.txt`
- Deployará la función

#### 5. Verificar Deployment

```bash
curl https://<tu-proyecto>.vercel.app/
```

Deberías recibir:
```json
{
  "message": "Welcome to EasyDocs API!",
  "version": "3.4.0",
  "endpoints": [...]
}
```

---

## Solución de Problemas

### Error: `ModuleNotFoundError: No module named 'api'`

**Solución:**
```bash
# Asegúrate que estés en la raíz del proyecto
cd /ruta/correcta/documentador-api

# Verifica que venv está activo
# Windows: (venv) debe aparecer en el prompt
# macOS/Linux: (venv) debe aparecer en el prompt

# Instala dependencias nuevamente
pip install -r requirements.txt

# Ejecuta desde raíz
python -m api.main
```

### Error: `ConnectionRefusedError: Redis connection failed`

**Solución:**
```bash
# 1. Verifica que Redis está corriendo
redis-cli ping
# Si no, inicia Redis:
redis-server

# 2. Verifica REDIS_URL en .env
# Debería ser: redis://localhost:6379/0

# 3. Si usas Redis en la nube, verifica la URL
# Ej: redis://xxxxx:xxxxx@xxxxx.upstash.io:xxxxx

# 4. Reinicia la aplicación
python -m api.main
```

### Error: `[CONFIG ERROR] Debes configurar al menos GROQ_API_KEY, OPENROUTER_API_KEY o GEMINI_API_KEY`

**Solución:**
1. Verifica que `.env` existe en la raíz del proyecto y tiene al menos una clave válida (`GROQ_API_KEY`, `OPENROUTER_API_KEY` o `GEMINI_API_KEY`) sin comillas ni espacios sobrantes.
2. Si un proveedor falla con `401`/`403`, regenera la clave en la consola del proveedor correspondiente.
3. Reinicia la aplicación (`python -m api.main`).

### Error: `Port 5000 already in use`

**Solución:**
```bash
# Opción 1: Usar otro puerto
python -m flask --app api.main run --port 5001

# Opción 2: Matar proceso usando puerto 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :5000
kill -9 <PID>
```

### Error: `Python version < 3.12`

**Solución:**
```bash
# Verifica versión actual
python --version

# Actualiza a Python 3.12+
# Windows: https://www.python.org/downloads/
# macOS: brew install python@3.12
# Linux: sudo apt-get install python3.12

# Usa la versión específica
python3.12 -m venv venv
```

---

## Verificación de Instalación

Ejecuta este script para verificar que todo está correcto:

```bash
#!/bin/bash
echo "✓ Verificando instalación de EasyDocs"

echo "1. Python version..."
python --version

echo "2. Dependencias..."
pip list | grep Flask
pip list | grep groq
pip list | grep redis

echo "3. Redis connection..."
redis-cli ping

echo "4. Variables de entorno..."
grep -E "^(GROQ|OPENROUTER|GEMINI)_API_KEY|^REDIS_URL" .env

echo "5. Estructura de carpetas..."
ls -la api/services/orchestrator/
ls -la api/services/ai/
ls -la api/export/
ls -la api/routes/

echo "✓ Todo listo! Puedes ejecutar: python -m api.main"
```

---

## Siguiente: Documentación API

Una vez instalado, consulta:
- [README.md](../README.md) — Inicio rápido y tabla de endpoints
- [ARCHITECTURE.md](ARCHITECTURE.md) — Arquitectura detallada (`v3.4.0`)
- `GET /` — Metadatos en vivo de la API en ejecución
