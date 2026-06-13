"""Perfil — dados pessoais, peso-alvo, preferências e suplementos."""
import streamlit as st

from core import calc, db, dieta, i18n, nutrients, sol, suplementos
from views import tema

_t = i18n.t

# nutrientes oferecidos ao criar um suplemento próprio
_CAMPOS_SUP = ["kcal", "proteina_g", "omega3_g", "vit_c_mg", "vit_d_ug", "vit_b12_ug",
               "calcio_mg", "ferro_mg", "magnesio_mg", "zinco_mg", "vit_e_mg", "vit_a_ug",
               "folato_ug", "vit_b6_mg", "vit_b1_mg", "vit_b2_mg", "vit_b3_mg", "potassio_mg"]


def mostrar():
    tema.cabecalho("👤", _t("O teu perfil", "Your profile"),
                   _t("Os teus dados definem as calorias de manutenção e os alvos do objetivo",
                      "Your data sets your maintenance calories and goal targets"))

    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid) or {}

    with st.form("form_perfil"):
        c1, c2 = st.columns(2)
        sexo = c1.radio(_t("Sexo", "Sex"), ["Homem", "Mulher"], horizontal=True,
                        index=0 if perfil.get("sexo", "Homem") == "Homem" else 1,
                        format_func=lambda s: _t("Homem", "Male") if s == "Homem"
                        else _t("Mulher", "Female"))
        idade = c2.number_input(_t("Idade", "Age"), 14, 100, int(perfil.get("idade", 25)))
        peso = c1.number_input(_t("Peso (kg)", "Weight (kg)"), 30.0, 250.0,
                               float(perfil.get("peso_kg", 70.0)), step=0.5)
        altura = c2.number_input(_t("Altura (cm)", "Height (cm)"), 120.0, 230.0,
                                 float(perfil.get("altura_cm", 170.0)), step=0.5)

        opcoes_atividade = list(calc.FATORES_ATIVIDADE)
        atividade = st.selectbox(_t("Exercício físico", "Physical activity"), opcoes_atividade,
                                 index=opcoes_atividade.index(perfil["atividade"])
                                 if perfil.get("atividade") in opcoes_atividade else 1,
                                 format_func=calc.nome_atividade)
        objetivo = st.selectbox(_t("Objetivo", "Goal"), calc.OBJETIVOS,
                                index=calc.OBJETIVOS.index(perfil["objetivo"])
                                if perfil.get("objetivo") in calc.OBJETIVOS else 0,
                                format_func=calc.nome_objetivo)
        ritmo = st.slider(_t("Ritmo (kg por semana, se quiseres emagrecer/engordar)",
                             "Pace (kg per week, if losing/gaining)"),
                          0.25, 1.0, float(perfil.get("ritmo_kg_semana", 0.5)), 0.25,
                          help=_t("0,5 kg/semana é um ritmo sustentável. Acima de 0,75 é agressivo.",
                                  "0.5 kg/week is sustainable. Above 0.75 is aggressive."))

        usar_alvo = st.checkbox(_t("Tenho um peso-alvo", "I have a target weight"),
                                value=bool(perfil.get("peso_alvo_kg")))
        peso_alvo = st.number_input(_t("Peso-alvo (kg)", "Target weight (kg)"), 30.0, 250.0,
                                    float(perfil.get("peso_alvo_kg") or peso), step=0.5,
                                    disabled=not usar_alvo,
                                    help=_t("Usado na página Progresso para estimar quando o atinges.",
                                            "Used on the Progress page to estimate when you'll reach it."))

        if st.form_submit_button(_t("💾 Guardar perfil", "💾 Save profile"), type="primary"):
            db.guardar_perfil(uid, sexo, idade, peso, altura, atividade, objetivo, ritmo,
                              peso_alvo if usar_alvo else None)
            st.success(_t("Perfil guardado!", "Profile saved!"))
            st.rerun()

    perfil = db.obter_perfil(uid)
    if not perfil:
        return

    st.divider()
    st.subheader(_t("As tuas necessidades", "Your needs"))
    alvos = calc.alvos_diarios(perfil)
    tmb_valor = calc.tmb(perfil["sexo"], perfil["peso_kg"], perfil["altura_cm"], perfil["idade"])
    manutencao = calc.tdee(perfil)

    c1, c2, c3 = st.columns(3)
    c1.metric(_t("Metabolismo basal", "Basal metabolism"), f"{tmb_valor:.0f} kcal",
              help=_t("O que o teu corpo gasta em repouso absoluto",
                      "What your body burns at complete rest"))
    c2.metric(_t("Manutenção", "Maintenance"), f"{manutencao:.0f} kcal",
              help=_t("O que gastas por dia com a tua atividade — comer isto mantém o peso",
                      "What you burn per day with your activity — eating this keeps your weight"))
    c3.metric(_t("O teu alvo diário", "Your daily target"), f"{alvos['kcal']} kcal",
              delta=_t(f"{alvos['kcal'] - manutencao:+.0f} kcal vs manutenção",
                       f"{alvos['kcal'] - manutencao:+.0f} kcal vs maintenance"),
              delta_color="off")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(_t("Proteína", "Protein"), f"{alvos['proteina_g']} g")
    c2.metric(_t("Hidratos", "Carbs"), f"{alvos['hidratos_g']} g")
    c3.metric(_t("Gordura", "Fat"), f"{alvos['gordura_g']} g")
    c4.metric(_t("Água", "Water"), f"{alvos['agua_ml']} ml")

    # ---- Alergias, preferências e suplementos ----
    st.divider()
    st.subheader(_t("🥗 Alergias, preferências e suplementos",
                    "🥗 Allergies, preferences and supplements"))
    st.caption(_t("As alergias e preferências adaptam as **refeições inteligentes**. "
                  "Os suplementos e o sol contam automaticamente nos teus totais diários.",
                  "Allergies and preferences tailor the **smart suggestions**. Supplements and "
                  "sun count automatically in your daily totals."))

    custom_nomes = [s["nome"] for s in db.listar_suplementos_custom(uid)]
    opcoes_sup = sorted(list(suplementos.CATALOGO) + custom_nomes,
                        key=lambda s: suplementos.nome(s).lower())

    with st.form("form_prefs"):
        alergias = st.multiselect(_t("Alergias / intolerâncias", "Allergies / intolerances"),
                                  dieta.ALERGIAS, default=perfil.get("alergias", []),
                                  format_func=dieta.nome_alergia)
        restricoes = st.multiselect(_t("Preferências alimentares", "Dietary preferences"),
                                    dieta.PREFERENCIAS, default=perfil.get("restricoes", []),
                                    format_func=dieta.nome_preferencia)
        sup = st.multiselect(_t("💊 Suplementos que tomas todos os dias",
                                "💊 Supplements you take daily"), opcoes_sup,
                             default=[s for s in perfil.get("suplementos", []) if s in opcoes_sup],
                             format_func=suplementos.nome)
        niveis_sol = list(sol.NIVEIS)
        sol_atual = perfil.get("sol_habitual") or sol.PREDEFINIDO
        sol_nivel = st.selectbox(
            _t("☀️ Exposição solar habitual (o sol é a maior fonte de vitamina D)",
               "☀️ Usual sun exposure (sun is the main source of vitamin D)"), niveis_sol,
            index=niveis_sol.index(sol_atual) if sol_atual in niveis_sol else 1,
            format_func=sol.nome,
            help=_t("O teu corpo produz vitamina D ao apanhar sol. Conta todos os dias.",
                    "Your body makes vitamin D from sun. Counts every day."))
        if st.form_submit_button(_t("💾 Guardar preferências", "💾 Save preferences"), type="primary"):
            db.guardar_preferencias(uid, restricoes, alergias, sup, sol_nivel)
            st.success(_t("Guardado!", "Saved!"))
            st.rerun()

    # ---- Os meus suplementos (ver / editar / apagar) ----
    st.divider()
    st.subheader(_t("💊 Os meus suplementos", "💊 My supplements"))
    st.caption(_t("Suplementos que tu criaste — vê o que têm, edita ou apaga. Para os usares "
                  "no dia a dia, escolhe-os na lista de suplementos diários acima.",
                  "Supplements you created — view their contents, edit or delete. To use them "
                  "daily, pick them in the daily supplements list above."))
    meus = db.listar_suplementos_custom(uid)
    if not meus:
        st.caption(_t("Ainda não criaste nenhum suplemento.", "You haven't created any yet."))
    for s in meus:
        na_rotina = "✅ " if s["nome"] in perfil.get("suplementos", []) else ""
        with st.expander(f"💊 {na_rotina}{s['nome']}"):
            if s["nutrientes"]:
                st.markdown("**" + _t("Por dose", "Per dose") + ":** " + " · ".join(
                    f"{nutrients.nome_de(k)} {v:.0f} {nutrients.unidade_de(k)}"
                    for k, v in s["nutrientes"].items()))
            else:
                st.caption(_t("Sem valores definidos.", "No values set."))
            with st.form(f"edit_sup_{s['id']}"):
                novo_nome = st.text_input(_t("Nome", "Name"), s["nome"], key=f"ensup_{s['id']}")
                st.caption(_t("Editar valores por dose:", "Edit values per dose:"))
                cols = st.columns(3)
                vals = {}
                for k, campo in enumerate(_CAMPOS_SUP):
                    with cols[k % 3]:
                        vals[campo] = st.number_input(
                            f"{nutrients.nome_de(campo)} ({nutrients.unidade_de(campo)})",
                            0.0, value=float(s["nutrientes"].get(campo, 0)), step=0.5,
                            key=f"edit_{s['id']}_{campo}")
                cs1, cs2 = st.columns(2)
                if cs1.form_submit_button(_t("💾 Guardar alterações", "💾 Save changes"), type="primary"):
                    if not novo_nome.strip():
                        st.error(_t("Dá um nome ao suplemento.", "Give it a name."))
                    else:
                        db.atualizar_suplemento(s["id"], novo_nome.strip(),
                                                {c: v for c, v in vals.items() if v > 0})
                        # se estava na rotina e mudou de nome, mantém-no na rotina
                        rotina = perfil.get("suplementos", [])
                        if s["nome"] in rotina and novo_nome.strip() != s["nome"]:
                            rotina = [novo_nome.strip() if x == s["nome"] else x for x in rotina]
                            db.guardar_preferencias(uid, perfil.get("restricoes", []),
                                                    perfil.get("alergias", []), rotina,
                                                    perfil.get("sol_habitual"))
                        st.success(_t("Atualizado!", "Updated!"))
                        st.rerun()
                if cs2.form_submit_button(_t("🗑️ Apagar", "🗑️ Delete")):
                    db.apagar_suplemento(s["id"])
                    st.rerun()

    with st.expander(_t("➕ Criar novo suplemento", "➕ Create new supplement")):
        with st.form("novo_sup"):
            nome_sup = st.text_input(_t("Nome do suplemento", "Supplement name"),
                                     placeholder=_t("Ex.: O meu pré-treino", "E.g.: My pre-workout"))
            st.caption(_t("Indica o que **1 dose** te dá (deixa 0 no que não tiver):",
                          "Enter what **1 dose** gives you (leave 0 for none):"))
            cols = st.columns(3)
            vals = {}
            for k, campo in enumerate(_CAMPOS_SUP):
                with cols[k % 3]:
                    vals[campo] = st.number_input(
                        f"{nutrients.nome_de(campo)} ({nutrients.unidade_de(campo)})",
                        0.0, step=0.5, key=f"novosup_{campo}")
            if st.form_submit_button(_t("Criar suplemento", "Create supplement"), type="primary"):
                if not nome_sup.strip():
                    st.error(_t("Dá um nome ao suplemento.", "Give the supplement a name."))
                else:
                    db.criar_suplemento(uid, nome_sup.strip(),
                                        {c: v for c, v in vals.items() if v > 0})
                    st.success(_t("Criado! Já o podes escolher na lista de suplementos acima.",
                                  "Created! You can now pick it in the supplements list above."))
                    st.rerun()

    notas = []
    if perfil.get("suplementos"):
        nut = db.suplementos_nutrientes(uid)
        if nut:
            notas.append("💊 **" + _t("Suplementos", "Supplements") + ":** " + " · ".join(
                f"{nutrients.nome_de(c)} +{v:.0f} {nutrients.unidade_de(c)}" for c, v in nut.items()))
    if perfil.get("sol_habitual") and sol.vit_d(perfil["sol_habitual"]):
        notas.append("☀️ **" + _t("Sol", "Sun") + ":** "
                     + _t(f"+{sol.vit_d(perfil['sol_habitual']):.0f} µg de vitamina D/dia",
                          f"+{sol.vit_d(perfil['sol_habitual']):.0f} µg vitamin D/day"))
    for nota in notas:
        st.caption(nota)
