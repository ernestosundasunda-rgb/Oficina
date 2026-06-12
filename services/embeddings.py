"""Modelo de embeddings all-MiniLM-L6-v2 (384 dimensões)"""
from langchain_huggingface import HuggingFaceEmbeddings

_embeddings = None

def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        print("🧠 Carregando modelo all-MiniLM-L6-v2 (384d)...")
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        print("✅ Modelo pronto.")
    return _embeddings