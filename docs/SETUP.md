# 🛠️ Guía de Instalación Detallada

## Requisitos Previos

- **Python 3.12+** ([descargar](https://www.python.org/downloads/))
- **Git** ([descargar](https://git-scm.com/))
- **Redis** (local o en la nube)
- **Groq API Key** ([obtener gratis](https://console.groq.com/))

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
- Flask 3.1.3 - Framework web
- Groq 1.1.2 - SDK Groq
- Redis 7.4.0 - Cliente Redis
- python-docx 1.1.2 - Exportación Word
- FPDF - Exportación PDF

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

```env
# ==========================================
# GROQ API CONFIGURATION
# ==========================================
GROQ_API_KEY=sk_xxxxxxxxxxxxxxxxxxxxx

# ==========================================
# REDIS CONFIGURATION  
# ==========================================
REDIS_URL=redis://localhost:6379
```

**Cómo obtener `GROQ_API_KEY`:**

1. Ir a [console.groq.com](https://console.groq.com)
2. Crear cuenta (gratis)
3. Ir a API Keys
4. Crear nueva clave
5. Copiar la clave a `.env`

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
REDIS_URL=redis://localhost:6379
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

## Instalación para Desarrollo

### Instalar Herramientas de Desarrollo

```bash
pip install -r requirements.txt
```
## tests
de momento no se usa pytest , las pruebas son debugs manuales 

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

#### 1. Push del Código a GitHub

```bash
git add .
git commit -m "Setup final: documentación y CI/CD"
git push origin main
```

#### 2. Importar en Vercel

1. Ir a [vercel.com](https://vercel.com)
2. Click en "New Project"
3. Conectar GitHub repository
4. Seleccionar `proyecto_py`
5. Click "Import"

#### 3. Configurar Variables de Entorno

En Vercel Dashboard → Settings → Environment Variables:

```
GROQ_API_KEY = sk_xxxxxxxxxxxxxxxxxxxxx
REDIS_URL = redis://...
```

#### 4. Deploy

- Vercel detectará automáticamente `vercel.json`
- Ejecutará `pip install -r requirements.txt`
- Deployará la función

**Output esperado:**
```
✓ Production Function ready in 12s
✓ Preview URL: https://proyecto-py-xxx.vercel.app
```

#### 5. Verificar Deployment

```bash
curl https://proyecto-py-xxx.vercel.app/
```

Deberías recibir:
```json
{
  "message": "Welcome to EasyDocs API!",
  "version": "2.3.0",
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
# Debería ser: redis://localhost:6379

# 3. Si usas Redis en la nube, verifica la URL
# Ej: redis://xxxxx:xxxxx@xxxxx.upstash.io:xxxxx

# 4. Reinicia la aplicación
python -m api.main
```

### Error: `Invalid GROQ_API_KEY`

**Solución:**
```bash
# 1. Verifica que la clave es válida
# Ve a https://console.groq.com/keys

# 2. Copia la clave completa (sin espacios)
# Ejemplo: sk_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p

# 3. Actualiza .env
GROQ_API_KEY=sk_1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p

# 4. Reinicia la aplicación
python -m api.main
```

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
grep -E "^GROQ_API_KEY|^REDIS_URL" .env

echo "5. Estructura de carpetas..."
ls -la api/services/ai/
ls -la api/export/
ls -la api/routes/

echo "✓ Todo listo! Puedes ejecutar: python -m api.main"
```

---

## Siguiente: Documentación API

Una vez instalado, consulta:
- [README.md](../README.md) - Uso general
- [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitectura detallada
- [API Endpoints](#) - Documentación interactiva en `/`
