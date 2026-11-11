# 🛠️ Detailed Setup Guide

[Español](SETUP.md) | English

## Prerequisites

- **Python 3.12+** ([download](https://www.python.org/downloads/))
- **Git** ([download](https://git-scm.com/))
- **Redis** (local, in Docker, or cloud-hosted such as Upstash)
- **At least one AI provider key:**
  - `GROQ_API_KEY` ([console.groq.com](https://console.groq.com/))
  - `OPENROUTER_API_KEY` ([openrouter.ai](https://openrouter.ai/))
  - `GEMINI_API_KEY` ([aistudio.google.com](https://aistudio.google.com/))

---

## Local Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/sebx771/documentador-api.git
cd documentador-api
```

### Step 2: Create a Virtual Environment

**On Windows (PowerShell/CMD):**
```powershell
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux (Bash/Zsh):**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Upgrade pip

```bash
pip install --upgrade pip
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```
Make sure the Python interpreter used by the virtual environment is the active one.

**Core dependencies:**
- `Flask` 3.1.3 — Web framework
- `groq` 1.1.2, `openai` 3.7.0 (OpenRouter), `google-genai` 2.24.0 (Gemini) — AI provider SDKs
- `redis` 7.4.0 — Redis client (caching and rate limiting)
- `markdown-pdf` 1.13.1 — PDF export
- `python-docx` — Word export (`.docx`)

### Step 5: Configure Environment Variables

#### Option A: Create `.env` manually

```bash
# On Windows
type nul > .env

# On macOS/Linux
touch .env
```

#### Option B: Copy from template

```bash
cp .env.example .env
```

#### Edit `.env`

Use [`.env.example`](../.env.example) as reference. Startup (`api/config.py`) requires **at least one** AI provider key (`GROQ_API_KEY`, `OPENROUTER_API_KEY`, or `GEMINI_API_KEY`) plus `REDIS_URL`:

```env
GROQ_API_KEY="api_key_here"
OPENROUTER_API_KEY="api_key_here"
GEMINI_API_KEY="api_key_here"
REDIS_URL="redis://localhost:6379/0"
DEBUG="false"
```

**Where to get AI keys:**
- **Groq:** [console.groq.com](https://console.groq.com)
- **OpenRouter:** [openrouter.ai](https://openrouter.ai)
- **Google Gemini:** [aistudio.google.com](https://aistudio.google.com)

**How to get `REDIS_URL`:**

**Option 1: Local Redis**
```bash
# Install Redis
# Windows: https://github.com/microsoftarchive/redis/releases
# macOS: brew install redis
# Linux: sudo apt-get install redis-server

# Start Redis
redis-server

# Verify connection
redis-cli ping
# You should see: PONG

# Use in .env:
REDIS_URL=redis://localhost:6379/0
```

**Option 2: Cloud Redis (Recommended for production)**
- [Upstash](https://upstash.com/) (10,000 free commands/day)

### Step 6: Verify Installation

```bash
# Check Python
python --version
# Output: Python 3.12.x

# Check active venv
which python
# Output: /path/to/venv/bin/python (macOS/Linux)
# Or: path\to\venv\Scripts\python.exe (Windows)

# Check dependencies
pip list
```

### Step 7: Run the Application

```bash
# Option 1: Run directly
python -m api.main

# Option 2: With Flask CLI
flask --app api.main run --reload

# Expected output:
# WARNING in flask.app: This is a development server. Do not use it in production.
# Running on http://127.0.0.1:5000
# Press CTRL+C to quit
```

Open `http://localhost:5000` in your browser.

---

## Docker Setup

With Docker Desktop installed and a configured `.env` file, you can start the API along with local Redis for development:

```powershell
docker compose -f docker-compose-dev.yml up --build
```

The API will be available at `http://localhost:5000`. To stop the containers:

```powershell
docker compose -f docker-compose-dev.yml down
```

`docker-compose-dev.yml` starts the API alongside local Redis for development. For production, `docker-compose.yml` starts only the API (with Gunicorn on port `5000`) and reads `REDIS_URL` from `.env` or from hosting environment variables (for example, an Upstash `rediss://` URL):

```powershell
docker compose -f docker-compose.yml up -d --build
```

To stop the production stack:

```powershell
docker compose -f docker-compose.yml down
```

---

## Development Setup

### Install Development Tools

```bash
pip install -r requirements.txt
```

### Run Tests

The unit and integration test suite is located under `test/`:

```bash
python test/run_tests.py
```

### Set Up pre-commit Hooks (optional)

```bash
pip install pre-commit
pre-commit install
```

### Linting and Formatting

```bash
# Auto-formatting
black api/
```

---

## Deploying to Vercel (Production)

### Prerequisites

- GitHub repository
- [Vercel](https://vercel.com) account
- Environment variables ready

### Steps

> **Note on serverless limits:** Vercel enforces an HTTP body limit of ~4.5 MB and per-function execution timeouts. For ZIP uploads up to `15 MB` or long multi-round consolidations, deploy with Docker PaaS (`Dockerfile` or `docker-compose.yml`).

#### 1. Push Code to GitHub

```bash
git push origin main
```

#### 2. Import on Vercel

1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Connect your GitHub repository
4. Select `documentador-api`
5. Click "Import"

#### 3. Configure Environment Variables

In Vercel Dashboard → Settings → Environment Variables, configure `REDIS_URL` (e.g., Upstash `rediss://...`) and the AI keys you use (`GROQ_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`):

```env
GROQ_API_KEY=your_groq_key
OPENROUTER_API_KEY=your_openrouter_key
GEMINI_API_KEY=your_gemini_key
REDIS_URL=rediss://...
DEBUG=false
```

#### 4. Deploy

- Vercel will automatically detect `vercel.json`
- Run `pip install -r requirements.txt`
- Deploy the function

#### 5. Verify Deployment

```bash
curl https://<your-project>.vercel.app/
```

You should receive:
```json
{
  "message": "Welcome to EasyDocs API!",
  "version": "3.4.0",
  "endpoints": [...]
}
```

---

## Troubleshooting

### Error: `ModuleNotFoundError: No module named 'api'`

**Solution:**
```bash
# Make sure you are in the project root
cd /correct/path/to/documentador-api

# Verify venv is active
# Windows: (venv) should appear in the prompt
# macOS/Linux: (venv) should appear in the prompt

# Reinstall dependencies
pip install -r requirements.txt

# Run from root
python -m api.main
```

### Error: `ConnectionRefusedError: Redis connection failed`

**Solution:**
```bash
# 1. Verify Redis is running
redis-cli ping
# If not, start Redis:
redis-server

# 2. Check REDIS_URL in .env
# Should be: redis://localhost:6379/0

# 3. If using cloud Redis, check the URL
# E.g.: redis://xxxxx:xxxxx@xxxxx.upstash.io:xxxxx

# 4. Restart the application
python -m api.main
```

### Error: `[CONFIG ERROR] Debes configurar al menos GROQ_API_KEY, OPENROUTER_API_KEY o GEMINI_API_KEY`

**Solution:**
1. Verify that `.env` exists in the project root and has at least one valid key (`GROQ_API_KEY`, `OPENROUTER_API_KEY`, or `GEMINI_API_KEY`) without stray quotes or trailing spaces.
2. If a provider fails with `401`/`403`, regenerate the key in that provider's console.
3. Restart the application (`python -m api.main`).

### Error: `Port 5000 already in use`

**Solution:**
```bash
# Option 1: Use another port
python -m flask --app api.main run --port 5001

# Option 2: Kill the process using port 5000
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux:
lsof -i :5000
kill -9 <PID>
```

### Error: `Python version < 3.12`

**Solution:**
```bash
# Check current version
python --version

# Upgrade to Python 3.12+
# Windows: https://www.python.org/downloads/
# macOS: brew install python@3.12
# Linux: sudo apt-get install python3.12

# Use the specific version
python3.12 -m venv venv
```

---

## Installation Verification

Run this script to verify everything is set up properly:

```bash
#!/bin/bash
echo "✓ Verifying EasyDocs installation"

echo "1. Python version..."
python --version

echo "2. Dependencies..."
pip list | grep Flask
pip list | grep groq
pip list | grep redis

echo "3. Redis connection..."
redis-cli ping

echo "4. Environment variables..."
grep -E "^(GROQ|OPENROUTER|GEMINI)_API_KEY|^REDIS_URL" .env

echo "5. Folder structure..."
ls -la api/services/orchestrator/
ls -la api/services/ai/
ls -la api/export/
ls -la api/routes/

echo "✓ All set! You can run: python -m api.main"
```

---

## Next: API Documentation

Once installed, check:
- [README.en.md](../README.en.md) — Quick start and endpoint overview
- [ARCHITECTURE.en.md](ARCHITECTURE.en.md) — Detailed architecture (`v3.4.0`)
- `GET /` — Live metadata from the running API
