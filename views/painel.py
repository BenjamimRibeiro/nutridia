"""Painel — resumo do dia: calorias, macros, água e pontuações de bem-estar."""
from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from core import (calc, db, doenca, exercicios, i18n, metas, momentos, nutrients, scores,
                  sugestoes)
from views import components, tema

_t = i18n.t

_PARAGENS = [(0, (217, 83, 79)), (28, (232, 116, 59)), (52, (232, 194, 32)),
             (76, (143, 185, 90)), (100, (46, 125, 79))]
_GRADIENTE = ("linear-gradient(90deg,#D9534F 0%,#E8743B 28%,#E8C220 52%,"
              "#8FB95A 76%,#2E7D4F 100%)")


def _cor(valor: float) -> str:
    v = max(0, min(100, valor))
    for (p0, c0), (p1, c1) in zip(_PARAGENS, _PARAGENS[1:]):
        if v <= p1:
            t = (v - p0) / (p1 - p0) if p1 > p0 else 0
            r, g, b = (round(a + (c - a) * t) for a, c in zip(c0, c1))
            return f"#{r:02X}{g:02X}{b:02X}"
    return "#2E7D4F"


def _cartao_pontuacao(nome_key: str, valor: int) -> None:
    cor = _cor(valor)
    emoji = scores.PONTUACOES[nome_key]["emoji"]
    st.markdown(
        f"""<div title="{scores.descricao(nome_key)}" style="background:#FBFCF6;border-radius:14px;
        padding:12px 14px;box-shadow:0 2px 8px rgba(36,48,36,.07);margin-bottom:10px;">
        <div style="display:flex;justify-content:space-between;align-items:center;
        font-weight:800;font-size:15px;">
        <span>{emoji} {scores.nome(nome_key)}</span><span style="color:{cor};">{valor}%</span></div>
        <div style="position:relative;height:11px;border-radius:99px;background:#E3EAD9;
        overflow:hidden;margin:8px 0 7px;">
        <div style="position:absolute;inset:0;background:{_GRADIENTE};"></div>
        <div style="position:absolute;top:0;bottom:0;left:{max(valor, 2)}%;right:0;
        background:#E3EAD9;"></div></div>
        <div style="font-size:12.5px;color:#5d6b52;line-height:1.35;">
        🍴 {_t("Ajuda", "Helps")}: {scores.dica(nome_key)}</div></div>""",
        unsafe_allow_html=True,
    )


def _evolucao_pontuacoes(uid, alvos: dict, sexo: str) -> None:
    escolha = st.selectbox(_t("Pontuação", "Score"), list(scores.PONTUACOES),
                           format_func=lambda n: f"{scores.PONTUACOES[n]['emoji']} {scores.nome(n)}")
    linhas = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        dia_s = d.strftime("%Y-%m-%d")
        totais_dia = db.totais_do_dia(uid, dia_s)
        if totais_dia.get("kcal", 0) > 0:
            alvos_d = {**alvos, "kcal": alvos["kcal"] + db.exercicio_kcal_do_dia(uid, dia_s)}
            valor = scores.calcular(totais_dia, alvos_d, sexo)[escolha]
            linhas.append({"Dia": d.strftime("%d/%m"), "Pontuação": valor,
                           "cor": _cor(valor), "ordem": 6 - i})
    if len(linhas) < 2:
        st.caption(_t("Regista refeições em pelo menos 2 dias para veres a progressão. 📈",
                      "Log meals on at least 2 days to see the trend. 📈"))
        return
    df = pd.DataFrame(linhas)
    ordem_dias = df.sort_values("ordem")["Dia"].tolist()
    linha = alt.Chart(df).mark_line(color="#9AB88E", size=2.5).encode(
        x=alt.X("Dia:N", sort=ordem_dias, title=None),
        y=alt.Y("Pontuação:Q", scale=alt.Scale(domain=[0, 100]), title="%"))
    pontos = alt.Chart(df).mark_point(filled=True, size=140).encode(
        x=alt.X("Dia:N", sort=ordem_dias), y="Pontuação:Q",
        color=alt.Color("cor:N", scale=None),
        tooltip=[alt.Tooltip("Dia:N", title=_t("Dia", "Day")),
                 alt.Tooltip("Pontuação:Q", title=_t("Pontuação", "Score"), format=".0f")])
    st.altair_chart((linha + pontos).properties(height=220), use_container_width=True)


def _onboarding(uid, perfil) -> None:
    chave = f"onboarding_{uid}"
    if db.obter_definicao(chave) == "1":
        return
    tem_refeicao = bool(db.dias_com_registos(uid, 1))
    tem_extras = bool(perfil and (perfil.get("alergias") or perfil.get("suplementos")
                                  or perfil.get("sol_habitual")))
    with st.container(border=True):
        st.markdown(_t("### 👋 Bem-vindo ao NutriDia!", "### 👋 Welcome to NutriDia!"))
        st.markdown(_t("Em poucos passos ficas a usar tudo:", "A few steps to get going:"))
        st.markdown(f"{'✅' if perfil else '⬜'} " + _t(
            "**1.** Preenche o teu **Perfil** (sexo, peso, altura, objetivo)",
            "**1.** Fill in your **Profile** (sex, weight, height, goal)"))
        st.markdown(f"{'✅' if tem_extras else '⬜'} " + _t(
            "**2.** No Perfil, define **alergias, suplementos e sol** (opcional)",
            "**2.** In Profile, set **allergies, supplements and sun** (optional)"))
        st.markdown(f"{'✅' if tem_refeicao else '⬜'} " + _t(
            "**3.** Regista a tua **1ª refeição** em «Registar refeição»",
            "**3.** Log your **first meal** in “Log a meal”"))
        st.markdown("⬜ " + _t("**4.** Vê o teu **Progresso** e as pontuações de bem-estar",
                               "**4.** Check your **Progress** and wellbeing scores"))
        if st.button(_t("Já percebi, esconder ✨", "Got it, hide ✨")):
            db.guardar_definicao(chave, "1")
            st.rerun()


def mostrar():
    tema.cabecalho("📊", _t("O teu dia", "Your day"),
                   _t("Calorias, nutrientes e bem-estar de hoje num relance",
                      "Today's calories, nutrients and wellbeing at a glance"))

    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid)
    _onboarding(uid, perfil)
    if not perfil:
        st.info(_t("Preenche o teu **Perfil** (no menu lateral) para começar.",
                   "Fill in your **Profile** (in the side menu) to get started."))
        return

    hoje = date.today().strftime("%Y-%m-%d")
    alvos = calc.alvos_diarios(perfil)
    totais = db.totais_do_dia(uid, hoje)
    refeicoes = db.refeicoes_do_dia(uid, hoje)

    kcal_ex = db.exercicio_kcal_do_dia(uid, hoje)
    alvo_kcal = alvos["kcal"] + kcal_ex
    alvos_aj = {**alvos, "kcal": alvo_kcal}

    # ---- Como te sentes hoje? (modo doente) ----
    estado = db.obter_estado(uid, hoje)
    doente_inicial = estado["estado"] == "Doente"
    with st.expander(_t("🤒 Como te sentes hoje?", "🤒 How are you feeling today?"),
                     expanded=doente_inicial):
        doente = st.toggle(_t("Estou doente", "I'm sick"), value=doente_inicial, key="doente_tg")
        tipo = None
        if doente:
            idx = doenca.TIPOS.index(estado["tipo"]) if estado.get("tipo") in doenca.TIPOS else 0
            tipo = st.selectbox(_t("O que tens?", "What's wrong?"), doenca.TIPOS, index=idx,
                                key="doente_tipo", format_func=doenca.nome)
        novo = "Doente" if doente else "Saudável"
        if novo != estado["estado"] or (doente and tipo != estado.get("tipo")):
            db.definir_estado(uid, novo, tipo)
            estado = {"estado": novo, "tipo": tipo}
        if doente:
            c = doenca.conforto(tipo)
            st.info(_t(f"💛 As melhoras! Para **{doenca.nome(tipo).lower()}**, conforto à base de comida:",
                       f"💛 Get well soon! For a **{doenca.nome(tipo).lower()}**, food comfort:")
                    + f"\n\n🍲 **{_t('Come', 'Eat')}:** {c['alimentos']}\n\n"
                    f"✨ {c['nutrientes']}\n\n💡 {c['dica']}")
            st.caption(_t("Hoje a app não te martela com as metas — recupera com calma. "
                          "⚕️ Isto é conforto alimentar, não conselho médico; se persistir, "
                          "consulta um médico.",
                          "Today the app won't push you on your goals — recover gently. "
                          "⚕️ This is food comfort, not medical advice; if it persists, "
                          "see a doctor."))

    # ---- Sequência (streak) ----
    seq = metas.sequencia_atual(uid, alvos)
    if seq >= 2:
        st.markdown(_t(f"#### 🔥 Sequência de **{seq} dias** dentro do alvo — continua assim!",
                       f"#### 🔥 **{seq}-day** streak on target — keep it up!"))

    # ---- Calorias e macros ----
    st.subheader(_t("Calorias e macros", "Calories and macros"))
    col_kcal, col_prot, col_hid, col_gord = st.columns(4)
    objetivo_txt = {"Manter peso": _t("manter", "maintaining"),
                    "Emagrecer": _t("emagrecer", "losing weight"),
                    "Engordar / ganhar massa": _t("ganhar massa", "gaining muscle")}[perfil["objetivo"]]
    kcal = totais.get("kcal", 0)
    col_kcal.metric(_t("Calorias", "Calories"), f"{kcal:.0f} / {alvo_kcal}",
                    delta=f"{kcal - alvo_kcal:+.0f} kcal", delta_color="off",
                    help=_t(f"Alvo para {objetivo_txt}", f"Target for {objetivo_txt}"))
    col_prot.metric(_t("Proteína", "Protein"), f"{totais.get('proteina_g', 0):.0f} / {alvos['proteina_g']} g")
    col_hid.metric(_t("Hidratos", "Carbs"), f"{totais.get('hidratos_g', 0):.0f} / {alvos['hidratos_g']} g")
    col_gord.metric(_t("Gordura", "Fat"), f"{totais.get('gordura_g', 0):.0f} / {alvos['gordura_g']} g")
    if kcal_ex:
        st.caption(_t(f"🏃 Alvo base {alvos['kcal']} + {kcal_ex} kcal de exercício = "
                      f"**{alvo_kcal} kcal** disponíveis hoje.",
                      f"🏃 Base target {alvos['kcal']} + {kcal_ex} kcal from exercise = "
                      f"**{alvo_kcal} kcal** available today."))

    for chave, alvo in [("kcal", alvo_kcal), ("proteina_g", alvos["proteina_g"])]:
        fracao = min(totais.get(chave, 0) / alvo, 1.0) if alvo else 0
        st.progress(fracao, text=f"{nutrients.nome_de(chave)}: {fracao:.0%} {_t('do alvo', 'of target')}")

    # ---- Sugestão inteligente: o que comer a seguir ----
    if estado["estado"] != "Doente":
        sug = sugestoes.para_agora(totais, alvos_aj, perfil["sexo"],
                                   perfil.get("alergias", []), perfil.get("restricoes", []))
        if sug["saudaveis"] or sug["treat"]:
            with st.expander(_t("🤖 Sugestão: o que comer a seguir", "🤖 Suggestion: what to eat next"),
                             expanded=False):
                if sug["saudaveis"]:
                    st.markdown(_t(f"Tens ~**{sug['resto_kcal']:.0f} kcal** disponíveis. Opções "
                                   "saudáveis e variadas que te dão o que ainda falta hoje:",
                                   f"You have ~**{sug['resto_kcal']:.0f} kcal** left. Healthy, "
                                   "varied options that give you what's still missing today:"))
                    for s in sug["saudaveis"]:
                        ajuda = ", ".join(nutrients.nome_de(c) for c, _ in s["cobre"][:3])
                        st.markdown(f"- 🥗 **{s['nome']}** ({s['rotulo']}, {s['gramas']} g) → "
                                    + _t("bom para", "good for") + f" **{ajuda}** · {s['kcal']:.0f} kcal")
                if sug["treat"]:
                    tr = sug["treat"]
                    st.markdown(_t("😋 E se te apetecer algo bom (sabe sempre bem de vez em quando!): ",
                                   "😋 And if you fancy a treat (always nice now and then!): ")
                                + f"**{tr['nome']}** ({tr['rotulo']}, {tr['gramas']} g) · {tr['kcal']:.0f} kcal")
                st.caption(_t("Sugestões que respeitam as tuas alergias e preferências (Perfil).",
                              "Suggestions that respect your allergies and preferences (Profile)."))

    # ---- Água ----
    st.subheader(_t("💧 Água", "💧 Water"))
    agua = db.agua_do_dia(uid, hoje)
    st.progress(min(agua / alvos["agua_ml"], 1.0), text=f"{agua} / {alvos['agua_ml']} ml")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🥤 +250 ml"):
        db.adicionar_agua(uid, 250)
        st.rerun()
    if c2.button("🍶 +500 ml"):
        db.adicionar_agua(uid, 500)
        st.rerun()
    if c3.button("🫗 +1 L"):
        db.adicionar_agua(uid, 1000)
        st.rerun()
    if c4.button("↩️ -250 ml"):
        db.adicionar_agua(uid, -250)
        st.rerun()

    # ---- Exercício de hoje ----
    st.subheader(_t("🏃 Exercício de hoje", "🏃 Today's exercise"))
    ca, cb, cc = st.columns([2, 1, 1])
    atividade = ca.selectbox(_t("Atividade", "Activity"), list(exercicios.ATIVIDADES),
                             key="ex_at", format_func=exercicios.nome)
    minutos = cb.number_input(_t("Minutos", "Minutes"), 1, 600, 30, step=5, key="ex_min")
    kcal_est = exercicios.kcal(exercicios.ATIVIDADES[atividade], perfil["peso_kg"], minutos)
    cc.metric(_t("Gasto estimado", "Est. burn"), f"{kcal_est} kcal")
    if st.button(_t("➕ Registar exercício", "➕ Log exercise"), type="primary"):
        db.registar_exercicio(uid, atividade, minutos, kcal_est)
        st.rerun()
    exs = db.exercicios_do_dia(uid, hoje)
    for e in exs:
        c1, c2 = st.columns([6, 1])
        c1.markdown(f"🔥 **{exercicios.nome(e['nome'])}** — {e['duracao_min']} min · {e['kcal']} kcal")
        if c2.button("🗑️", key=f"exdel_{e['id']}", help=_t("Remover", "Remove")):
            db.apagar_exercicio(e["id"])
            st.rerun()
    if exs:
        st.caption(_t(f"Total queimado hoje: **{kcal_ex} kcal** — já somados ao teu alvo de calorias.",
                      f"Total burned today: **{kcal_ex} kcal** — already added to your calorie target."))

    # ---- Pontuações de bem-estar ----
    st.subheader(_t("Pontuações de bem-estar", "Wellbeing scores"))
    if not refeicoes:
        st.caption(_t("Regista a tua primeira refeição de hoje para veres as pontuações. 🍽️",
                      "Log your first meal today to see your scores. 🍽️"))
    else:
        pontuacoes = scores.calcular(totais, alvos_aj, perfil["sexo"])
        colunas = st.columns(3)
        for i, (nome_key, valor) in enumerate(pontuacoes.items()):
            with colunas[i % 3]:
                _cartao_pontuacao(nome_key, valor)
        st.caption(_t("As pontuações sobem ao longo do dia à medida que registas refeições — "
                      "valores baixos de manhã são normais. Passa o rato por cima de um cartão "
                      "para veres o que mede.",
                      "Scores rise through the day as you log meals — low values in the morning "
                      "are normal. Hover over a card to see what it measures."))
        with st.expander(_t("📈 Progressão das pontuações (últimos 7 dias)",
                            "📈 Score trend (last 7 days)")):
            _evolucao_pontuacoes(uid, alvos, perfil["sexo"])

    # ---- Nutrientes do dia (gráficos por grupo) ----
    st.subheader(_t("📈 Nutrientes do dia — alcançados e em falta",
                    "📈 Today's nutrients — reached and missing"))
    if not refeicoes:
        st.caption(_t("Regista refeições para preencheres estes gráficos.",
                      "Log meals to fill these charts."))
    else:
        components.graficos_cobertura(totais, perfil["sexo"], alvos_aj)
        with st.expander(_t("📋 Ver tabela detalhada", "📋 See detailed table")):
            components.tabela_cobertura(totais, perfil["sexo"], alvos_aj)

    # ---- Refeições de hoje (agrupadas por momento) ----
    st.subheader(_t(f"Refeições de hoje ({len(refeicoes)})", f"Today's meals ({len(refeicoes)})"))
    if not refeicoes:
        st.caption(_t("Ainda não registaste nada hoje.", "You haven't logged anything today."))
    else:
        st.caption(_t("✏️ Para corrigir quantidades ou apagar, vai ao **Histórico**.",
                      "✏️ To fix amounts or delete, go to **History**."))
        por_momento: dict[str, list] = {}
        for ref in refeicoes:
            por_momento.setdefault(ref.get("momento") or "Outras", []).append(ref)
        for momento in momentos.MOMENTOS + ["Outras"]:
            refs = por_momento.get(momento)
            if not refs:
                continue
            kcal_m = sum(r["nutrientes"].get("kcal", 0) for r in refs)
            st.markdown(f"**{momentos.emoji(momento)} {momentos.nome(momento)}** — {kcal_m:.0f} kcal")
            for ref in refs:
                n = ref["nutrientes"]
                st.markdown(f"&nbsp;&nbsp;&nbsp;{ref['hora']} · {ref['nome']} · "
                            f"{n.get('kcal', 0):.0f} kcal · {n.get('proteina_g', 0):.0f} g "
                            + _t("prot", "prot"), unsafe_allow_html=True)
