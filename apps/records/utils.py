import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import tempfile
import re

def extract_fields_from_document(file_path):
    text = ""

    if file_path.endswith('.pdf'):
        images = convert_from_path(file_path)
        for image in images:
            text += pytesseract.image_to_string(image)
    else:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)

    # Very simple field-value regex (you can improve it)
    fields = re.findall(r'([A-Z][A-Za-z\s]*):\s*(.*)', text)
    return fields