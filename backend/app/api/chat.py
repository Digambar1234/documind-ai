from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest
from app.services.rag_service import generate_answer

router = APIRouter()


@router.post("/ask")
def ask_question(request: ChatRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        return generate_answer(request.question)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer: {exc}",
        ) from exc
