from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ContextoUsuario(BaseModel):
    userId: int
    papel: str = "cliente"

class ChatRequest(BaseModel):
    mensagem: str = Field(..., min_length=1, max_length=2000)
    contexto_usuario: ContextoUsuario

class ChatResponse(BaseModel):
    resposta: str
    intencao: Optional[str] = None
    utilizador: Optional[Dict[str, Any]] = None