# LegalEase - AI Legal Document Generator

Streamlit (frontend) + FastAPI (backend) + Google Gemini (AI) + SQLite (history).
Exports documents as .txt, .docx and .pdf.

## Setup (VS Code)
1. Install Python 3.10+ and VS Code (with the Python extension).
2. Open this folder: File > Open Folder > `LegalEase`. Open a terminal: Terminal > New Terminal.
3. Create and activate a virtual environment
   - Windows PowerShell: `python -m venv venv` then `venv\Scripts\activate`
     (if blocked: `Set-ExecutionPolicy -Scope Process Bypass`)
   - macOS/Linux: `python3 -m venv venv && source venv/bin/activate`
4. `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and paste your key from https://aistudio.google.com/apikey
6. (Optional) `python setup_assets.py` regenerates the placeholder logos in `Image/`.

## Run
Two terminals (both with the venv activated, in the project root):

    uvicorn legalEaseAPI.main:app --reload --port 8000
    streamlit run frontend/app.py

Or one command: `run.bat` (Windows) / `./run.sh` (macOS/Linux/Git-Bash).
Frontend: http://localhost:8501 | API docs: http://localhost:8000/docs

## Test
- Automated: `pytest -v` (AI is mocked, no key needed)
- Manual: fill the form (e.g. Freelance Work Contract / Jane Doe (Service Provider), TechNova Inc. (Client) /
  `Work delivered by May 15, 2025; Payment within 7 days of invoice; Client owns IP` / April 15, 2025),
  click Generate, preview, Edit, then download TXT/DOCX/PDF.

## Troubleshooting
- 404 / "model not found": run `python list_models.py`, then set `GEMINI_MODEL` in `.env`.
- 429 quota error: wait a minute, or use a Flash model.
- "Cannot reach the backend": start uvicorn first; check `API_URL` in `.env`.
- PDF shows `?` for non-Latin names: built-in PDF fonts are Latin-1 only (DOCX/TXT are unaffected).
