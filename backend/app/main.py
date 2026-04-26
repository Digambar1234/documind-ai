from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="DocuMind AI",
    description="RAG Chatbot for Company Documents using FastAPI, LangChain, Gemini and ChromaDB",
    version="1.0.0",
)

app.include_router(documents_router, prefix="/api/documents", tags=["Documents"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])

if FRONTEND_DIR.exists():
    app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="ui")


@app.get("/")
def root():
    return {
        "message": "DocuMind AI backend is running",
        "docs": "/docs",
    }
