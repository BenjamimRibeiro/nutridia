"""Ecrã de início de sessão / criação de conta (apenas na versão online)."""
import streamlit as st

from core import db, i18n
from views import tema

_t = i18n.t


def mostrar() -> None:
    tema.cabecalho("🥗", "NutriDia",
                   _t("Entra na tua conta para acederes ao teu diário",
                      "Sign in to access your diary"))

    entrar, criar = st.tabs([_t("🔑 Entrar", "🔑 Sign in"), _t("✨ Criar conta", "✨ Sign up")])

    with entrar:
        with st.form("entrar"):
            username = st.text_input(_t("Nome de utilizador", "Username"))
            password = st.text_input(_t("Palavra-passe", "Password"), type="password")
            if st.form_submit_button(_t("Entrar", "Sign in"), type="primary"):
                conta = db.autenticar(username, password)
                if conta:
                    st.session_state["uid"] = conta["id"]
                    st.session_state["nome"] = conta["nome"]
                    st.rerun()
                else:
                    st.error(_t("Nome de utilizador ou palavra-passe incorretos.",
                                "Wrong username or password."))

    with criar:
        with st.form("criar"):
            nome = st.text_input(_t("O teu nome", "Your name"),
                                 placeholder=_t("Como queres ser tratado", "How you'd like to be called"))
            novo_user = st.text_input(_t("Nome de utilizador", "Username"),
                                      placeholder=_t("só letras/números, sem espaços",
                                                     "letters/numbers only, no spaces"))
            p1 = st.text_input(_t("Palavra-passe", "Password"), type="password")
            p2 = st.text_input(_t("Confirma a palavra-passe", "Confirm password"), type="password")
            if st.form_submit_button(_t("Criar conta", "Create account"), type="primary"):
                if not nome.strip() or not novo_user.strip():
                    st.error(_t("Preenche o nome e o nome de utilizador.",
                                "Fill in your name and username."))
                elif len(novo_user.strip()) < 3:
                    st.error(_t("O nome de utilizador deve ter pelo menos 3 caracteres.",
                                "Username must be at least 3 characters."))
                elif len(p1) < 6:
                    st.error(_t("A palavra-passe deve ter pelo menos 6 caracteres.",
                                "Password must be at least 6 characters."))
                elif p1 != p2:
                    st.error(_t("As palavras-passe não coincidem.", "Passwords don't match."))
                elif db.username_existe(novo_user):
                    st.error(_t("Esse nome de utilizador já existe. Escolhe outro.",
                                "That username already exists. Pick another."))
                else:
                    uid = db.criar_conta(nome, novo_user, p1)
                    st.session_state["uid"] = uid
                    st.session_state["nome"] = nome.strip()
                    st.success(_t("Conta criada! A entrar…", "Account created! Signing in…"))
                    st.rerun()

    st.caption(_t("🔒 A tua palavra-passe é guardada de forma encriptada (hash). "
                  "Cada utilizador só vê o seu próprio diário.",
                  "🔒 Your password is stored encrypted (hashed). Each user only sees "
                  "their own diary."))
