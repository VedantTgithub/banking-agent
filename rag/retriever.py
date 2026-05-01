"""
rag/retriever.py
Sets up the HuggingFace embeddings and Chroma retriever.
Call get_retriever() to get a LangChain retriever ready for querying.
"""

import os
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_store")

# ── Embedding model ────────────────────────────────────────────────────────────
EMBED_MODEL = "intfloat/e5-base-v2"


def get_embeddings() -> HuggingFaceEmbeddings:
    """Return HuggingFace embeddings (cached after first call)."""
    return HuggingFaceEmbeddings(
        model_name=EMBED_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_retriever(k: int = 5):
    """
    Load Chroma vector store from disk and return a retriever.

    Args:
        k: number of chunks to return per query (default 5)

    Returns:
        LangChain retriever object ready for .invoke() calls.

    Raises:
        FileNotFoundError: if the Chroma store hasn't been built yet.
                           Run rag/ingest.py first.
    """
    if not os.path.exists(CHROMA_DIR):
        raise FileNotFoundError(
            f"Chroma store not found at '{CHROMA_DIR}'. "
            "Please run `python rag/ingest.py` first to ingest your PDFs."
        )

    embeddings = get_embeddings()
    vectordb   = Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )
    return vectordb.as_retriever(search_kwargs={"k": k})