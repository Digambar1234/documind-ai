import os
import shutil

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import UPLOAD_DIR
from app.services.document_service import process_pdf_document

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported currently.",
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_name = os.path.basename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = process_pdf_document(file_path=file_path, file_name=file_name)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Document upload succeeded, but indexing failed: {exc}",
        ) from exc

    return {
        "message": "Document uploaded and indexed successfully",
        "file_name": file_name,
        "chunks_created": result["chunks_created"],
    }


@router.get("/")
def list_documents():
    return {"documents": []}
