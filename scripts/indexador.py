"""
Indexador de FAQ para produção (Supabase + pgvector 384d).
Lê o ficheiro JSON do FAQ e insere os embeddings na tabela documento_chunks.

Uso:
    python scripts/indexador.py --arquivo dados/faq.json
"""

import json
import os
import sys
import argparse

# Adiciona a raiz ao path para permitir imports absolutos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.documents import Document
from services.supabase_client import get_supabase
from services.embeddings import get_embeddings


def carregar_faq(caminho: str) -> list[Document]:
    """Carrega o JSON do FAQ e retorna uma lista de Documents."""
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)

    documentos = []

    # A estrutura do teu JSON é {"faq_oficina": [ ... ]}
    if isinstance(dados, dict) and "faq_oficina" in dados:
        lista = dados["faq_oficina"]
    elif isinstance(dados, list):
        lista = dados
    else:
        raise ValueError("Formato de FAQ inesperado. Esperado objeto com chave 'faq_oficina' ou lista direta.")

    for item in lista:
        pergunta = item.get("pergunta", "")
        resposta = item.get("resposta", "")
        categoria = item.get("categoria", "geral")
        palavras_chave = item.get("palavras_chave", [])

        # Conteúdo que será efetivamente embedado
        conteudo = f"Pergunta: {pergunta}\nResposta: {resposta}"

        # Metadados que ajudam na filtragem e identificação
        metadados = {
            "tipo": "faq",
            "categoria": categoria,
            "pergunta": pergunta,
            "palavras_chave": ", ".join(palavras_chave) if isinstance(palavras_chave, list) else ""
        }

        doc = Document(page_content=conteudo, metadata=metadados)
        documentos.append(doc)

    return documentos


def indexar_para_supabase(documentos: list[Document]):
    """Gera embeddings e insere cada documento na tabela documento_chunks."""
    supabase = get_supabase()
    embeddings = get_embeddings()

    total = len(documentos)
    print(f"🧠 A gerar embeddings para {total} documentos...")

    for i, doc in enumerate(documentos, start=1):
        try:
            # Gera o embedding (lista de floats)
            embedding = embeddings.embed_documents([doc.page_content])[0]

            # Insere no Supabase
            supabase.table("documento_chunks").insert({
                "titulo": f"FAQ – {doc.metadata.get('pergunta', 'item')}",
                "conteudo": doc.page_content,
                "metadata": doc.metadata,
                "embedding": embedding
            }).execute()

            if i % 5 == 0 or i == total:
                print(f"   ✅ {i}/{total} indexados")

        except Exception as e:
            print(f"   ❌ Erro no documento {i}: {e}")

    print(f"🎉 FAQ indexada com sucesso! ({total} itens)")


def main():
    parser = argparse.ArgumentParser(description="Indexador de FAQ para Supabase")
    parser.add_argument(
        "--arquivo",
        required=True,
        help="Caminho para o ficheiro JSON do FAQ"
    )
    args = parser.parse_args()

    if not os.path.exists(args.arquivo):
        print(f"❌ Ficheiro não encontrado: {args.arquivo}")
        return

    print(f"📂 A carregar FAQ: {args.arquivo}")
    documentos = carregar_faq(args.arquivo)

    if not documentos:
        print("❌ Nenhum documento carregado. Verifica o conteúdo do JSON.")
        return

    indexar_para_supabase(documentos)


if __name__ == "__main__":
    main()