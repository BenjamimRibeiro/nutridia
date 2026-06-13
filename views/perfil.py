"""Perfil — dados pessoais, peso-alvo e cálculo das necessidades diárias."""
import streamlit as st

from core import calc, db, dieta, i18n, nutrients, sol, suplementos
from views import tema


def mostrar():
    tema.cabecalho("👤", i18n.t("O teu perfil", "Your profile"),
                   i18n.t("Os teus dados definem as calorias de manutenção e os alvos do objetivo",
                          "Your data sets your maintenance calories and goal targets"))

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

        # ---- Alergias, preferências e suplementos ----
        st.divider()
        st.subheader("🥗 Alergias, preferências e suplementos")
        st.caption("As alergias e preferências adaptam as **refeições inteligentes**. "
                   "Os suplementos contam automaticamente nos teus totais diários.")
        with st.form("form_prefs"):
            alergias = st.multiselect("Alergias / intolerâncias", dieta.ALERGIAS,
                                      default=perfil.get("alergias", []))
            restricoes = st.multiselect("Preferências alimentares", dieta.PREFERENCIAS,
                                        default=perfil.get("restricoes", []))
            sup = st.multiselect("💊 Suplementos que tomas todos os dias",
                                 list(suplementos.CATALOGO), default=perfil.get("suplementos", []))
            niveis_sol = list(sol.NIVEIS)
            sol_atual = perfil.get("sol_habitual") or sol.PREDEFINIDO
            sol_nivel = st.selectbox(
                "☀️ Exposição solar habitual (o sol é a maior fonte de vitamina D)", niveis_sol,
                index=niveis_sol.index(sol_atual) if sol_atual in niveis_sol else 1,
                help="O teu corpo produz vitamina D ao apanhar sol. Indica quanto sol "
                     "apanhas por dia, em média — conta automaticamente todos os dias.")
            if st.form_submit_button("💾 Guardar preferências", type="primary"):
                db.guardar_preferencias(uid, restricoes, alergias, sup, sol_nivel)
                st.success("Guardado! Suplementos e sol passam a contar nos teus totais diários.")
                st.rerun()

        notas = []
        if perfil.get("suplementos"):
            nut = suplementos.nutrientes_de(perfil["suplementos"])
            notas.append("💊 **Suplementos:** " + " · ".join(
                f"{nutrients.nome_de(c)} +{v:.0f} {nutrients.unidade_de(c)}" for c, v in nut.items()))
        if perfil.get("sol_habitual") and sol.vit_d(perfil["sol_habitual"]):
            notas.append(f"☀️ **Sol:** +{sol.vit_d(perfil['sol_habitual']):.0f} µg de vitamina D/dia")
        for nota in notas:
            st.caption(nota)
