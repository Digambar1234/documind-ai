from fastapi import HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import GEMINI_CHAT_MODEL, GOOGLE_API_KEY
from app.services.vector_service import search_similar_documents


def generate_answer(question: str):
    if not _has_google_api_key():
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_API_KEY is missing. Add it to backend/.env.",
        )

    relevant_docs = search_similar_documents(question, k=4)

    if not relevant_docs:
        return {
            "answer": "I could not find relevant information in the uploaded documents.",
            "sources": [],
        }

    context = "\n\n".join(
        [
            (
                f"Source: {doc.metadata.get('file_name', 'Unknown')}, "
                f"Page: {_page_number(doc.metadata.get('page'))}\n"
                f"{doc.page_content}"
            )
            for doc in relevant_docs
        ]
    )

    prompt = f"""
You are a helpful AI assistant for company documents.

Answer the user's question using only the context below.
If the answer is not present in the context, say:
"I could not find this information in the uploaded documents."

Context:
{context}

Question:
{question}

Answer:
"""

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_CHAT_MODEL,
        google_api_key=GOOGLE_API_KEY,
        temperature=0.2,
    )

    sources = _format_sources(relevant_docs)

    try:
        response = llm.invoke(prompt)
    except Exception as exc:
        if _is_quota_error(exc):
            return {
                "answer": _quota_fallback_answer(relevant_docs),
                "sources": sources,
            }
        raise

    return {
        "answer": response.content,
        "sources": sources,
    }


def _is_quota_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return (
        "429" in message
        or "resource_exhausted" in message
        or "quota" in message
        or "rate limit" in message
    )


def _quota_fallback_answer(documents) -> str:
    snippets = []

    for doc in documents[:3]:
        file_name = doc.metadata.get("file_name", "the uploaded document")
        page = _page_number(doc.metadata.get("page"))
        text = " ".join((doc.page_content or "").split())
        if not text:
            continue

        snippets.append(f"- {file_name}, page {page}: {_truncate(text, 360)}")

    if not snippets:
        return (
            "Gemini is temporarily rate-limited, and I could not extract a fallback "
            "answer from the uploaded document. Please try again in about a minute."
        )

    return (
        "Gemini is temporarily rate-limited, so I cannot generate a polished answer "
        "right now. Here are the most relevant parts I found in the uploaded document:\n\n"
        + "\n".join(snippets)
        + "\n\nPlease try again in about a minute for a full AI-written answer."
    )


def _format_sources(documents):
    sources = []
    seen = set()

    for doc in documents:
        file_name = doc.metadata.get("file_name", "Unknown")
        page = _page_number(doc.metadata.get("page"))
        preview = " ".join((doc.page_content or "").split())
        key = (file_name, page, preview[:180])

        if key in seen:
            continue

        seen.add(key)
        sources.append(
            {
                "file_name": file_name,
                "page": page,
                "content_preview": _truncate(preview, 260),
            }
        )

    return sources


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return f"{text[:max_length].rstrip()}..."


def _page_number(raw_page):
    if isinstance(raw_page, int):
        return raw_page + 1
    return raw_page if raw_page is not None else "N/A"


def _has_google_api_key() -> bool:
    return bool(GOOGLE_API_KEY and not GOOGLE_API_KEY.startswith("your_"))
