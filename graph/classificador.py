from langchain_core.messages import HumanMessage
from services.groq_client import get_groq
from services.supabase_vector import buscar_memoria_similar
from graph.intencao import CLASSIFICADOR_PROMPT, ClassificacaoOutput
from graph.state import AgenteState

def no_classificador(state: AgenteState) -> AgenteState:
    groq = get_groq()
    session_id = state.get("session_id", "")
    try:
        user_id = int(session_id)
    except (ValueError, TypeError):
        user_id = None

    user = state.get("utilizador")
    cadastrado = user is not None

    pendente = state.get("pendente")
    if pendente:
        state["intencao"] = "fornecer_dados"
        state["erro"] = None
        state["dados_extraidos"] = {"mensagem_completa": state["mensagem_usuario"]}
        return state

    if cadastrado:
        try:
            memorias = buscar_memoria_similar(user_id, state["mensagem_usuario"], k=3)
            state["contexto_memoria"] = memorias
        except Exception:
            state["contexto_memoria"] = []

    hist = ""
    for msg in state["mensagens"][-6:-1]:
        if hasattr(msg, "content"):
            papel = "Cliente" if isinstance(msg, HumanMessage) else "Assistente"
            hist += f"{papel}: {msg.content}\n"
    if state["contexto_memoria"]:
        hist += "\n=== MEMÓRIA DE LONGO PRAZO ===\n"
        for m in state["contexto_memoria"]:
            hist += f"- {m['conteudo']}\n"

    prompt = CLASSIFICADOR_PROMPT.format(historico=hist or "(nova conversa)", mensagem=state["mensagem_usuario"])
    groq_structured = groq.with_structured_output(ClassificacaoOutput)

    try:
        resp = groq_structured.invoke(prompt)
        state["intencao"] = resp.intencao.value
        state["dados_extraidos"] = resp.entidades or {}
        state["erro"] = None
    except Exception as e:
        state["intencao"] = "conversa_casual"
        state["dados_extraidos"] = {}
        state["erro"] = str(e)

    return state