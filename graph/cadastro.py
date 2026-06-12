import re
from services.supabase_db import criar_utilizador, buscar_utilizador_por_telefone
from services.groq_client import get_groq
from graph.state import AgenteState

def _extrair_dados_cadastro(msg: str) -> dict:
    dados = {}
    m = re.search(r'(?:nome|Nome)\s*[:=—-]\s*(.+?)(?:\n|$|,|Telefone|Email|Endere[çc]o)', msg)
    if m: dados["nome"] = m.group(1).strip().rstrip(',')
    m = re.search(r'(?:telefone|Telefone)\s*[:=—-]\s*(.+?)(?:\n|$|,|Email|Endere[çc]o)', msg)
    if m: dados["telefone"] = m.group(1).strip().rstrip(',')
    m = re.search(r'(?:e-?mail|E-?mail)\s*[:=—-]\s*(.+?)(?:\n|$|,|Endere[çc]o)', msg)
    if m:
        v = m.group(1).strip().rstrip(',')
        if v.lower() not in ("não","nao","skip","-"): dados["email"] = v
    m = re.search(r'(?:endere[çc]o|Endere[çc]o|morada)\s*[:=—-]\s*(.+?)(?:\n|$)', msg)
    if m:
        v = m.group(1).strip().rstrip(',')
        if v.lower() not in ("não","nao","skip","-"): dados["endereco"] = v
    return dados

def no_cadastro(state: AgenteState) -> AgenteState:
    groq = get_groq()
    if state.get("intencao") == "fornecer_dados" or state.get("dados_extraidos", {}).get("mensagem_completa"):
        msg = state.get("dados_extraidos", {}).get("mensagem_completa", state["mensagem_usuario"])
        dados = _extrair_dados_cadastro(msg)
        if not dados.get("nome") or not dados.get("telefone"):
            try:
                resp = groq.invoke(f"Extrai JSON com nome, telefone, email, endereco desta mensagem: {msg}")
                import json
                conteudo = resp.content.strip()
                if conteudo.startswith("```"): conteudo = conteudo.split("\n",1)[1].rsplit("\n",1)[0]
                dados.update(json.loads(conteudo))
            except: pass
        nome = dados.get("nome")
        tel = dados.get("telefone")
        if not nome or not tel:
            state["pendente"] = "dados_cadastro"
            state["resposta_final"] = "❌ Preciso do nome e telefone. Usa:\nNome: ...\nTelefone: ..."
            return state
        existente = buscar_utilizador_por_telefone(tel)
        if existente:
            state["session_id"] = str(existente["id"])
            state["utilizador"] = existente
            state["pendente"] = None
            state["resposta_final"] = f"✅ Bem-vindo de volta, {existente['nome']}!"
            return state
        novo = criar_utilizador(nome, tel, dados.get("email"), dados.get("endereco"))
        if novo:
            state["session_id"] = str(novo["id"])
            state["utilizador"] = novo
            state["pendente"] = None
            state["resposta_final"] = f"✅ Cadastro concluído, {nome}! ID: {novo['id']}."
        else:
            state["resposta_final"] = "❌ Erro ao criar cadastro."
        return state
    state["pendente"] = "dados_cadastro"
    state["resposta_final"] = "📝 Para cadastro, envia:\nNome: ...\nTelefone: ...\nEmail: (opcional)\nEndereço: (opcional)"
    return state