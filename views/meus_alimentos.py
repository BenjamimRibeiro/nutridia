"""Os meus alimentos — criar alimentos próprios e receitas reutilizáveis."""
import streamlit as st

from core import calc, db, nutrients
from views import builder, components, tema

_MACROS = [("kcal", "Calorias", "kcal"), ("proteina_g", "Proteína", "g"),
           ("hidratos_g", "Hidratos", "g"), ("gordura_g", "Gordura", "g"),
           ("fibra_g", "Fibra", "g"), ("acucar_g", "Açúcar", "g")]


def mostrar():
    tema.cabecalho("🥣", "Os meus alimentos",
                   "Cria os teus próprios alimentos e receitas para usar nas refeições")

    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid)
    alvos = calc.alvos_diarios(perfil) if perfil else None
    sexo = perfil["sexo"] if perfil else None

    tab_simples, tab_receita, tab_lista = st.tabs(
        ["➕ Alimento simples", "🍲 Receita (juntar ingredientes)", "📋 Os que já tenho"])

    # ---- Alimento simples ----
    with tab_simples:
        st.caption("Para um produto que conheces (ex.: o teu batido, um pão específico). "
                   "Indica os valores de **uma porção** — a app trata do resto.")
        with st.form("novo_simples"):
            nome = st.text_input("Nome do alimento", placeholder="Ex.: Batido proteico caseiro")
            gramas = st.number_input("Quanto pesa 1 porção (g/ml)", 1.0, 2000.0, 100.0, step=10.0)
            st.markdown("**Valores nessa porção:**")
            cols = st.columns(3)
            vals = {}
            for k, (campo, rotulo, unidade) in enumerate(_MACROS):
                with cols[k % 3]:
                    vals[campo] = st.number_input(f"{rotulo} ({unidade})", 0.0, step=1.0,
                                                  key=f"s_{campo}")
            with st.expander("➕ Adicionar vitaminas/minerais (opcional)"):
                cols_m = st.columns(3)
                extras = [c for c in nutrients.CAMPOS_NUTRIENTES
                          if c not in dict((m[0], 1) for m in _MACROS)]
                for k, campo in enumerate(nutrients.ordenar(extras)):
                    with cols_m[k % 3]:
                        vals[campo] = st.number_input(
                            f"{nutrients.nome_de(campo)} ({nutrients.unidade_de(campo)})",
                            0.0, step=0.5, key=f"s_{campo}")
            if st.form_submit_button("💾 Criar alimento", type="primary"):
                if not nome.strip():
                    st.error("Dá um nome ao alimento.")
                else:
                    por_100g = {c: v / gramas * 100 for c, v in vals.items()}
                    rotulo = "1 porção"
                    db.criar_alimento(uid, nome.strip(), por_100g, [[rotulo, round(gramas)]])
                    st.success(f"✅ «{nome}» criado! Já aparece em 🍎 Alimentos → ⭐ Os meus.")

    # ---- Receita (juntar ingredientes) ----
    with tab_receita:
        st.caption("Junta ingredientes (como no Registar), diz quantas doses rende, "
                   "e guardas a receita inteira como um alimento próprio.")
        receita = st.session_state.setdefault("receita_cesto", [])
        builder.adicionar_alimento(receita, "rec", db.obter_definicao("off_pais", "pt"), uid)

        if receita:
            st.markdown("**Ingredientes da receita:**")
            builder.mostrar_itens(receita, "rec", sexo, alvos)
            totais = builder.totais(receita)
            gramas_total = sum(i["gramas"] for i in receita)
            st.markdown(f"**Receita inteira:** {totais['kcal']:.0f} kcal · "
                        f"{gramas_total:.0f} g no total")
            with st.form("nova_receita"):
                nome = st.text_input("Nome da receita", placeholder="Ex.: Sopa da avó")
                doses = st.number_input("Quantas doses/porções rende?", 1, 50, 4)
                if st.form_submit_button("💾 Guardar receita", type="primary"):
                    if not nome.strip():
                        st.error("Dá um nome à receita.")
                    else:
                        por_100g = {c: v / gramas_total * 100 for c, v in totais.items()}
                        g_dose = round(gramas_total / doses)
                        db.criar_alimento(uid, nome.strip(), por_100g, [["1 dose", g_dose]])
                        st.session_state["receita_cesto"] = []
                        st.success(f"✅ Receita «{nome}» guardada! 1 dose ≈ {g_dose} g. "
                                   "Já aparece em 🍎 Alimentos → ⭐ Os meus.")
                        st.rerun()
        else:
            st.caption("Adiciona ingredientes acima para criar a receita.")

    # ---- Lista dos que já tenho ----
    with tab_lista:
        meus = db.listar_alimentos_custom(uid)
        if not meus:
            st.caption("Ainda não criaste alimentos próprios.")
        for alimento in meus:
            rotulo, g = alimento["porcoes"][0]
            nut = nutrients.escalar(alimento["por_100g"], g)
            c1, c2 = st.columns([6, 1])
            with c1.popover(f"🥣 {alimento['nome']} ({rotulo}, {g} g) — {nut['kcal']:.0f} kcal"):
                st.markdown(components.lista_nutrientes(nut, sexo, alvos))
            if c2.button("🗑️", key=f"del_{alimento['id']}", help="Apagar"):
                db.apagar_alimento(alimento["id"])
                st.rerun()
