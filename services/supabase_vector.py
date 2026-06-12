"""Operações vetoriais via RPC no Supabase"""
from services.supabase_client import get_supabase
from services.embeddings import get_embeddings
from typing import List, Dict, Any

def buscar_documentos_similares(query: str, k: int = 3) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    emb = get_embeddings()
    vec = emb.embed_query(query)
    res = supabase.rpc("buscar_documentos_similares", {"query_embedding": vec, "k_resultados": k}).execute()
    return res.data

def inserir_documento(titulo: str, conteudo: str, metadados: dict = None):
    supabase = get_supabase()
    emb = get_embeddings()
    vec = emb.embed_documents([conteudo])[0]
    supabase.table("documento_chunks").insert({
        "titulo": titulo, "conteudo": conteudo, "metadata": metadados or {}, "embedding": vec
    }).execute()

def buscar_memoria_similar(user_id: int, query: str, k: int = 3) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    emb = get_embeddings()
    vec = emb.embed_query(query)
    res = supabase.rpc("buscar_memoria_similar", {
        "p_utilizador_id": user_id, "p_query_embedding": vec, "p_k_resultados": k
    }).execute()
    return res.data

def guardar_memoria(user_id: int, conteudo: str):
    supabase = get_supabase()
    emb = get_embeddings()
    vec = emb.embed_documents([conteudo])[0]
    supabase.table("memoria_usuario").insert({
        "utilizador_id": user_id, "conteudo": conteudo, "embedding": vec
    }).execute()