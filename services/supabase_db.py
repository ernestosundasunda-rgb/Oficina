"""Queries Supabase (produção)"""
from services.supabase_client import get_supabase
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

# ---------- UTILIZADORES ----------
def buscar_utilizador(user_id: int) -> Optional[Dict[str, Any]]:
    supabase = get_supabase()
    res = supabase.table("utilizadores").select("*").eq("id", user_id).eq("papel", "cliente").execute()
    return res.data[0] if res.data else None

def criar_utilizador(nome: str, telefone: str, email: str = None, endereco: str = None) -> Optional[Dict[str, Any]]:
    supabase = get_supabase()
    dados = {"nome": nome, "telefone": telefone, "hash_senha": "sem_senha", "papel": "cliente"}
    if email: dados["email"] = email
    if endereco: dados["endereco"] = endereco
    res = supabase.table("utilizadores").insert(dados).execute()
    return res.data[0] if res.data else None

# ---------- VEÍCULOS ----------
def buscar_veiculos_cliente(cliente_id: int) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    res = supabase.table("veiculos").select("*").eq("cliente_id", cliente_id).execute()
    return res.data

# ---------- ORDENS DE SERVIÇO ----------
def buscar_ordens_cliente(cliente_id: int) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    return supabase.table("ordens_servico")\
        .select("*, veiculos(matricula, marca, modelo)")\
        .eq("cliente_id", cliente_id)\
        .order("criado_em", desc=True).execute().data

def buscar_ordem_por_placa(cliente_id: int, placa: str) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    return supabase.table("ordens_servico")\
        .select("*, veiculos!inner(matricula, marca, modelo)")\
        .eq("cliente_id", cliente_id)\
        .ilike("veiculos.matricula", f"%{placa}%")\
        .order("criado_em", desc=True).execute().data

# ---------- AGENDAMENTO / DISPONIBILIDADE ----------
def buscar_disponibilidade(data: str) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    return supabase.table("disponibilidade_tecnico")\
        .select("*, utilizadores(nome, especialidade)")\
        .eq("data", data).eq("disponivel", True).execute().data

def verificar_data_disponivel(data: str) -> bool:
    return len(buscar_disponibilidade(data)) > 0

def buscar_datas_lotadas(inicio: str, fim: str) -> List[str]:
    supabase = get_supabase()
    res = supabase.table("disponibilidade_tecnico")\
        .select("data").eq("disponivel", True)\
        .gte("data", inicio).lte("data", fim).execute().data
    disponiveis = {d["data"] for d in res}
    todas = []
    d_ini = datetime.strptime(inicio, "%Y-%m-%d")
    d_fim = datetime.strptime(fim, "%Y-%m-%d")
    atual = d_ini
    while atual <= d_fim:
        s = atual.strftime("%Y-%m-%d")
        if s not in disponiveis:
            todas.append(s)
        atual += timedelta(days=1)
    return todas

def criar_agendamento(cliente_id: int, data: str, hora: str, servico: str, tecnico_id: int, veiculo_id: int = None) -> Optional[Dict[str, Any]]:
    supabase = get_supabase()
    dados = {
        "cliente_id": cliente_id,
        "data_agendada": data,
        "descricao": servico,
        "tecnico_id": tecnico_id,
        "estado": "pendente",
        "prioridade": "media"
    }
    if veiculo_id: dados["veiculo_id"] = veiculo_id
    res = supabase.table("ordens_servico").insert(dados).execute()
    return res.data[0] if res.data else None

# ---------- INTERAÇÕES / HISTÓRICO ----------
def guardar_interacao(user_id: int, direcao: str, conteudo: str, metadados: dict = None):
    supabase = get_supabase()
    supabase.table("interacoes").insert({
        "utilizador_id": user_id,
        "direcao": direcao,
        "conteudo": conteudo,
        "metadados": metadados or {}
    }).execute()

def buscar_historico(user_id: int, limite: int = 10) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    res = supabase.table("interacoes").select("*")\
        .eq("utilizador_id", user_id)\
        .order("criado_em", desc=True).limit(limite).execute()
    return list(reversed(res.data))

# ---------- LOGS ----------
def guardar_log_decisao(tipo: str, entrada: dict, saida: dict, justificativa: str = ""):
    supabase = get_supabase()
    supabase.table("logs_decisao_agente").insert({
        "tipo_decisao": tipo, "entrada": entrada, "saida": saida, "justificativa": justificativa
    }).execute()