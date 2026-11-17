# BrandSentinel

**BrandSentinel** is a full‑stack brand‑governance platform that reviews draft content (text, DOCX, images, PDFs) against a versioned knowledge‑base of approved rules, facts, terms, claims and assets. It provides grounded, cited findings, intent‑preserving rewrite suggestions, visual and accessibility checks, and a role‑based workflow with immutable audit trails.

---

## Quick start (Windows)

### Prerequisites
- **Python 3.11+** (download from python.org)
- **Node.js 20+** (download from nodejs.org)
- **Git** (installed with Windows optional features)
- **Tesseract OCR** (optional for image/PDF text extraction). Install from https://github.com/UB-Mannheim/tesseract/wiki. Add the `tesseract.exe` directory to your `PATH`.

### 1. Clone / open the repo (already local)
```powershell
cd C:\Users\sreep\Desktop\psp\codezen-project\brandsentinel
```

### 2. Set up a Python virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # PowerShell
# or: .\.venv\Scripts\activate   # cmd.exe
```

### 3. Install backend dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run database migrations (SQLite fallback)
```powershell
alembic upgrade head
```

### 5. Start the FastAPI backend
```powershell
uvicorn backend.app.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

### 6. Set up the frontend
```powershell
cd frontend
npm install
npm run dev
```
The React app will be served at `http://localhost:5173` and proxies API calls to the backend.

### 7. Environment configuration
Copy the example file and edit if you have a Gemini key:
```powershell
copy .env.example .env
# edit .env to add GEMINI_API_KEY and GEMINI_PROJECT_ID if available
```
If `GEMINI_API_KEY` is left empty the app automatically falls back to the **MockProvider** (no external calls).

---

## Demo data
When the environment variable `SEED_DEMO=true` is set, the app creates three workspaces (NovaFit, Lumen Bank, Aster University) each with demo accounts:
- `admin@<brand>.local` – **Admin**
- `manager@<brand>.local` – **Manager**
- `reviewer@<brand>.local` – **Authorised Reviewer**
- `creator1@<brand>.local` – **Creator**
- `creator2@<brand>.local` – **Creator**
All passwords are `Demo@12345`.

---

## Running the test suite
```powershell
pytest
```
The suite runs against SQLite by default. To test against PostgreSQL:
```powershell
set SEED_DEMO=true
set TEST_DB=postgres
docker compose --profile postgres up -d
pytest -m postgres
```

---

## License
MIT – see `LICENSE`.
