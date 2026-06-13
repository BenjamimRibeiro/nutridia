"""Ecrã de início de sessão / criação de conta (apenas na versão online)."""
import streamlit as st

from core import db
from views import tema


def mostrar() -> None:
    tema.cabecalho("🥗", "NutriDia", "Entra na tua conta para acederes ao teu diário")

    entrar, criar = st.tabs(["🔑 Entrar", "✨ Criar conta"])

    with entrar:
        with st.form("entrar"):
            username = st.text_input("Nome de utilizador")
            password = st.text_input("Palavra-passe", type="password")
            if st.form_submit_button("Entrar", type="primary"):
                conta = db.autenticar(username, password)
                if conta:
                    st.session_state["uid"] = conta["id"]
                    st.session_state["nome"] = conta["nome"]
                    st.rerun()
                else:
                    st.error("Nome de utilizador ou palavra-passe incorretos.")

    with criar:
        with st.form("criar"):
            nome = st.text_input("O teu nome", placeholder="Como queres ser tratado")
            novo_user = st.text_input("Nome de utilizador", placeholder="só letras/números, sem espaços")
            p1 = st.text_input("Palavra-passe", type="password")
            p2 = st.text_input("Confirma a palavra-passe", type="password")
            if st.form_submit_button("Criar conta", type="primary"):
                if not nome.strip() or not novo_user.strip():
                    st.error("Preenche o nome e o nome de utilizador.")
                elif len(novo_user.strip()) < 3:
                    st.error("O nome de utilizador deve ter pelo menos 3 caracteres.")
                elif len(p1) < 6:
                    st.error("A palavra-passe deve ter pelo menos 6 caracteres.")
                elif p1 != p2:
                    st.error("As palavras-passe não coincidem.")
                elif db.username_existe(novo_user):
                    st.error("Esse nome de utilizador já existe. Escolhe outro.")
                else:
                    uid = db.criar_conta(nome, novo_user, p1)
                    st.session_state["uid"] = uid
                    st.session_state["nome"] = nome.strip()
                    st.success("Conta criada! A entrar…")
                    st.rerun()

    st.caption("🔒 A tua palavra-passe é guardada de forma encriptada (hash). "
               "Cada utilizador só vê o seu próprio diário.")
