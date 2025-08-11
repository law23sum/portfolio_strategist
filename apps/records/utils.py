import re
from pathlib import Path
from typing import List, Tuple

from PyPDF2 import PdfReader

try:
    import pytesseract
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    pytesseract = None  # type: ignore[assignment]


def extract_fields_from_document(file_path: str) -> List[Tuple[str, str]]:
    """Extract key/value pairs from a document.

    For PDF files we use :mod:`PyPDF2` to pull the text directly. For other
    image formats we fall back to ``pytesseract`` if available.
    """
    path = Path(file_path)
    text = ""

    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        for page in reader.pages:
            text += page.extract_text() or ""
    elif Image and pytesseract:
        image = Image.open(path)
        text = pytesseract.image_to_string(image)

    # Simple ``Field: Value`` matcher; tweak as needed for your documents.
    return re.findall(r"([A-Za-z][A-Za-z\s]*):\s*(.*)", text)