from langgraph.graph import StateGraph, END
from graph.state import AgenteState
from graph.classificador import no_classificador
from graph.status import no_status
from graph.agendamento import no_agendamento
from graph.resposta_geral import no_resposta_geral
from services.supabase_db import guardar_interacao, guardar_log_decisao
from services.supabase_vector import guardar_memoria

def no_fornecer_dados(state: AgenteState) -> AgenteState:
    pendente = state.get("pendente", "")
    if "agendamento" in pendente or pendente in ("data", "hora", "servico"):
        return no_agendamento(state)
    if "status" in pendente or pendente in ("placa_status", "nome_status"):
        return no_status(state)
    return no_resposta_geral(state)

def no_guardar_historico(state: AgenteState) -> AgenteState:
    user = state.get("utilizador")
    if user and state.get("resposta_final"):
        uid = user["id"]
        intencao = state.get("intencao", "desconhecido")
        try:
            guardar_interacao(uid, "entrada", state["mensagem_usuario"], {"intencao": intencao})
            guardar_interacao(uid, "saida", state["resposta_final"], {"intencao": intencao})
            guardar_memoria(uid, f"{state['mensagem_usuario'][:100]} → {state['resposta_final'][:100]}")
            guardar_log_decisao("ia_decision",
                {"intencao": intencao, "msg": state["mensagem_usuario"][:200]},
                {"resposta": state["resposta_final"][:200]})
        except Exception:
            pass
    return state

def roteador(state: AgenteState) -> str:
    intencao = state.get("intencao", "")
    if intencao in ("agendar", "consultar_status") and not state.get("utilizador"):
        # redireciona para resposta geral com mensagem de cadastro
        return "no_resposta_geral"
    rotas = {
        "agendar": "no_agendamento",
        "consultar_status": "no_status",
        "informacao_geral": "no_resposta_geral",
        "conversa_casual": "no_resposta_geral",
        "fornecer_dados": "no_fornecer_dados",
        "cadastrar": "no_resposta_geral"  # será tratada lá com mensagem informativa
    }
    return rotas.get(intencao, "no_resposta_geral")

def criar_grafo():
    w = StateGraph(AgenteState)
    w.add_node("classificador", no_classificador)
    w.add_node("no_status", no_status)
    w.add_node("no_agendamento", no_agendamento)
    w.add_node("no_resposta_geral", no_resposta_geral)
    w.add_node("no_fornecer_dados", no_fornecer_dados)
    w.add_node("no_guardar_historico", no_guardar_historico)

    w.set_entry_point("classificador")
    w.add_conditional_edges("classificador", roteador, {
        "no_status": "no_status",
        "no_agendamento": "no_agendamento",
        "no_resposta_geral": "no_resposta_geral",
        "no_fornecer_dados": "no_fornecer_dados"
    })

    for n in ("no_status", "no_agendamento", "no_resposta_geral", "no_fornecer_dados"):
        w.add_edge(n, "no_guardar_historico")
    w.add_edge("no_guardar_historico", END)

    return w.compile()