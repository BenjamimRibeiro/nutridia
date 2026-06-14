"""Histórico — refeições passadas (editáveis), evolução de calorias, água e peso."""
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from core import calc, db, exercicios, foods, i18n, momentos, nutrients
from views import builder, tema

_t = i18n.t
_CAMPOS_SIMPLES = ["kcal", "proteina_g", "hidratos_g", "gordura_g", "fibra_g", "acucar_g"]


def _editor_refeicao(ref: dict, pais: str, sexo: str | None, alvos: dict | None, uid) -> None:
    """Edita uma refeição guardada: adicionar/remover alimentos (igual ao Registar)."""
    rid = ref["id"]
    chave = f"edit_cesto_{rid}"
    if chave not in st.session_state:
        # carrega os itens guardados (cópia) para um cesto editável
        st.session_state[chave] = [dict(i) for i in (ref.get("itens") or [])]
    cesto = st.session_state[chave]

    cn, cm = st.columns([2, 1])
    novo_nome = cn.text_input(_t("Nome da refeição", "Meal name"), ref["nome"], key=f"en_{rid}")
    mom_atual = ref.get("momento")
    novo_momento = cm.selectbox(
        _t("Momento", "Time of day"), momentos.MOMENTOS, key=f"em_{rid}",
        format_func=momentos.nome,
        index=momentos.MOMENTOS.index(mom_atual) if mom_atual in momentos.MOMENTOS else 0)

    if not ref.get("itens"):
        st.info(_t("Esta refeição antiga não tinha lista de alimentos. Adiciona os alimentos "
                   "abaixo para a reconstruíres — os totais passam a vir dos alimentos.",
                   "This older meal had no food list. Add the foods below to rebuild it — "
                   "the totals will then come from the foods."))

    st.markdown("**" + _t("Adicionar mais alimentos:", "Add more foods:") + "**")
    builder.adicionar_alimento(cesto, f"e{rid}", pais, uid)

    if cesto:
        st.markdown("**" + _t("Alimentos nesta refeição", "Foods in this meal")
                    + "** (🗑️ " + _t("remove", "remove") + "):")
        builder.mostrar_itens(cesto, f"e{rid}", sexo, alvos)
        totais = builder.totais(cesto)
        st.markdown(f"**{_t('Novo total:', 'New total:')}** {totais['kcal']:.0f} kcal · "
                    f"{totais['proteina_g']:.0f} g {_t('proteína', 'protein')}")

    col1, col2 = st.columns(2)
    if col1.button(_t("💾 Guardar alterações", "💾 Save changes"), key=f"sv_{rid}", type="primary"):
        if cesto:
            db.atualizar_refeicao(rid, novo_nome.strip() or ref["nome"],
                                  builder.totais(cesto), list(cesto), momento=novo_momento)
        elif ref.get("itens"):
            st.warning(_t("A refeição ficaria sem alimentos. Adiciona pelo menos um, "
                          "ou apaga a refeição.",
                          "The meal would have no foods. Add at least one, or delete the meal."))
            return
        else:
            # refeição antiga sem itens e sem alterações de alimentos: só renomeia
            db.atualizar_refeicao(rid, novo_nome.strip() or ref["nome"], ref["nutrientes"],
                                  momento=novo_momento)
        st.session_state.pop(chave, None)
        st.session_state.pop(f"e{rid}_res", None)
        st.success(_t("Refeição atualizada!", "Meal updated!"))
        st.rerun()
    if col2.button(_t("Cancelar", "Cancel"), key=f"cl_{rid}"):
        st.session_state.pop(chave, None)
        st.rerun()


def mostrar():
    tema.cabecalho("📅", i18n.t("Histórico", "History"),
                   i18n.t("Vê, corrige e acompanha a tua evolução ao longo do tempo",
                          "See, edit and track your progress over time"))

    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid)
    alvos = calc.alvos_diarios(perfil) if perfil else None
    sexo = perfil["sexo"] if perfil else None
    pais = db.obter_definicao("off_pais", "pt")

    # ---- Refeições de um dia ----
    dia_escolhido = st.date_input(_t("Ver refeições do dia", "View meals from day"),
                                  value=date.today(),
                                  max_value=date.today(), format="DD/MM/YYYY")
    dia_str = dia_escolhido.strftime("%Y-%m-%d")
    refeicoes = db.refeicoes_do_dia(uid, dia_str)

    if not refeicoes:
        st.caption(_t("Sem refeições registadas neste dia.", "No meals logged on this day."))
    for ref in refeicoes:
        n = ref["nutrientes"]
        mom = ref.get("momento")
        prefixo = f"{momentos.emoji(mom)} {momentos.nome(mom)} · " if mom else ""
        with st.expander(f"{prefixo}{ref['hora']} — {ref['nome']} ({n.get('kcal', 0):.0f} kcal)"):
            if ref["foto_path"]:
                try:
                    st.image(ref["foto_path"], width=300)
                except Exception:
                    pass
            if ref.get("itens"):
                st.markdown("**" + _t("Alimentos:", "Foods:") + "** " + " · ".join(
                    f"{foods.nome(i['nome'])} ({i['gramas']:.0f} g)" for i in ref["itens"]))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(_t("Proteína", "Protein"), f"{n.get('proteina_g', 0):.0f} g")
            c2.metric(_t("Hidratos", "Carbs"), f"{n.get('hidratos_g', 0):.0f} g")
            c3.metric(_t("Gordura", "Fat"), f"{n.get('gordura_g', 0):.0f} g")
            c4.metric(_t("Fibra", "Fibre"), f"{n.get('fibra_g', 0):.0f} g")
            if st.toggle(_t("✏️ Editar esta refeição", "✏️ Edit this meal"),
                         key=f"editar_tg_{ref['id']}"):
                _editor_refeicao(ref, pais, sexo, alvos, uid)
            if st.button(_t("🗑️ Apagar esta refeição", "🗑️ Delete this meal"),
                         key=f"apagar_{ref['id']}"):
                db.apagar_refeicao(ref["id"])
                st.rerun()

    exs = db.exercicios_do_dia(uid, dia_str)
    if exs:
        st.markdown("**" + _t("🏃 Exercício neste dia:", "🏃 Exercise on this day:") + "** "
                    + " · ".join(
            f"{exercicios.nome(e['nome'])} ({e['duracao_min']} min, {e['kcal']} kcal)"
            for e in exs))

    # ---- Evolução últimos 14 dias ----
    st.divider()
    st.subheader(_t("Últimos 14 dias", "Last 14 days"))
    dias = [(date.today() - timedelta(days=i)) for i in range(13, -1, -1)]
    linhas = []
    col_dia = _t("Dia", "Day")
    col_cal = _t("Calorias", "Calories")
    col_prot = _t("Proteína (g)", "Protein (g)")
    for d in dias:
        totais = db.totais_do_dia(uid, d.strftime("%Y-%m-%d"))
        linhas.append({col_dia: d.strftime("%d/%m"),
                       col_cal: round(totais.get("kcal", 0)),
                       col_prot: round(totais.get("proteina_g", 0)),
                       "agua": round(totais.get("agua_ml", 0))})
    df = pd.DataFrame(linhas).set_index(col_dia)

    if df[col_cal].sum() == 0:
        st.caption(_t("Ainda não há dados suficientes — começa a registar refeições!",
                      "Not enough data yet — start logging meals!"))
    else:
        st.markdown("**" + _t("Calorias por dia", "Calories per day") + "**"
                    + (f" ({_t('alvo', 'target')}: {alvos['kcal']} kcal)" if alvos else ""))
        st.bar_chart(df[col_cal], color="#5BA150")
        st.markdown("**" + _t("Proteína por dia (g)", "Protein per day (g)") + "**")
        st.bar_chart(df[col_prot], color="#2E7D4F")

    # ---- Peso ----
    st.divider()
    st.subheader(_t("⚖️ Peso", "⚖️ Weight"))
    c1, c2 = st.columns([1, 2])
    with c1:
        novo_peso = st.number_input(_t("Peso de hoje (kg)", "Today's weight (kg)"), 30.0, 250.0,
                                    float(perfil["peso_kg"]) if perfil else 70.0, step=0.1)
        if st.button(_t("Registar peso", "Log weight")):
            db.registar_peso(uid, novo_peso)
            if perfil:
                db.guardar_perfil(uid, perfil["sexo"], perfil["idade"], novo_peso,
                                  perfil["altura_cm"], perfil["atividade"],
                                  perfil["objetivo"], perfil["ritmo_kg_semana"],
                                  perfil.get("peso_alvo_kg"))
            st.success(_t("Peso registado (e perfil atualizado)!",
                          "Weight logged (and profile updated)!"))
            st.rerun()
    with c2:
        historico = db.historico_peso(uid)
        if len(historico) >= 2:
            df_peso = pd.DataFrame(historico)
            df_peso["data"] = pd.to_datetime(df_peso["data"])
            st.line_chart(df_peso.set_index("data")["kg"], color="#2E7D4F")
        else:
            st.caption(_t("Regista o peso regularmente (ex.: 1x por semana, em jejum) "
                          "para veres aqui a tua evolução.",
                          "Log your weight regularly (e.g. once a week, fasted) "
                          "to see your progress here."))
