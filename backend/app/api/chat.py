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
        if _is_quota_error(exc):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini is temporarily rate-limited. Please try again in about a minute."
                ),
            ) from exc

        raise HTTPException(
            status_code=500,
            detail="Failed to generate answer. Please try again.",
        ) from exc


def _is_quota_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "429" in message
        or "resource_exhausted" in message
        or "quota" in message
        or "rate limit" in message
    )
