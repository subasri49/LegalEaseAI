from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ai_core.gemini_generator import (
    GeminiConfigError,
    GeminiDocumentGenerator,
    GeminiGenerationError,
)
from legalEaseAPI import database

router = APIRouter()
_generator = None  # created lazily so the server still starts without an API key


def get_generator() -> GeminiDocumentGenerator:
    global _generator
    if _generator is None:
        _generator = GeminiDocumentGenerator()
    return _generator


class DocumentRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    document_type: str = Field(..., min_length=2, max_length=200)
    parties: str = Field(..., min_length=2, max_length=2000)
    terms: str = Field(..., min_length=2, max_length=5000)
    dates: str = Field(..., min_length=2, max_length=100)


class DocumentUpdate(BaseModel):
    content: str = Field(..., min_length=1)


@router.post("/generate")
def generate_legal_document(request: DocumentRequest):
    try:
        generator = get_generator()
    except GeminiConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    try:
        response = generator.generate_document(
            request.document_type, request.parties, request.terms, request.dates
        )
    except GeminiGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    doc_id = database.save_document(
        request.document_type, request.parties, request.terms, request.dates, response
    )
    return {"id": doc_id, "document": response, "model": generator.last_model_used}


@router.get("/history")
def history(limit: int = 20):
    return {"items": database.list_documents(limit=min(max(limit, 1), 100))}


@router.get("/history/{doc_id}")
def history_item(doc_id: int):
    item = database.get_document(doc_id)
    if not item:
        raise HTTPException(status_code=404, detail="Document not found")
    return item


@router.put("/history/{doc_id}")
def update_item(doc_id: int, body: DocumentUpdate):
    if not database.update_document(doc_id, body.content):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"id": doc_id, "updated": True}


@router.delete("/history/{doc_id}")
def delete_item(doc_id: int):
    if not database.delete_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"id": doc_id, "deleted": True}
