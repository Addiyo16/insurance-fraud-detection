from io import BytesIO


def _read_uploaded_file(uploaded_file):
    if uploaded_file is None:
        return b"", ""

    name = getattr(uploaded_file, "name", "") or ""
    try:
        position = uploaded_file.tell()
    except Exception:
        position = None

    try:
        data = uploaded_file.getvalue()
    except Exception:
        data = uploaded_file.read()
    finally:
        if position is not None:
            try:
                uploaded_file.seek(position)
            except Exception:
                pass

    return data or b"", name.lower()


def extract_text_from_file(uploaded_file):
    data, name = _read_uploaded_file(uploaded_file)
    if not data:
        return ""

    if name.endswith(".pdf"):
        return _extract_pdf_text(data)

    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore")

    return _extract_image_text(data)


def _extract_pdf_text(data):
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    except Exception:
        return ""


def _extract_image_text(data):
    try:
        import pytesseract
        from PIL import Image

        image = Image.open(BytesIO(data))
        return pytesseract.image_to_string(image)
    except Exception:
        return ""


def extract_documents_text(documents):
    chunks = []
    for key, uploaded_file in (documents or {}).items():
        if uploaded_file is None:
            continue
        if isinstance(uploaded_file, list):
            files = uploaded_file
        else:
            files = [uploaded_file]
        for file_item in files:
            text = extract_text_from_file(file_item)
            if text:
                chunks.append(f"\n--- {key} ---\n{text}")
    return "\n".join(chunks)
