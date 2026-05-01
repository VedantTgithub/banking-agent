import os
import pypdf

def extract_text_from_pdf(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ""

    text = ""
    try:
        reader = pypdf.PdfReader(file_path)
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        return ""

    return text.strip()


def extract_text_from_uploaded_file(uploaded_file) -> str:
    """
    Accepts a Streamlit UploadedFile object directly.
    No need to save to disk first.
    """
    text = ""
    try:
        reader = pypdf.PdfReader(uploaded_file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        return ""

    return text.strip()