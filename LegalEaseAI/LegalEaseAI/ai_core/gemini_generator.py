"""Gemini integration: builds a structured prompt and returns the generated legal text."""
import logging

from google import genai
from google.genai import types

import config

logger = logging.getLogger("legalease.gemini")


class GeminiConfigError(Exception):
    """Raised when the API key is missing."""


class GeminiGenerationError(Exception):
    """Raised when every configured model fails to produce a document."""


SYSTEM_INSTRUCTION = (
    "You are a senior legal drafting assistant. You draft clear, formal, well-structured "
    "legal documents using standard clauses. Output PLAIN TEXT only: no markdown symbols "
    "(no #, *, or backticks). Use numbered section headings such as '1. Services:' on their "
    "own line. Where facts are unknown, use square-bracket placeholders like [Address]. "
    "Never invent party names, amounts or dates that the user did not provide."
)


class GeminiDocumentGenerator:
    def __init__(self, model_name=None, api_key=None):
        self.api_key = (api_key or config.GEMINI_API_KEY).strip()
        if not self.api_key:
            raise GeminiConfigError(
                "GEMINI_API_KEY is missing. Copy .env.example to .env and add your key."
            )
        self.client = genai.Client(api_key=self.api_key)
        primary = model_name or config.GEMINI_MODEL
        self.models = [primary] + [m for m in config.GEMINI_FALLBACK_MODELS if m != primary]
        self.last_model_used = None

    @staticmethod
    def build_prompt(document_type, parties, terms, dates):
        term_list = [t.strip() for t in terms.replace("\n", ";").split(";") if t.strip()]
        terms_block = "\n".join(f"- {t}" for t in term_list) or "- (none provided)"
        return (
            f"Generate a comprehensive legal document titled '{document_type}'.\n"
            f"Involved parties: {parties}\n"
            f"Effective date: {dates}\n"
            f"Terms and conditions to include (each must appear as a clause):\n{terms_block}\n\n"
            "Requirements:\n"
            "- First line: the document title in capital letters.\n"
            "- Use a formal legal structure: preamble/recitals, definitions where useful, "
            "numbered sections with legal clauses, governing law, severability, entire agreement, "
            "and a signature block for every party.\n"
            "- Plain text only, no markdown."
        )

    def generate_document(self, document_type, parties, terms, dates):
        prompt = self.build_prompt(document_type, parties, terms, dates)
        last_error = None
        for model in self.models:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION, temperature=0.3
                    ),
                )
                text = (response.text or "").strip()
                if text:
                    self.last_model_used = model
                    return text
                last_error = RuntimeError(f"Model {model} returned an empty response")
            except Exception as exc:  # network / quota / unknown model ...
                logger.warning("Model %s failed: %s", model, exc)
                last_error = exc
                if "API key" in str(exc) or "API_KEY" in str(exc):
                    break  # a different model will not fix a bad key
        raise GeminiGenerationError(f"Gemini generation failed: {last_error}")
