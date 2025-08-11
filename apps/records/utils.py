import re
from pathlib import Path
from collections import OrderedDict

# --- very small, regex‑based AcroForm parser -------------------------------

_FIELD_RX = re.compile(
    rb"""/T\s*\(\s*(?P<name>.*?)\s*\)      # field name
          .*?                              # ...anything in between...
          /V\s*(?:                         # field value (two common forms)
              \(\s*(?P<val_text>.*?)\s*\)  #   literal string  (/V (value))
            | /(?P<val_name>\w+)           #   name object      (/V /Yes)
          )""",
    re.DOTALL | re.VERBOSE,
)

def _decode_pdf_string(raw: bytes) -> str:
    """
    Extremely tiny subset of PDF literal‑string decoding:
    • unescapes \\(, \\), and octal sequences like \\040
    • returns Latin‑1 text (works for most simple forms)
    """
    def _unescape(m):
        seq = m.group(0)
        if seq.startswith(b"\\(") or seq.startswith(b"\\)"):
            return seq[1:2]                      # drop leading backslash
        if seq.startswith(b"\\"):                # octal escape
            try:
                return bytes([int(seq[1:], 8)])
            except ValueError:
                pass
        return seq                               # leave weird cases unchanged
    literal = re.sub(rb"\\[0-7]{1,3}|\\\(|\\\)", _unescape, raw)
    return literal.decode("latin1", errors="replace")

# --- public API -------------------------------------------------------------

def extract_fields_from_document(file_path):
    """
    Extract (name, value) pairs from an un‑encrypted, *uncompressed* PDF.

    Parameters
    ----------
    file_path : str | Path
        Path to a PDF containing AcroForm fields.

    Returns
    -------
    list[tuple[str, str]]
        List of (field_name, field_value) tuples.

    Raises
    ------
    ValueError
        If the file is not a PDF.
    """
    path = Path(file_path)
    if path.suffix.lower() != ".pdf":
        raise ValueError("Dependency‑free version handles PDF files only.")

    pdf_bytes = path.read_bytes()
    fields = OrderedDict()

    for m in _FIELD_RX.finditer(pdf_bytes):
        raw_name  = m.group("name")
        raw_value = m.group("val_text") or m.group("val_name") or b""
        name  = _decode_pdf_string(raw_name)
        value = _decode_pdf_string(raw_value)
        # keep the first occurrence to avoid duplicate widget hits
        fields.setdefault(name, value)

    return list(fields.items())