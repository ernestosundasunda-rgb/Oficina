from fastapi import APIRouter, Depends
from api.schemas import ChatRequest, ChatResponse
from api.dependencies import verify_secret_key, get_graph, load_user_from_context
from graph.state import AgenteState

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_secret_key)])
def chat(req: ChatRequest, grafo=Depends(get_graph)):
    user, veiculos = load_user_from_context(req.contexto_usuario)

    state: AgenteState = {
        "session_id": str(req.contexto_usuario.userId),
        "utilizador": user,
        "veiculos": veiculos,
        "mensagem_usuario": req.mensagem,
        "mensagens": [],
        "intencao": None,
        "dados_extraidos": {},
        "contexto_rag": [],
        "contexto_memoria": [],
        "resposta_final": None,
        "erro": None,
        "pendente": None,
        "agendamento_parcial": {},
        "cadastro_parcial": {},
    }

    result = grafo.invoke(state)
    return ChatResponse(
        resposta=result.get("resposta_final", ""),
        intencao=result.get("intencao"),
        utilizador=result.get("utilizador"),
    )