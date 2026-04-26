import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
CHROMA_DB_PATH = str((BASE_DIR / os.getenv("CHROMA_DB_PATH", "./chroma_db")).resolve())
UPLOAD_DIR = str((BASE_DIR / os.getenv("UPLOAD_DIR", "./uploads")).resolve())
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./documind.db")
