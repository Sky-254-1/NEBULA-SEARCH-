"""Document text extraction for supported formats."""

import hashlib
from pathlib import Path

SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".pdf", ".html", ".htm", ".docx"}


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".txt", ".md", ".json", ".csv"):
        return path.read_text(encoding="utf-8", errors="replace")
    if ext in (".html", ".htm"):
        return _extract_html(path)
    if ext == ".pdf":
        return _extract_pdf(path)
    if ext == ".docx":
        return _extract_docx(path)
    raise ValueError(f"Unsupported file type: {ext}")


def _extract_html(path: Path) -> str:
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except ImportError:
        return path.read_text(encoding="utf-8", errors="replace")


def _extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts)
    except ImportError:
        raise ValueError("PDF support requires pypdf. Install with: pip install pypdf")


def _extract_docx(path: Path) -> str:
    try:
        from docx import Document

        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        raise ValueError("DOCX support requires python-docx. Install with: pip install python-docx")
