from fastapi import HTTPException
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import CHROMA_DB_PATH, GEMINI_EMBEDDING_MODEL, GOOGLE_API_KEY


def get_embedding_model():
    if not _has_google_api_key():
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_API_KEY is missing. Add it to backend/.env.",
        )

    return GoogleGenerativeAIEmbeddings(
        model=GEMINI_EMBEDDING_MODEL,
        google_api_key=GOOGLE_API_KEY,
    )


def get_vector_db():
    return Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=get_embedding_model(),
        collection_name="company_documents",
    )


def add_documents_to_vector_db(documents):
    vector_db = get_vector_db()
    vector_db.add_documents(documents)
    return True


def reset_vector_db():
    vector_db = get_vector_db()
    try:
        vector_db.delete_collection()
    except Exception:
        return False
    return True


def search_similar_documents(query: str, k: int = 4):
    vector_db = get_vector_db()
    return vector_db.similarity_search(query, k=k)


def _has_google_api_key() -> bool:
    return bool(GOOGLE_API_KEY and not GOOGLE_API_KEY.startswith("your_"))
