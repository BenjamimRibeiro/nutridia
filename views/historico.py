"""Histórico — refeições passadas (editáveis), evolução de calorias, água e peso."""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from core import calc, db, nutrients
from views import builder, tema

_CAMPOS_SIMPLES = ["kcal", "proteina_g", "hidratos_g", "gordura_g", "fibra_g", "acucar_g"]


def _editor_refeicao(ref: dict, pais: str, sexo: str | None, alvos: dict | None, uid) -> None:
    """Edita uma refeição guardada: adicionar/remover alimentos (igual ao Registar)."""
    rid = ref["id"]
    chave = f"edit_cesto_{rid}"
    if chave not in st.session_state:
        # carrega os itens guardados (cópia) para um cesto editável
        st.session_state[chave] = [dict(i) for i in (ref.get("itens") or [])]
    cesto = st.session_state[chave]

    novo_nome = st.text_input("Nome da refeição", ref["nome"], key=f"en_{rid}")

    if not ref.get("itens"):
        st.info("Esta refeição antiga não tinha lista de alimentos. Adiciona os alimentos "
                "abaixo para a reconstruíres — os totais passam a vir dos alimentos.")

    st.markdown("**Adicionar mais alimentos:**")
    builder.adicionar_alimento(cesto, f"e{rid}", pais, uid)

    if cesto:
        st.markdown("**Alimentos nesta refeição** (🗑️ remove):")
        builder.mostrar_itens(cesto, f"e{rid}", sexo, alvos)
        totais = builder.totais(cesto)
        st.markdown(f"**Novo total:** {totais['kcal']:.0f} kcal · "
                    f"{totais['proteina_g']:.0f} g proteína")

    col1, col2 = st.columns(2)
    if col1.button("💾 Guardar alterações", key=f"sv_{rid}", type="primary"):
        if cesto:
            db.atualizar_refeicao(rid, novo_nome.strip() or ref["nome"],
                                  builder.totais(cesto), list(cesto))
        elif ref.get("itens"):
            st.warning("A refeição ficaria sem alimentos. Adiciona pelo menos um, "
                       "ou apaga a refeição.")
            return
        else:
            # refeição antiga sem itens e sem alterações de alimentos: só renomeia
            db.atualizar_refeicao(rid, novo_nome.strip() or ref["nome"], ref["nutrientes"])
        st.session_state.pop(chave, None)
        st.session_state.pop(f"e{rid}_res", None)
        st.success("Refeição atualizada!")
        st.rerun()
    if col2.button("Cancelar", key=f"cl_{rid}"):
        st.session_state.pop(chave, None)
        st.rerun()


def mostrar():
    tema.cabecalho("📅", "Histórico",
                   "Vê, corrige e acompanha a tua evolução ao longo do tempo")

    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid)
    alvos = calc.alvos_diarios(perfil) if perfil else None
    sexo = perfil["sexo"] if perfil else None
    pais = db.obter_definicao("off_pais", "pt")

    # ---- Refeições de um dia ----
    dia_escolhido = st.date_input("Ver refeições do dia", value=date.today(),
                                  max_value=date.today(), format="DD/MM/YYYY")
    dia_str = dia_escolhido.strftime("%Y-%m-%d")
    refeicoes = db.refeicoes_do_dia(uid, dia_str)

    if not refeicoes:
        st.caption("Sem refeições registadas neste dia.")
    for ref in refeicoes:
        n = ref["nutrientes"]
        with st.expander(f"{ref['hora']} — {ref['nome']} ({n.get('kcal', 0):.0f} kcal)"):
            if ref["foto_path"]:
                try:
                    st.image(ref["foto_path"], width=300)
                except Exception:
                    pass
            if ref.get("itens"):
                st.markdown("**Alimentos:** " + " · ".join(
                    f"{i['nome']} ({i['gramas']:.0f} g)" for i in ref["itens"]))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Proteína", f"{n.get('proteina_g', 0):.0f} g")
            c2.metric("Hidratos", f"{n.get('hidratos_g', 0):.0f} g")
            c3.metric("Gordura", f"{n.get('gordura_g', 0):.0f} g")
            c4.metric("Fibra", f"{n.get('fibra_g', 0):.0f} g")
            if st.toggle("✏️ Editar esta refeição", key=f"editar_tg_{ref['id']}"):
                _editor_refeicao(ref, pais, sexo, alvos, uid)
            if st.button("🗑️ Apagar esta refeição", key=f"apagar_{ref['id']}"):
                db.apagar_refeicao(ref["id"])
                st.rerun()

    # ---- Evolução últimos 14 dias ----
    st.divider()
    st.subheader("Últimos 14 dias")
    dias = [(date.today() - timedelta(days=i)) for i in range(13, -1, -1)]
    linhas = []
    for d in dias:
        totais = db.totais_do_dia(uid, d.strftime("%Y-%m-%d"))
        linhas.append({"Dia": d.strftime("%d/%m"),
                       "Calorias": round(totais.get("kcal", 0)),
                       "Proteína (g)": round(totais.get("proteina_g", 0)),
                       "Água (ml)": round(totais.get("agua_ml", 0))})
    df = pd.DataFrame(linhas).set_index("Dia")

    if df["Calorias"].sum() == 0:
        st.caption("Ainda não há dados suficientes — começa a registar refeições!")
    else:
        st.markdown("**Calorias por dia**" + (f" (alvo: {alvos['kcal']} kcal)" if alvos else ""))
        st.bar_chart(df["Calorias"], color="#5BA150")
        st.markdown("**Proteína por dia (g)**")
        st.bar_chart(df["Proteína (g)"], color="#2E7D4F")

    # ---- Peso ----
    st.divider()
    st.subheader("⚖️ Peso")
    c1, c2 = st.columns([1, 2])
    with c1:
        novo_peso = st.number_input("Peso de hoje (kg)", 30.0, 250.0,
                                    float(perfil["peso_kg"]) if perfil else 70.0, step=0.1)
        if st.button("Registar peso"):
            db.registar_peso(uid, novo_peso)
            if perfil:
                db.guardar_perfil(uid, perfil["sexo"], perfil["idade"], novo_peso,
                                  perfil["altura_cm"], perfil["atividade"],
                                  perfil["objetivo"], perfil["ritmo_kg_semana"],
                                  perfil.get("peso_alvo_kg"))
            st.success("Peso registado (e perfil atualizado)!")
            st.rerun()
    with c2:
        historico = db.historico_peso(uid)
        if len(historico) >= 2:
            df_peso = pd.DataFrame(historico)
            df_peso["data"] = pd.to_datetime(df_peso["data"])
            st.line_chart(df_peso.set_index("data")["kg"], color="#2E7D4F")
        else:
            st.caption("Regista o peso regularmente (ex.: 1x por semana, em jejum) "
                       "para veres aqui a tua evolução.")
