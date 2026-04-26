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

    response = llm.invoke(prompt)

    sources = [
        {
            "file_name": doc.metadata.get("file_name", "Unknown"),
            "page": _page_number(doc.metadata.get("page")),
            "chunk": doc.page_content,
        }
        for doc in relevant_docs
    ]

    return {
        "answer": response.content,
        "sources": sources,
    }


def _page_number(raw_page):
    if isinstance(raw_page, int):
        return raw_page + 1
    return raw_page if raw_page is not None else "N/A"


def _has_google_api_key() -> bool:
    return bool(GOOGLE_API_KEY and not GOOGLE_API_KEY.startswith("your_"))
