import csv
import io
import json
from pathlib import Path

SUPPORTED_EXTENSIONS = [
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".py",
    ".js",
    ".ts",
    ".java",
    ".cpp",
    ".pdf",
    ".docx",
]


def _decode_text(raw_bytes):
    return raw_bytes.decode("utf-8", errors="ignore")


def _parse_csv(raw_bytes):
    text = _decode_text(raw_bytes)
    rows = csv.reader(io.StringIO(text))
    return "\n".join(" | ".join(cell.strip() for cell in row) for row in rows)


def _parse_json(raw_bytes):
    text = _decode_text(raw_bytes)
    try:
        parsed = json.loads(text)
        return json.dumps(parsed, indent=2)
    except Exception:
        return text


def _parse_pdf(raw_bytes):
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise RuntimeError("PDF support requires the optional 'pypdf' package.") from exc

    reader = PdfReader(io.BytesIO(raw_bytes))
    return "\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()


def _parse_docx(raw_bytes):
    try:
        from docx import Document
    except Exception as exc:
        raise RuntimeError("DOCX support requires the optional 'python-docx' package.") from exc

    document = Document(io.BytesIO(raw_bytes))
    return "\n".join(paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip())


def parse_document_bytes(filename, raw_bytes):
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise RuntimeError(f"Unsupported file type: {extension}")

    if extension == ".csv":
        return _parse_csv(raw_bytes), "csv"
    if extension == ".json":
        return _parse_json(raw_bytes), "json"
    if extension == ".pdf":
        return _parse_pdf(raw_bytes), "pdf"
    if extension == ".docx":
        return _parse_docx(raw_bytes), "docx"

    return _decode_text(raw_bytes), extension.lstrip(".") or "text"


def parse_document_file(path):
    file_path = Path(path)
    raw_bytes = file_path.read_bytes()
    return parse_document_bytes(file_path.name, raw_bytes)
