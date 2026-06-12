"""
Nó Agendamento: verifica disponibilidade de técnicos e cria ordem de serviço.
Acesso restrito a clientes autenticados.
"""

from datetime import datetime, timedelta
from services.supabase_db import (
    buscar_disponibilidade,
    buscar_datas_lotadas,
    criar_agendamento
)
from graph.state import AgenteState
import re


def _extrair_dados_agendamento(msg: str) -> dict:
    """Extrai data, hora e serviço de uma mensagem de texto."""
    dados = {}
    m = re.search(r'(?:data|Data)\s*[:=—-]\s*(\d{4}-\d{2}-\d{2})', msg)
    if m:
        dados["data"] = m.group(1)
    m = re.search(r'(?:hora|Hora)\s*[:=—-]\s*(\d{2}:\d{2})', msg)
    if m:
        dados["hora"] = m.group(1)
    m = re.search(
        r'(?:servi[çc]o|Servi[çc]o|servico|Servico)\s*[:=—-]\s*(.+?)(?:\n|$|,\s*(?:Data|Hora|Ve[íi]culo))',
        msg
    )
    if m:
        dados["servico"] = m.group(1).strip().rstrip(',')
    return dados


def _encontrar_data_proxima(data_str: str, datas_lotadas: list) -> list:
    """Retorna até 3 datas disponíveis mais próximas, ignorando domingos."""
    try:
        alvo = datetime.strptime(data_str, "%Y-%m-%d")
    except ValueError:
        return []
    sugestoes = []
    delta = 1
    while len(sugestoes) < 3 and delta <= 30:
        for direcao in (1, -1):
            candidata = alvo + timedelta(days=delta * direcao)
            s = candidata.strftime("%Y-%m-%d")
            if candidata.weekday() != 6 and s not in datas_lotadas and s not in sugestoes:
                sugestoes.append(s)
                if len(sugestoes) >= 3:
                    break
        delta += 1
    return sorted(sugestoes)


def _data_futura(data_str: str) -> bool:
    """Verifica se a data é hoje ou no futuro."""
    try:
        return datetime.strptime(data_str, "%Y-%m-%d").date() >= datetime.now().date()
    except ValueError:
        return False


def no_agendamento(state: AgenteState) -> AgenteState:
    """Processa o pedido de agendamento."""
    user = state.get("utilizador")

    # Bloqueia acesso a não autenticados
    if not user:
        state["resposta_final"] = (
            "🔒 Para agendar um serviço, precisas de ter conta no nosso site oficial. "
            "Acede a https://oficinalpn.com e cria a tua conta. É rápido e seguro!"
        )
        return state

    nome = user["nome"]
    uid = user["id"]
    partial = state.setdefault("agendamento_parcial", {})

    # Integra dados fornecidos pelo utilizador
    if state.get("intencao") == "fornecer_dados" and state.get("dados_extraidos"):
        partial.update(state["dados_extraidos"])
        state["agendamento_parcial"] = partial

    # FASE 1 – Pedir data
    if not partial.get("data"):
        state["pendente"] = "data"
        state["resposta_final"] = f"📅 {nome}, para que data queres agendar? (ex: 2026-06-20)"
        return state

    # FASE 2 – Pedir hora
    if not partial.get("hora"):
        state["pendente"] = "hora"
        state["resposta_final"] = f"🕐 Certo, data {partial['data']}. A que horas? (ex: 14:30)"
        return state

    # FASE 3 – Pedir serviço
    if not partial.get("servico"):
        state["pendente"] = "servico"
        state["resposta_final"] = f"🔧 Qual o serviço que queres agendar? (ex: Troca de óleo)"
        return state

    # Dados completos – validar
    data = partial["data"]
    hora = partial["hora"]
    servico = partial["servico"]
    state["pendente"] = None

    # Regra 1: data não pode estar no passado
    if not _data_futura(data):
        partial["data"] = None
        state["agendamento_parcial"] = partial
        state["pendente"] = "data"
        state["resposta_final"] = (
            f"❌ A data {data} já passou. Por favor, escolhe uma data a partir de hoje."
        )
        return state

    # Regra 2: a oficina não trabalha aos domingos
    if datetime.strptime(data, "%Y-%m-%d").weekday() == 6:
        partial["data"] = None
        state["agendamento_parcial"] = partial
        state["pendente"] = "data"
        state["resposta_final"] = (
            "❌ A oficina não abre aos domingos. Escolhe outro dia, por favor."
        )
        return state

    # Verificar disponibilidade de técnicos
    try:
        disponiveis = buscar_disponibilidade(data)
    except Exception as e:
        state["erro"] = str(e)
        state["resposta_final"] = "⚠️ Problema ao verificar disponibilidade. Tenta novamente."
        return state

    if disponiveis:
        tecnico = disponiveis[0]["tecnico_id"]
        try:
            ordem = criar_agendamento(uid, data, hora, servico, tecnico)
        except Exception as e:
            state["erro"] = str(e)
            state["resposta_final"] = "❌ Erro ao criar o agendamento. Tenta novamente."
            return state

        if ordem:
            state["agendamento_parcial"] = {}
            state["resposta_final"] = (
                f"✅ Agendamento confirmado, **{nome}**!\n\n"
                f"📅 Data: {data}\n"
                f"🕐 Hora: {hora}\n"
                f"🔧 Serviço: {servico}\n"
                f"🔢 Ordem nº {ordem['id']}\n\n"
                f"Obrigado! Qualquer alteração, é só avisar."
            )
        else:
            state["resposta_final"] = "❌ Não foi possível guardar o agendamento. Tenta novamente."
    else:
        # Sem técnicos disponíveis → sugerir datas alternativas
        inicio = datetime.now().strftime("%Y-%m-%d")
        fim = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        try:
            lotadas = buscar_datas_lotadas(inicio, fim)
        except Exception:
            lotadas = []
        sugestoes = _encontrar_data_proxima(data, lotadas)

        if sugestoes:
            partial["data"] = None
            state["agendamento_parcial"] = partial
            state["pendente"] = "data"
            state["resposta_final"] = (
                f"❌ {data} não tem técnicos disponíveis.\n\n"
                f"📅 Datas livres mais próximas:\n"
                + "\n".join(f"• {s}" for s in sugestoes) +
                "\n\nQual preferes?"
            )
        else:
            state["resposta_final"] = (
                f"Não encontrei datas livres nos próximos 30 dias. "
                f"Contacta a oficina diretamente para agendar."
            )

    return state