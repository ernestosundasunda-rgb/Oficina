"""
Nó Status: consulta as ordens de serviço do cliente autenticado.
Apenas clientes com sessão iniciada podem ver os seus próprios serviços.
"""

from services.supabase_db import buscar_ordens_cliente, buscar_ordem_por_placa
from services.groq_client import get_groq
from graph.state import AgenteState


def no_status(state: AgenteState) -> AgenteState:
    """Mostra as ordens de serviço associadas ao cliente logado."""
    groq = get_groq()
    user = state.get("utilizador")

    # Bloqueia acesso a não autenticados
    if not user:
        state["resposta_final"] = (
            "🔒 Para consultares os teus serviços, precisas de ter conta no nosso site oficial. "
            "Acede a https://oficinalpn.com e cria a tua conta. É rápido e seguro!"
        )
        return state

    uid = user["id"]
    nome = user["nome"]
    placa = state.get("dados_extraidos", {}).get("placa")

    try:
        if placa:
            ordens = buscar_ordem_por_placa(uid, placa)
        else:
            ordens = buscar_ordens_cliente(uid)
    except Exception as e:
        state["erro"] = str(e)
        state["resposta_final"] = "⚠️ Problema ao consultar os serviços. Tenta novamente."
        return state

    if not ordens:
        state["resposta_final"] = (
            f"Não tens nenhum serviço registado, **{nome}**.\n"
            f"Para agendar um serviço, diz **'quero agendar'**."
        )
        return state

    estado_map = {
        "pendente": "⏳ Pendente",
        "em_andamento": "🔧 Em andamento",
        "aguardando_pecas": "📦 Aguardando peças",
        "concluida": "✅ Concluída",
        "cancelada": "❌ Cancelada"
    }

    linhas = []
    for o in ordens:
        veiculo = o.get("veiculos", {})
        estado_str = estado_map.get(o.get("estado", ""), o.get("estado", ""))
        linhas.append(
            f"🔢 Ordem #{o['id']} – {estado_str}\n"
            f"🚗 {veiculo.get('marca','')} {veiculo.get('modelo','')} "
            f"({veiculo.get('matricula','')})\n"
            f"🔧 Serviço: {o.get('descricao','')}\n"
            f"📅 Previsão: {o.get('data_prevista') or o.get('data_agendada') or 'a definir'}"
        )

    prompt = (
        f"Cliente: {nome} (ID {uid})\n\n"
        f"Serviços em curso:\n" + "\n\n".join(linhas) + "\n\n"
        f"Responde de forma organizada, profissional e amigável. "
        f"Trata o cliente por **{nome}**."
    )

    try:
        state["resposta_final"] = groq.invoke(prompt).content
    except Exception as e:
        state["erro"] = str(e)
        state["resposta_final"] = "Erro ao gerar a resposta. Tenta novamente."

    return state