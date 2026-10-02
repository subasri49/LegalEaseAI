"""Central configuration. Values come from the .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview").strip()
GEMINI_FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash,gemini-2.0-flash").split(",")
    if m.strip()
]

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = Path(os.getenv("DB_PATH", DATA_DIR / "legalease.db"))

LOGO_PATH = BASE_DIR / "Image" / "Logo.png"            # for white backgrounds (DOCX / PDF)
WEB_LOGO_PATH = BASE_DIR / "Image" / "inverseLogo.png"  # for the dark Streamlit UI
FOOTER_TEXT = "LegalEase | AI-generated draft - have a qualified lawyer review before signing"
