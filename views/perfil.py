"""Perfil — dados pessoais, peso-alvo e cálculo das necessidades diárias."""
import streamlit as st

from core import calc, db
from views import tema


def mostrar():
    tema.cabecalho("👤", "O teu perfil",
                   "Os teus dados definem as calorias de manutenção e os alvos do objetivo")

    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid) or {}

    with st.form("form_perfil"):
        c1, c2 = st.columns(2)
        sexo = c1.radio("Sexo", ["Homem", "Mulher"], horizontal=True,
                        index=0 if perfil.get("sexo", "Homem") == "Homem" else 1)
        idade = c2.number_input("Idade", 14, 100, int(perfil.get("idade", 25)))
        peso = c1.number_input("Peso (kg)", 30.0, 250.0, float(perfil.get("peso_kg", 70.0)), step=0.5)
        altura = c2.number_input("Altura (cm)", 120.0, 230.0, float(perfil.get("altura_cm", 170.0)), step=0.5)

        opcoes_atividade = list(calc.FATORES_ATIVIDADE)
        atividade = st.selectbox("Exercício físico", opcoes_atividade,
                                 index=opcoes_atividade.index(perfil["atividade"])
                                 if perfil.get("atividade") in opcoes_atividade else 1)
        objetivo = st.selectbox("Objetivo", calc.OBJETIVOS,
                                index=calc.OBJETIVOS.index(perfil["objetivo"])
                                if perfil.get("objetivo") in calc.OBJETIVOS else 0)
        ritmo = st.slider("Ritmo (kg por semana, se quiseres emagrecer/engordar)",
                          0.25, 1.0, float(perfil.get("ritmo_kg_semana", 0.5)), 0.25,
                          help="0,5 kg/semana é um ritmo sustentável. Acima de 0,75 é agressivo.")

        usar_alvo = st.checkbox("Tenho um peso-alvo", value=bool(perfil.get("peso_alvo_kg")))
        peso_alvo = st.number_input("Peso-alvo (kg)", 30.0, 250.0,
                                    float(perfil.get("peso_alvo_kg") or peso), step=0.5,
                                    disabled=not usar_alvo,
                                    help="Usado na página Progresso para estimar quando o atinges.")

        if st.form_submit_button("💾 Guardar perfil", type="primary"):
            db.guardar_perfil(uid, sexo, idade, peso, altura, atividade, objetivo, ritmo,
                              peso_alvo if usar_alvo else None)
            st.success("Perfil guardado!")
            st.rerun()

    perfil = db.obter_perfil(uid)
    if perfil:
        st.divider()
        st.subheader("As tuas necessidades")
        alvos = calc.alvos_diarios(perfil)
        tmb_valor = calc.tmb(perfil["sexo"], perfil["peso_kg"], perfil["altura_cm"], perfil["idade"])
        manutencao = calc.tdee(perfil)

        c1, c2, c3 = st.columns(3)
        c1.metric("Metabolismo basal", f"{tmb_valor:.0f} kcal",
                  help="O que o teu corpo gasta em repouso absoluto")
        c2.metric("Manutenção", f"{manutencao:.0f} kcal",
                  help="O que gastas por dia com a tua atividade — comer isto mantém o peso")
        c3.metric("O teu alvo diário", f"{alvos['kcal']} kcal",
                  delta=f"{alvos['kcal'] - manutencao:+.0f} kcal vs manutenção",
                  delta_color="off")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Proteína", f"{alvos['proteina_g']} g")
        c2.metric("Hidratos", f"{alvos['hidratos_g']} g")
        c3.metric("Gordura", f"{alvos['gordura_g']} g")
        c4.metric("Água", f"{alvos['agua_ml']} ml")
