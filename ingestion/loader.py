"""
PDF Loader - Improved Text Extraction

- Better text extraction
- Handles tables properly
- Cleans up whitespace
"""

from pathlib import Path
from llama_index.core import Document
from typing import List
import re


def load_pdf(path: str) -> List[Document]:
    """
    Load PDF with improved text extraction.
    """
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    
    # Try pdfplumber first (better for tables)
    try:
        return _load_with_pdfplumber(path)
    except ImportError:
        print("[Loader] pdfplumber not available")
    except Exception as e:
        print(f"[Loader] pdfplumber failed: {e}")
    
    # Try PyMuPDF
    try:
        return _load_with_pymupdf(path)
    except ImportError:
        print("[Loader] PyMuPDF not available")
    except Exception as e:
        print(f"[Loader] PyMuPDF failed: {e}")
    
    # Fallback to pypdf
    try:
        return _load_with_pypdf(path)
    except Exception as e:
        print(f"[Loader] pypdf failed: {e}")
    
    raise RuntimeError("No PDF backend available")


def _clean_text(text: str) -> str:
    """Clean extracted text."""
    if not text:
        return ""
    
    # Fix common PDF extraction issues
    
    # Add space after numbers followed directly by text
    text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)
    
    # Add space before numbers preceded directly by text
    text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)
    
    # Fix run-together words (camelCase in extracted text)
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Fix multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove lines that are just numbers (page numbers, table indices)
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Keep line if it's not just a number or very short
        if stripped and not (stripped.isdigit() and len(stripped) < 4):
            cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    return text.strip()


def _load_with_pdfplumber(path: Path) -> List[Document]:
    """Load using pdfplumber - best for tables."""
    import pdfplumber
    
    print("[Loader] Using pdfplumber...")
    
    text_parts = []
    
    with pdfplumber.open(str(path)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_text = ""
            
            # Extract tables first
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    if table:
                        # Convert table to readable format
                        for row in table:
                            if row:
                                # Clean None values and join
                                row_text = " | ".join(str(cell) if cell else "" for cell in row)
                                page_text += row_text + "\n"
                        page_text += "\n"
            
            # Extract remaining text
            text = page.extract_text()
            if text:
                page_text += text
            
            if page_text.strip():
                cleaned = _clean_text(page_text)
                text_parts.append(f"[Page {page_num + 1}]\n{cleaned}")
        
        page_count = len(pdf.pages)
    
    full_text = "\n\n".join(text_parts)
    print(f"[Loader] ✅ Loaded {page_count} pages with pdfplumber")
    
    return [Document(text=full_text, metadata={"source": str(path), "pages": page_count})]


def _load_with_pymupdf(path: Path) -> List[Document]:
    """Load using PyMuPDF."""
    import fitz
    
    print("[Loader] Using PyMuPDF...")
    
    doc = fitz.open(str(path))
    text_parts = []
    
    for page_num, page in enumerate(doc):
        # Extract text with better formatting
        text = page.get_text("text")
        if text.strip():
            cleaned = _clean_text(text)
            text_parts.append(f"[Page {page_num + 1}]\n{cleaned}")
    
    page_count = len(doc)
    doc.close()
    
    full_text = "\n\n".join(text_parts)
    print(f"[Loader] ✅ Loaded {page_count} pages with PyMuPDF")
    
    return [Document(text=full_text, metadata={"source": str(path), "pages": page_count})]


def _load_with_pypdf(path: Path) -> List[Document]:
    """Load using pypdf."""
    from pypdf import PdfReader
    
    print("[Loader] Using pypdf...")
    
    reader = PdfReader(str(path))
    text_parts = []
    
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            cleaned = _clean_text(text)
            text_parts.append(f"[Page {page_num + 1}]\n{cleaned}")
    
    full_text = "\n\n".join(text_parts)
    print(f"[Loader] ✅ Loaded {len(reader.pages)} pages with pypdf")
    
    return [Document(text=full_text, metadata={"source": str(path), "pages": len(reader.pages)})]