"""Os meus alimentos — criar alimentos próprios e receitas reutilizáveis."""
import streamlit as st

from core import calc, db, i18n, nutrients
from views import builder, components, tema

_t = i18n.t
# (chave, unidade) — o rótulo vem de nutrients.nome_de para ficar traduzido
_MACROS = [("kcal", "kcal"), ("proteina_g", "g"), ("hidratos_g", "g"),
           ("gordura_g", "g"), ("fibra_g", "g"), ("acucar_g", "g")]


def mostrar():
    tema.cabecalho("🥣", i18n.t("Os meus alimentos", "My foods"),
                   i18n.t("Cria os teus próprios alimentos e receitas para usar nas refeições",
                          "Create your own foods and recipes to use in meals"))

    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid)
    alvos = calc.alvos_diarios(perfil) if perfil else None
    sexo = perfil["sexo"] if perfil else None

    tab_simples, tab_receita, tab_lista = st.tabs(
        [_t("➕ Alimento simples", "➕ Simple food"),
         _t("🍲 Receita (juntar ingredientes)", "🍲 Recipe (combine ingredients)"),
         _t("📋 Os que já tenho", "📋 The ones I have")])

    # ---- Alimento simples ----
    with tab_simples:
        st.caption(_t("Para um produto que conheces (ex.: o teu batido, um pão específico). "
                      "Indica os valores de **uma porção** — a app trata do resto.",
                      "For a product you know (e.g. your shake, a specific bread). "
                      "Enter the values for **one portion** — the app handles the rest."))
        with st.form("novo_simples"):
            nome = st.text_input(_t("Nome do alimento", "Food name"),
                                 placeholder=_t("Ex.: Batido proteico caseiro",
                                                "E.g.: Homemade protein shake"))
            gramas = st.number_input(_t("Quanto pesa 1 porção (g/ml)",
                                        "How much does 1 portion weigh (g/ml)"),
                                     1.0, 2000.0, 100.0, step=10.0)
            st.markdown("**" + _t("Valores nessa porção:", "Values in that portion:") + "**")
            cols = st.columns(3)
            vals = {}
            for k, (campo, unidade) in enumerate(_MACROS):
                with cols[k % 3]:
                    vals[campo] = st.number_input(
                        f"{nutrients.nome_de(campo)} ({unidade})", 0.0, step=1.0, key=f"s_{campo}")
            with st.expander(_t("➕ Adicionar vitaminas/minerais (opcional)",
                                "➕ Add vitamins/minerals (optional)")):
                cols_m = st.columns(3)
                extras = [c for c in nutrients.CAMPOS_NUTRIENTES
                          if c not in dict((m[0], 1) for m in _MACROS)]
                for k, campo in enumerate(nutrients.ordenar(extras)):
                    with cols_m[k % 3]:
                        vals[campo] = st.number_input(
                            f"{nutrients.nome_de(campo)} ({nutrients.unidade_de(campo)})",
                            0.0, step=0.5, key=f"s_{campo}")
            if st.form_submit_button(_t("💾 Criar alimento", "💾 Create food"), type="primary"):
                if not nome.strip():
                    st.error(_t("Dá um nome ao alimento.", "Give the food a name."))
                else:
                    por_100g = {c: v / gramas * 100 for c, v in vals.items()}
                    rotulo = "1 porção"
                    db.criar_alimento(uid, nome.strip(), por_100g, [[rotulo, round(gramas)]])
                    st.success(_t(f"✅ «{nome}» criado! Já aparece em 🍎 Alimentos → ⭐ Os meus.",
                                  f"✅ «{nome}» created! It now appears in 🍎 Foods → ⭐ Mine."))

    # ---- Receita (juntar ingredientes) ----
    with tab_receita:
        st.caption(_t("Junta ingredientes (como no Registar), diz quantas doses rende, "
                      "e guardas a receita inteira como um alimento próprio.",
                      "Combine ingredients (like in Log), say how many servings it yields, "
                      "and save the whole recipe as your own food."))
        receita = st.session_state.setdefault("receita_cesto", [])
        builder.adicionar_alimento(receita, "rec", db.obter_definicao("off_pais", "pt"), uid)

        if receita:
            st.markdown("**" + _t("Ingredientes da receita:", "Recipe ingredients:") + "**")
            builder.mostrar_itens(receita, "rec", sexo, alvos)
            totais = builder.totais(receita)
            gramas_total = sum(i["gramas"] for i in receita)
            st.markdown(f"**{_t('Receita inteira:', 'Whole recipe:')}** {totais['kcal']:.0f} kcal · "
                        f"{gramas_total:.0f} g {_t('no total', 'in total')}")
            with st.form("nova_receita"):
                nome = st.text_input(_t("Nome da receita", "Recipe name"),
                                     placeholder=_t("Ex.: Sopa da avó", "E.g.: Grandma's soup"))
                doses = st.number_input(_t("Quantas doses/porções rende?",
                                           "How many servings does it yield?"), 1, 50, 4)
                if st.form_submit_button(_t("💾 Guardar receita", "💾 Save recipe"), type="primary"):
                    if not nome.strip():
                        st.error(_t("Dá um nome à receita.", "Give the recipe a name."))
                    else:
                        por_100g = {c: v / gramas_total * 100 for c, v in totais.items()}
                        g_dose = round(gramas_total / doses)
                        db.criar_alimento(uid, nome.strip(), por_100g, [["1 dose", g_dose]])
                        st.session_state["receita_cesto"] = []
                        st.success(_t(f"✅ Receita «{nome}» guardada! 1 dose ≈ {g_dose} g. "
                                      "Já aparece em 🍎 Alimentos → ⭐ Os meus.",
                                      f"✅ Recipe «{nome}» saved! 1 serving ≈ {g_dose} g. "
                                      "It now appears in 🍎 Foods → ⭐ Mine."))
                        st.rerun()
        else:
            st.caption(_t("Adiciona ingredientes acima para criar a receita.",
                          "Add ingredients above to create the recipe."))

    # ---- Lista dos que já tenho ----
    with tab_lista:
        meus = db.listar_alimentos_custom(uid)
        if not meus:
            st.caption(_t("Ainda não criaste alimentos próprios.",
                          "You haven't created any foods of your own yet."))
        for alimento in meus:
            rotulo, g = alimento["porcoes"][0]
            nut = nutrients.escalar(alimento["por_100g"], g)
            c1, c2 = st.columns([6, 1])
            with c1.popover(f"🥣 {alimento['nome']} ({rotulo}, {g} g) — {nut['kcal']:.0f} kcal"):
                st.markdown(components.lista_nutrientes(nut, sexo, alvos))
            if c2.button("🗑️", key=f"del_{alimento['id']}", help=_t("Apagar", "Delete")):
                db.apagar_alimento(alimento["id"])
                st.rerun()
