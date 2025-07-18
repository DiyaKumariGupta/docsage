import fitz  # PyMuPDF

def process_pdf(uploaded_file):
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])

    # Split into chunks (roughly ~500 chars each)
    sentences = text.split(". ")
    chunks = []
    chunk = ""
    for sentence in sentences:
        if len(chunk) + len(sentence) < 500:
            chunk += sentence + ". "
        else:
            chunks.append({"text": chunk.strip()})
            chunk = sentence + ". "
    if chunk:
        chunks.append({"text": chunk.strip()})
    return chunks
