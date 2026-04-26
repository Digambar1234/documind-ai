# DocuMind AI

RAG chatbot backend for company PDF documents using FastAPI, LangChain, Gemini, and ChromaDB.

## What It Does

1. Upload a PDF.
2. Extract text with `PyPDFLoader`.
3. Split text into chunks.
4. Create Gemini embeddings.
5. Store chunks in ChromaDB.
6. Ask questions against uploaded documents.
7. Return an answer with source chunks.

## Setup

Create a virtual environment from the `backend` folder:

```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Update `.env`:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
CHROMA_DB_PATH=./chroma_db
UPLOAD_DIR=./uploads
```

## Run locally

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## Test Flow

Upload a PDF:

```text
POST /api/documents/upload
```

Ask a question:

```text
POST /api/chat/ask
```

```json
{
  "question": "What is this document about?"
}
```

Example response:

```json
{
  "answer": "The leave policy allows...",
  "sources": [
    {
      "file_name": "HR_Policy.pdf",
      "page": 4,
      "chunk": "..."
    }
  ]
}
```
