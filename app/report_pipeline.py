from pathlib import Path

from app.config import DEFAULT_PDF_NAME, RAW_DATA_DIR
from app.parser_pdf import extract_text_from_pdf
from app.text_cleaner import clean_text
from app.vector_store import get_or_create_vector_store, try_load_cached_store


class ReportNotFoundError(FileNotFoundError):
    pass


def resolve_report_pdf() -> Path:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    default_pdf = RAW_DATA_DIR / DEFAULT_PDF_NAME
    if default_pdf.exists():
        return default_pdf

    pdfs = sorted(RAW_DATA_DIR.glob("*.pdf"))
    if pdfs:
        return pdfs[0]

    raise ReportNotFoundError(
        f"Nenhum PDF encontrado em '{RAW_DATA_DIR}'. "
        f"Coloque o relatório em data/raw/{DEFAULT_PDF_NAME}."
    )


def file_fingerprint(pdf_path: Path) -> str:
    stat = pdf_path.stat()
    return f"{pdf_path.resolve()}:{stat.st_mtime_ns}:{stat.st_size}"


def prepare_vector_store(pdf_path: Path | None = None, *, force_reindex: bool = False):
    pdf_path = pdf_path or resolve_report_pdf()
    fingerprint = file_fingerprint(pdf_path)

    if not force_reindex:
        cached = try_load_cached_store(fingerprint)
        if cached is not None:
            return cached, pdf_path, fingerprint

    raw_text = extract_text_from_pdf(str(pdf_path))
    cleaned_text = clean_text(raw_text)
    vectordb = get_or_create_vector_store(cleaned_text, fingerprint)

    return vectordb, pdf_path, fingerprint
