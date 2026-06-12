from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgenteState(TypedDict):
    session_id: str
    utilizador: Optional[Dict[str, Any]]
    veiculos: List[Dict[str, Any]]
    mensagem_usuario: str
    mensagens: Annotated[List[BaseMessage], add_messages]
    intencao: Optional[str]
    dados_extraidos: Dict[str, Any]
    contexto_rag: List[Dict[str, Any]]
    contexto_memoria: List[Dict[str, Any]]
    resposta_final: Optional[str]
    erro: Optional[str]
    pendente: Optional[str]
    agendamento_parcial: Dict[str, Any]
    cadastro_parcial: Dict[str, Any]