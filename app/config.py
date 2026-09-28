import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
VECTORDB_DIR = PROJECT_ROOT / "data" / "vectordb"
DEFAULT_PDF_NAME = "genetic_report.pdf"

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
# k=3: ajuste baseado na evidência da Etapa 5 (groundedness/consistência)
RETRIEVAL_K = 3
MAX_CONTEXT_CHARS = 3500
LLM_NUM_PREDICT = 400

DASA_BLUE = "#003DA5"
DASA_BLUE_DARK = "#002855"
DASA_BLUE_LIGHT = "#E8F0FA"
DASA_ACCENT = "#0066CC"
