import os
from fastapi import Header, HTTPException
from services.supabase_db import buscar_utilizador, buscar_veiculos_cliente
from services.groq_client import get_groq
from services.embeddings import get_embeddings
from graph import criar_grafo

def verify_secret_key(authorization: str = Header(...)):
    expected = os.getenv("AGENTE_SECRET_KEY")
    if not expected:
        raise HTTPException(500, "AGENTE_SECRET_KEY não configurada")
    token = authorization.replace("Bearer ", "")
    if token != expected:
        raise HTTPException(401, "Chave inválida")

def get_graph():
    return criar_grafo()

def load_user_from_context(contexto):
    """Carrega dados do utilizador a partir do contexto enviado pelo frontend."""
    user_id = contexto.userId
    papel = contexto.papel
    if papel != "cliente":
        return None, []
    user = buscar_utilizador(user_id)
    veiculos = buscar_veiculos_cliente(user_id) if user else []
    return user, veiculos