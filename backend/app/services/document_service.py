from pathlib import Path

from fastapi import HTTPException
from google import genai
from google.genai import types
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import GEMINI_CHAT_MODEL, GOOGLE_API_KEY
from app.services.vector_service import add_documents_to_vector_db


def process_pdf_document(file_path: str, file_name: str):
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    for document in documents:
        document.metadata["file_name"] = file_name

    if not _has_extractable_text(documents):
        documents = _extract_text_with_gemini(file_path=file_path, file_name=file_name)

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = text_splitter.split_documents(documents)

    chunks = [chunk for chunk in chunks if chunk.page_content.strip()]
    if not chunks:
        raise HTTPException(
            status_code=400,
            detail=(
                "No readable text could be extracted from this PDF. "
                "Try a text-based PDF or a clearer scanned document."
            ),
        )

    add_documents_to_vector_db(chunks)

    return {
        "chunks_created": len(chunks),
        "extraction_method": documents[0].metadata.get("extraction_method", "pypdf"),
    }


def _has_extractable_text(documents) -> bool:
    return any((document.page_content or "").strip() for document in documents)


def _extract_text_with_gemini(file_path: str, file_name: str) -> list[Document]:
    if not _has_google_api_key():
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_API_KEY is missing. Add it to backend/.env.",
        )

    path = Path(file_path)
    prompt = """
Extract all readable text from this PDF.

Return plain text only.
Preserve important labels, dates, names, amounts, addresses, and table-like rows.
Do not summarize.
If a page has no readable text, write: [No readable text on this page]
"""

    client = genai.Client(api_key=GOOGLE_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_CHAT_MODEL,
        contents=[
            types.Part.from_bytes(
                data=path.read_bytes(),
                mime_type="application/pdf",
            ),
            prompt,
        ],
    )

    extracted_text = (response.text or "").strip()
    if not extracted_text:
        raise HTTPException(
            status_code=400,
            detail=(
                "This PDF appears to be scanned or image-only, and Gemini OCR "
                "could not extract readable text from it."
            ),
        )

    return [
        Document(
            page_content=extracted_text,
            metadata={
                "file_name": file_name,
                "page": "OCR",
                "source": str(path),
                "extraction_method": "gemini_ocr",
            },
        )
    ]


def _has_google_api_key() -> bool:
    return bool(GOOGLE_API_KEY and not GOOGLE_API_KEY.startswith("your_"))
