from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

try:
    import pdfplumber  # type: ignore
except ImportError:  # pragma: no cover
    pdfplumber = None

from pypdf import PdfReader

from backend.data.vectorstore import VectorStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DOCS_FOLDER = PROJECT_ROOT / "data" / "docs"


def infer_metadata(filename: str) -> Dict[str, Any]:
    name = filename.lower()
    is_deprecated = "deprecated" in name
    is_customer_agreement = "agreement" in name
    is_historical = "known_issues" in name or "historical" in name

    customer_name = None
    if is_customer_agreement:
        match = re.search(r"\d+_([a-z_]+?)_(?:enterprise_)?agreement", name)
        if match:
            customer_name = match.group(1).replace("_", " ").title()

    if is_customer_agreement:
        doc_type = "agreement"
        priority = 1
    elif is_historical:
        doc_type = "historical_ticket_resolution"
        priority = 6
    elif "policy" in name or "sop" in name or "guide" in name:
        doc_type = "policy"
        priority = 5 if is_deprecated else 2
    else:
        doc_type = "reference"
        priority = 3

    return {
        "source_file": filename,
        "doc_type": doc_type,
        "is_deprecated": is_deprecated,
        "is_customer_agreement": is_customer_agreement,
        "customer_name": customer_name,
        "chunk_index": 0,
        "priority": priority,
    }


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    words = text.split()
    if not words:
        return []

    chunks: List[str] = []
    start = 0
    while start < len(words):
        end = min(len(words), start + chunk_size)
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = max(0, end - overlap)
    return chunks


def extract_text_from_pdf(pdf_path: str) -> str:
    if pdfplumber is not None:
        with pdfplumber.open(pdf_path) as pdf:  # pragma: no branch
            text = "\n\n".join(filter(None, (page.extract_text() for page in pdf.pages)))
            if text.strip():
                return text

    reader = PdfReader(pdf_path)
    return "\n\n".join(filter(None, ((page.extract_text() or "") for page in reader.pages)))


def ingest_documents(docs_folder: str | Path = DEFAULT_DOCS_FOLDER, reset: bool = False) -> int:
    docs_path = Path(docs_folder)
    if not docs_path.is_absolute():
        docs_path = PROJECT_ROOT / docs_path

    if not docs_path.exists():
        raise FileNotFoundError(f"Documents folder not found: {docs_path}")

    vector_store = VectorStore()
    if reset:
        vector_store.clear()

    all_chunks: List[Dict[str, Any]] = []

    for pdf_file in sorted(docs_path.glob("*.pdf")):
        text = extract_text_from_pdf(str(pdf_file)).strip()
        if not text:
            continue

        metadata = infer_metadata(pdf_file.name)
        for index, chunk in enumerate(chunk_text(text)):
            all_chunks.append(
                {
                    "text": chunk,
                    "metadata": {
                        **metadata,
                        "chunk_index": index,
                    },
                }
            )

    if all_chunks:
        vector_store.ingest(all_chunks)

    return len(all_chunks)


if __name__ == "__main__":
    print(ingest_documents(reset=True))
