"""
rag/ingest.py
Ingests all PDFs from rag/docs/ into a Chroma vector store.

Run once (or whenever you add/update documents):
    python rag/ingest.py

Supports:
  - rbi_master_circular_loans.pdf
  - rbi_kyc_guidelines.pdf
  - rbi_priority_sector_lending.pdf
  - basel3_capital_framework.pdf
  - internal_credit_policy.pdf
  - Any other PDF you drop into rag/docs/
"""

import os
import sys

# Allow running from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from rag.retriever import get_embeddings, CHROMA_DIR

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")

# ── Splitter config ────────────────────────────────────────────────────────────
CHUNK_SIZE    = 1000
CHUNK_OVERLAP = 200


def ingest_pdfs() -> int:
    """
    Loads all PDFs from DOCS_DIR, splits them into chunks,
    and stores them in Chroma. Returns the total number of chunks ingested.
    """
    if not os.path.exists(DOCS_DIR):
        print(f"[Ingest] ERROR: docs directory not found at '{DOCS_DIR}'")
        sys.exit(1)

    pdf_files = [f for f in os.listdir(DOCS_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print(f"[Ingest] No PDF files found in '{DOCS_DIR}'. "
              "Download RBI PDFs from rbi.org.in and place them there.")
        sys.exit(1)

    print(f"[Ingest] Found {len(pdf_files)} PDF(s): {pdf_files}")

    all_docs = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    for pdf_name in pdf_files:
        pdf_path = os.path.join(DOCS_DIR, pdf_name)
        print(f"[Ingest] Loading: {pdf_name}")
        try:
            loader = PyPDFLoader(pdf_path)
            pages  = loader.load()

            # Tag each chunk with source metadata
            doc_type = _infer_doc_type(pdf_name)
            for page in pages:
                page.metadata["source"]   = pdf_name
                page.metadata["doc_type"] = doc_type

            chunks = splitter.split_documents(pages)
            all_docs.extend(chunks)
            print(f"[Ingest]   → {len(pages)} pages, {len(chunks)} chunks")

        except Exception as e:
            print(f"[Ingest] WARNING: Could not load '{pdf_name}': {e}")

    if not all_docs:
        print("[Ingest] No documents could be loaded. Aborting.")
        sys.exit(1)

    print(f"\n[Ingest] Total chunks to store: {len(all_docs)}")
    print(f"[Ingest] Building Chroma store at: {CHROMA_DIR}")

    embeddings = get_embeddings()
    Chroma.from_documents(
        documents=all_docs,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
    )

    print(f"[Ingest] ✅ Done. {len(all_docs)} chunks stored in Chroma.")
    return len(all_docs)


def _infer_doc_type(filename: str) -> str:
    """Maps filename to a human-readable document type tag."""
    name = filename.lower()
    if "kyc"            in name: return "kyc_guidelines"
    if "priority"       in name: return "priority_sector"
    if "master"         in name: return "master_circular"
    if "basel"          in name: return "capital_framework"
    if "internal"       in name: return "internal_policy"
    if "credit_policy"  in name: return "internal_policy"
    return "general_policy"


if __name__ == "__main__":
    ingest_pdfs()