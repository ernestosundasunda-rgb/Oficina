from services.groq_client import get_groq
from services.supabase_vector import buscar_documentos_similares
from services.supabase_db import buscar_historico
from graph.state import AgenteState

def no_resposta_geral(state: AgenteState) -> AgenteState:
    groq = get_groq()
    intencao = state["intencao"]
    user = state.get("utilizador")
    nome = user["nome"] if user else "cliente"

    hist_txt = ""
    if user:
        try:
            for h in buscar_historico(user["id"], 5):
                hist_txt += f"{h['direcao']}: {h['conteudo']}\n"
        except: pass

    mem_txt = "\n".join(f"- {m['conteudo']}" for m in state.get("contexto_memoria", []))

    persona = f"""Tu és o assistente virtual da Oficina LPN.
Trata o cliente por **{nome}**. NUNCA uses a palavra 'cliente' se sabes o nome.
Histórico recente:
{hist_txt}
Memória de longo prazo:
{mem_txt}
"""

    if intencao == "informacao_geral":
        try:
            docs = buscar_documentos_similares(state["mensagem_usuario"], k=3)
            ctx = "\n\n".join(d["conteudo"] for d in docs) if docs else "(sem dados)"
        except Exception as e:
            state["erro"] = str(e)
            ctx = "(erro ao aceder à base de conhecimento)"
        prompt = f"{persona}\nBase de conhecimento:\n{ctx}\nPergunta: {state['mensagem_usuario']}\nResposta:"
    else:
        prompt = f"{persona}\nMensagem casual: {state['mensagem_usuario']}\nResposta simpática e oferece ajuda:"

    resp = groq.invoke(prompt)
    state["resposta_final"] = resp.content
    return state