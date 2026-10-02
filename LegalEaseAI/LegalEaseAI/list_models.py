"""Run `python list_models.py` to see which Gemini models YOUR key can use."""
from google import genai

import config

if not config.GEMINI_API_KEY:
    raise SystemExit("GEMINI_API_KEY is missing in .env")

client = genai.Client(api_key=config.GEMINI_API_KEY)
for m in client.models.list():
    print(m.name)
