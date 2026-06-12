from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class Intencao(str, Enum):
    AGENDAR = "agendar"
    CONSULTAR_STATUS = "consultar_status"
    INFORMACAO_GERAL = "informacao_geral"
    CONVERSA_CASUAL = "conversa_casual"
    FORNECER_DADOS = "fornecer_dados"
    CADASTRAR = "cadastrar"  # o cliente pergunta como se cadastrar

class ClassificacaoOutput(BaseModel):
    intencao: Intencao = Field(description="Intenção principal")
    entidades: Optional[dict] = Field(default=None, description="Entidades extraídas")
    justificativa: str = Field(description="Breve explicação")

CLASSIFICADOR_PROMPT = """
Analisa a mensagem e classifica numa intenção:
- agendar: marcar serviço, data, hora
- consultar_status: saber estado do veículo
- informacao_geral: perguntas sobre serviços, preços, horários
- conversa_casual: saudação, agradecimento
- fornecer_dados: resposta a pergunta anterior (nome, telefone, data, hora, placa)
- cadastrar: perguntar como criar conta

Histórico: {historico}
Mensagem: {mensagem}
"""