"""NutriDia — o teu diário alimentar inteligente."""
import os

import streamlit as st

st.set_page_config(page_title="NutriDia", page_icon="🥗", layout="wide")


def _secret(chave: str):
    try:
        return st.secrets.get(chave)
    except Exception:
        return None


# Configuração (vinda dos "secrets" do Streamlit Cloud, se existirem):
#  - database_url  -> usa Postgres em vez do SQLite local (dados persistentes)
#  - require_login -> "true" para obrigar a início de sessão
# O login só é exigido na versão online (base de dados Postgres) ou se for pedido
# explicitamente — no PC local (SQLite) continua sem login.
_db_url = _secret("database_url") or os.environ.get("NUTRIDIA_DB_URL")
if _db_url:
    os.environ["NUTRIDIA_DB_URL"] = _db_url
_is_postgres = bool(_db_url) and not str(_db_url).startswith("sqlite")
REQUER_LOGIN = _is_postgres or str(_secret("require_login") or "").lower() in ("1", "true", "yes")

from core import db
from views import (carencias, definicoes, historico, login, metas, meus_alimentos,
                   painel, perfil, registar, tema)

db.inicializar()
tema.aplicar()

# ---- Sessão / utilizador ----
if "uid" not in st.session_state:
    if REQUER_LOGIN:
        login.mostrar()
        st.stop()
    else:
        st.session_state["uid"] = db.garantir_utilizador_default()
        st.session_state["nome"] = "Eu"

with st.sidebar:
    st.markdown('<div class="nd-brand">🥗 <span>NutriDia</span></div>', unsafe_allow_html=True)
    if REQUER_LOGIN:
        st.markdown(f'<div class="nd-tag">Olá, {st.session_state.get("nome", "")} 👋</div>',
                    unsafe_allow_html=True)
        if st.button("Terminar sessão", use_container_width=True):
            for chave in ("uid", "nome", "cesto", "receita_cesto"):
                st.session_state.pop(chave, None)
            st.rerun()
    else:
        st.markdown('<div class="nd-tag">O teu diário alimentar</div>', unsafe_allow_html=True)

paginas = [
    st.Page(painel.mostrar, title="Painel", icon="📊", url_path="painel", default=True),
    st.Page(registar.mostrar, title="Registar refeição", icon="🍽️", url_path="registar"),
    st.Page(meus_alimentos.mostrar, title="Os meus alimentos", icon="🥣", url_path="meus-alimentos"),
    st.Page(historico.mostrar, title="Histórico", icon="📅", url_path="historico"),
    st.Page(metas.mostrar, title="Progresso", icon="🎯", url_path="progresso"),
    st.Page(carencias.mostrar, title="Carências e sintomas", icon="🔬", url_path="carencias"),
    st.Page(perfil.mostrar, title="Perfil", icon="👤", url_path="perfil"),
    st.Page(definicoes.mostrar, title="Definições", icon="⚙️", url_path="definicoes"),
]

st.navigation(paginas).run()
