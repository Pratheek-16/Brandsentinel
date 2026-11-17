"""Ingestion utilities for BrandSentinel.
Supports plain text, DOCX, PDF and image uploads.
All functions are deterministic and work offline – no external services.
"""

import io
import pathlib
from typing import Tuple

import docx
import pdfplumber
import pytesseract
from PIL import Image

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from a DOCX file given its bytes.
    Returns concatenated paragraph texts.
    """
    doc = docx.Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from each page of a PDF using pdfplumber.
    Returns combined page texts.
    """
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages)

def extract_text_from_image(file_bytes: bytes) -> str:
    """Run OCR on an image using pytesseract.
    Returns the recognized text.
    If Tesseract is not installed, returns an empty string.
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(image)
    except Exception:
        return ""

def ingest_file(file_bytes: bytes, content_type: str) -> Tuple[str, str]:
    """Dispatch to the appropriate extractor based on MIME type.
    Returns a tuple (extracted_text, detected_type).
    Supported content_type values: 'text', 'docx', 'pdf', 'image'.
    """
    if content_type == "text":
        return file_bytes.decode(errors="ignore"), "text"
    if content_type == "docx":
        return extract_text_from_docx(file_bytes), "docx"
    if content_type == "pdf":
        return extract_text_from_pdf(file_bytes), "pdf"
    if content_type == "image":
        return extract_text_from_image(file_bytes), "image"
    # fallback – treat as raw text
    return file_bytes.decode(errors="ignore"), "text"
