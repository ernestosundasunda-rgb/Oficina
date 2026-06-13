"""Modelo de embeddings all-MiniLM-L6-v2 (384 dimensões) via Hugging Face Inference API."""
import os
from langchain_huggingface import HuggingFaceEndpointEmbeddings

_embeddings = None

def get_embeddings() -> HuggingFaceEndpointEmbeddings:
    """Retorna a instância singleton do modelo de embeddings."""
    global _embeddings
    if _embeddings is None:
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            raise ValueError("HF_TOKEN não configurado no ambiente.")
        print("🧠 A ligar à Hugging Face Inference API (all-MiniLM-L6-v2)...")
        _embeddings = HuggingFaceEndpointEmbeddings(
            model="https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2",
            huggingfacehub_api_token=hf_token,
            task="feature-extraction"
        )
        print("✅ Modelo pronto.")
    return _embeddings