"""Definições — região da base de dados de produtos (Open Food Facts)."""
import streamlit as st

from core import db
from views import tema

PAISES = {"pt": "🇵🇹 Portugal", "br": "🇧🇷 Brasil", "world": "🌍 Mundo (todos os países)"}


def mostrar():
    tema.cabecalho("⚙️", "Definições", "Sem chaves nem custos — só a base de dados de produtos")
    st.success("Esta app **não precisa de configuração nem de chaves pagas**. Os valores "
               "nutricionais vêm da tabela de alimentos comuns e da base gratuita "
               "**Open Food Facts**.")

    st.subheader("Base de dados de produtos")
    atual = db.obter_definicao("off_pais", "pt")
    chaves = list(PAISES)
    escolha = st.radio(
        "Região a usar quando pesquisas produtos de marca pelo nome",
        chaves, index=chaves.index(atual) if atual in chaves else 0,
        format_func=lambda k: PAISES[k],
    )
    if st.button("💾 Guardar", type="primary"):
        db.guardar_definicao("off_pais", escolha)
        st.success("Guardado!")

    st.caption("A pesquisa por nome dá prioridade a produtos da região escolhida. "
               "A pesquisa por código de barras funciona em qualquer região.")

    st.divider()
    st.caption("ℹ️ Open Food Facts (openfoodfacts.org) é uma base de dados colaborativa e "
               "gratuita. Os valores são aproximados e contribuídos por voluntários — "
               "podem faltar vitaminas/minerais nalguns produtos.")
