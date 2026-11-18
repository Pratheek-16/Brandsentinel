"""Secure ingestion utilities for BrandSentinel.
Supports plain text, Markdown, DOCX, PDF, and image uploads.
All extractors work deterministically and handle errors cleanly without exposing local filesystem paths.
"""

import io
import os
import re
import uuid
from typing import Tuple, Optional
from PIL import Image

import docx
import pdfplumber

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

MAX_IMAGE_DIMENSION = 8192  # Protection against decompression bombs

def sanitize_filename(filename: str) -> str:
    """Strip dangerous directory traversal characters, null bytes, and non-whitelisted characters."""
    clean = os.path.basename(filename)
    clean = re.sub(r"[^\w\.\-\_]", "_", clean)
    if not clean or clean.startswith("."):
        clean = f"document_{clean}"
    return clean[:128]

def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from a DOCX file given its bytes."""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text]
        return "\n\n".join(paragraphs)
    except Exception as e:
        raise ValueError(f"Could not parse DOCX document: {str(e)}")

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from each page of a PDF using pdfplumber."""
    try:
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            if not pdf.pages:
                return ""
            for idx, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())
        return "\n\n".join(text_parts)
    except Exception as e:
        raise ValueError(f"Could not parse PDF document: {str(e)}")

def extract_text_from_image(file_bytes: bytes) -> str:
    """Run OCR on an image using pytesseract if available.
    Degrades gracefully if Tesseract binary is not installed on host.
    """
    try:
        image = Image.open(io.BytesIO(file_bytes))
        width, height = image.size
        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            raise ValueError(f"Image dimensions ({width}x{height}) exceed maximum allowed limit ({MAX_IMAGE_DIMENSION}px).")

        if HAS_TESSERACT:
            try:
                return pytesseract.image_to_string(image).strip()
            except Exception:
                return ""
        return ""
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Invalid image format: {str(e)}")

def ingest_file(file_bytes: bytes, file_ext: str) -> Tuple[str, str]:
    """Dispatch to the appropriate extractor based on extension.
    Returns a tuple (extracted_text, detected_type).
    """
    ext = file_ext.lower().strip()
    if ext in [".txt", ".md"]:
        try:
            return file_bytes.decode("utf-8"), "text"
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="ignore"), "text"

    if ext == ".docx":
        return extract_text_from_docx(file_bytes), "docx"

    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes), "pdf"

    if ext in [".png", ".jpg", ".jpeg"]:
        return extract_text_from_image(file_bytes), "image"

    raise ValueError(f"Unsupported file format: '{ext}'. Allowed: .txt, .md, .docx, .pdf, .png, .jpg, .jpeg")
