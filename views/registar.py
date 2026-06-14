"""Registar refeição — alimentos comuns/próprios ou pesquisa OFF, favoritos e
repetição de refeições. Tu só dizes o quê e quanto; a app calcula os nutrientes."""
from datetime import date, datetime, time

import streamlit as st

from core import calc, db, i18n, momentos, nutrients
from views import builder, components, tema


def _carregar(cesto: list, itens: list) -> None:
    """Substitui o cesto pelos itens de um favorito/refeição (cópia)."""
    cesto.clear()
    cesto.extend(dict(i) for i in itens)


def mostrar():
    tema.cabecalho("🍽️", i18n.t("Registar refeição", "Log a meal"),
                   i18n.t("Escolhe os alimentos e a porção — a app trata das calorias e nutrientes",
                          "Pick the foods and portion — the app handles calories and nutrients"))

    uid = st.session_state.get("uid")
    cesto = st.session_state.setdefault("cesto", [])
    pais = db.obter_definicao("off_pais", "pt")
    perfil = db.obter_perfil(uid)
    alvos = calc.alvos_diarios(perfil) if perfil else None
    sexo = perfil["sexo"] if perfil else None

    _t = i18n.t
    # ---- Atalhos: favoritos e repetir ----
    favoritos = db.listar_favoritos(uid)
    dias = db.dias_com_registos(uid, 14)
    if favoritos or dias:
        with st.expander(_t("⚡ Favoritos e repetir refeições", "⚡ Favourites and repeat meals"),
                         expanded=not cesto):
            if favoritos:
                st.markdown(_t("**Os teus favoritos** (carrega para o cesto):",
                               "**Your favourites** (load into the basket):"))
                cols = st.columns(3)
                for k, fav in enumerate(favoritos):
                    with cols[k % 3]:
                        if st.button(f"⭐ {fav['nome']}", key=f"fav_{fav['id']}",
                                     use_container_width=True):
                            _carregar(cesto, fav["itens"])
                            st.rerun()
                        if st.button("🗑️", key=f"favdel_{fav['id']}",
                                     help=_t("Apagar favorito", "Delete favourite")):
                            db.apagar_favorito(fav["id"])
                            st.rerun()
            if dias:
                st.markdown(_t("**Copiar uma refeição de outro dia:**",
                               "**Copy a meal from another day:**"))
                dia_sel = st.selectbox(_t("Dia", "Day"), dias, format_func=lambda d:
                                       datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y"),
                                       key="copiar_dia")
                refs = [r for r in db.refeicoes_do_dia(uid, dia_sel) if r.get("itens")]
                if refs:
                    idx = st.selectbox(_t("Refeição", "Meal"), range(len(refs)),
                                       format_func=lambda i: f"{refs[i]['hora']} — {refs[i]['nome']}",
                                       key="copiar_ref")
                    if st.button(_t("📋 Copiar para o cesto", "📋 Copy to basket")):
                        _carregar(cesto, refs[idx]["itens"])
                        st.rerun()
                else:
                    st.caption(_t("Esse dia não tem refeições com lista de alimentos para copiar.",
                                  "That day has no meals with a food list to copy."))

    st.subheader(_t("1️⃣ Adicionar alimentos", "1️⃣ Add foods"))
    builder.adicionar_alimento(cesto, "reg", pais, uid)

    st.divider()
    st.subheader(_t("2️⃣ A tua refeição", "2️⃣ Your meal"))
    if not cesto:
        st.caption(_t("Ainda não adicionaste nada. Usa os atalhos ou os separadores acima. 👆",
                      "Nothing added yet. Use the shortcuts or the tabs above. 👆"))
        return

    st.markdown(_t("**Cada alimento dá-te** (clica em 🔍 para o detalhe completo):",
                   "**Each food gives you** (click 🔍 for full detail):"))
    builder.mostrar_itens(cesto, "reg", sexo, alvos)
    totais = builder.totais(cesto)

    st.markdown(_t(f"### Total da refeição: {totais['kcal']:.0f} kcal",
                   f"### Meal total: {totais['kcal']:.0f} kcal"))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(_t("Proteína", "Protein"), f"{totais['proteina_g']:.0f} g")
    c2.metric(_t("Hidratos", "Carbs"), f"{totais['hidratos_g']:.0f} g")
    c3.metric(_t("Gordura", "Fat"), f"{totais['gordura_g']:.0f} g")
    c4.metric(_t("Fibra", "Fibre"), f"{totais['fibra_g']:.0f} g")

    st.markdown(_t("**O que esta refeição te dá no geral:**", "**What this meal gives overall:**"))
    if perfil:
        components.tabela_cobertura(totais, sexo, alvos, apenas_consumidos=True)
    else:
        st.markdown(components.lista_nutrientes(totais))
        st.caption(_t("Preenche o Perfil para veres a % dos teus alvos diários.",
                      "Fill in your Profile to see the % of your daily targets."))

    nome_sugerido = ", ".join(i["nome"].split(" — ")[0] for i in cesto[:3])
    cn, cm = st.columns([2, 1])
    nome = cn.text_input(_t("Nome da refeição", "Meal name"), nome_sugerido)
    momento = cm.selectbox(_t("Momento do dia", "Time of day"), momentos.MOMENTOS,
                           index=momentos.MOMENTOS.index(momentos.sugerir()),
                           format_func=momentos.nome)

    # ---- Quando comeste? (permite registar refeições de outro dia/hora) ----
    with st.expander(_t("🕒 Comeste noutra altura? (por defeito: agora)",
                        "🕒 Eaten at another time? (default: now)")):
        st.caption(_t("Esqueceste-te de registar ontem? Escolhe o dia e a hora reais — "
                      "a refeição vai parar ao sítio certo no Painel e no Histórico.",
                      "Forgot to log yesterday? Pick the real day and time — the meal will "
                      "land in the right place on the Dashboard and History."))
        cd, ch = st.columns(2)
        dia_ref = cd.date_input(_t("Dia da refeição", "Meal day"), value=date.today(),
                                max_value=date.today(), format="DD/MM/YYYY", key="reg_dia")
        hora_ref = ch.time_input(_t("Hora", "Time"), value=datetime.now().time().replace(second=0),
                                 step=300, key="reg_hora")
    dia_str = dia_ref.strftime("%Y-%m-%d")
    hora_str = hora_ref.strftime("%H:%M")
    if dia_ref != date.today():
        st.info(_t(f"📅 Esta refeição será registada em **{dia_ref.strftime('%d/%m/%Y')}** "
                   f"às **{hora_str}**.",
                   f"📅 This meal will be logged on **{dia_ref.strftime('%d/%m/%Y')}** "
                   f"at **{hora_str}**."))

    foto_bytes = None
    with st.expander(_t("📷 Adicionar foto (opcional)", "📷 Add a photo (optional)")):
        foto = st.file_uploader(_t("Foto da refeição", "Meal photo"),
                                type=["jpg", "jpeg", "png", "webp"],
                                key="reg_foto", label_visibility="collapsed")
        if foto:
            foto_bytes = foto.getvalue()
            st.image(foto_bytes, width=220)

    c1, c2 = st.columns(2)
    if c1.button(_t("💾 Guardar refeição", "💾 Save meal"), type="primary", use_container_width=True):
        db.guardar_refeicao(uid, nome.strip() or "Refeição", totais, itens=list(cesto),
                            momento=momento, foto_bytes=foto_bytes, dia=dia_str, hora=hora_str)
        st.session_state["cesto"] = []
        st.session_state.pop("reg_res", None)
        st.session_state.pop("reg_foto", None)
        if dia_ref != date.today():
            st.success(_t(f"✅ «{nome}» guardada em {dia_ref.strftime('%d/%m/%Y')}! "
                          "Vê no Histórico.",
                          f"✅ “{nome}” saved on {dia_ref.strftime('%d/%m/%Y')}! See it in History."))
        else:
            st.success(_t(f"✅ «{nome}» guardada! Vê o impacto no Painel.",
                          f"✅ “{nome}” saved! See the impact on the Dashboard."))
        st.balloons()
        st.rerun()
    if c2.button(_t("⭐ Guardar como favorito", "⭐ Save as favourite"), use_container_width=True,
                 help=_t("Guarda esta combinação para repetir com 1 clique",
                         "Save this combo to repeat in 1 click")):
        db.guardar_favorito(uid, nome.strip() or "Favorito", list(cesto))
        st.success(_t(f"⭐ «{nome}» guardado nos favoritos!", f"⭐ “{nome}” saved to favourites!"))
