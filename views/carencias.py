"""Carências — o que pode faltar na tua alimentação, o que sentirias,
e sugestões de alimentos para repor."""
from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from core import calc, db, dieta, foods, i18n, nutrients
from core import condicoes as condicoes_mod
from core import sugestoes as sugestoes_mod
from views import tema

_t = i18n.t


def _media_periodo(uid, dias: int) -> tuple[dict, int]:
    """Média diária de nutrientes nos últimos `dias` dias COM refeições registadas."""
    somas: dict[str, float] = {}
    dias_com_dados = 0
    for i in range(dias):
        dia = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        if db.tem_refeicoes(uid, dia):
            dias_com_dados += 1
            for chave, valor in db.totais_do_dia(uid, dia).items():
                somas[chave] = somas.get(chave, 0) + valor
    if dias_com_dados == 0:
        return {}, 0
    return {k: v / dias_com_dados for k, v in somas.items()}, dias_com_dados


def _media_7_dias(uid) -> tuple[dict, int]:
    return _media_periodo(uid, 7)


def _sugestoes(em_falta: list, medias: dict, alergias: list, preferencias: list,
               condicoes_ativas: list | None = None) -> list:
    """Alimentos compatíveis ordenados por quanto repõem dos nutrientes em falta.

    Devolve [(pontuacao, alimento, rotulo_porcao, gramas, {nutriente: fracao_do_gap})]."""
    gaps = {chave: max(alvo - medias.get(chave, 0), 0) for chave, _, alvo in em_falta}
    pontuados = []
    for alimento in foods.ALIMENTOS:
        if not dieta.compativel(alimento, alergias, preferencias):
            continue
        rotulo, gramas = alimento["porcoes"][0]
        nut = nutrients.escalar(alimento["por_100g"], gramas)
        fator = sugestoes_mod.fator_condicoes(nut, condicoes_ativas)
        if fator is None:  # rebenta o limite de uma condição de saúde → fora
            continue
        cobertura = {}
        for chave, falta in gaps.items():
            if falta > 0 and nut.get(chave, 0) > 0:
                fracao = min(nut[chave] / falta, 1.0)
                if fracao >= 0.10:  # só conta se repuser pelo menos 10% do que falta
                    cobertura[chave] = fracao
        if cobertura:
            pontuados.append((sum(cobertura.values()) * fator, alimento, rotulo, gramas, cobertura))
    pontuados.sort(key=lambda x: -x[0])
    return pontuados


def mostrar():
    tema.cabecalho("🔬", i18n.t("Carências e sintomas", "Deficiencies & symptoms"),
                   i18n.t("O que pode faltar na tua semana — e o que comer para repor",
                          "What might be missing this week — and what to eat to top it up"))

    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid)
    if not perfil:
        st.info(_t("Preenche primeiro o teu **Perfil** para personalizar esta análise.",
                   "Fill in your **Profile** first to personalise this analysis."))
        return

    alvos = calc.alvos_diarios(perfil)
    medias, dias_com_dados = _media_7_dias(uid)

    # macros relevantes + micros com DDR, sem duplicados, em ordem alfabética
    chaves = nutrients.ordenar(dict.fromkeys(["proteina_g", "agua_ml", *nutrients.DDR]))

    em_falta = []
    if dias_com_dados == 0:
        st.warning(_t("Ainda não tens registos suficientes. Regista refeições durante alguns "
                      "dias e volta cá. Entretanto, podes explorar qualquer nutriente em baixo. 👇",
                      "You don't have enough logs yet. Log meals for a few days and come back. "
                      "Meanwhile, you can explore any nutrient below. 👇"))
    else:
        st.caption(_t(f"Análise baseada em **{dias_com_dados} dia(s)** com registos na última semana.",
                      f"Analysis based on **{dias_com_dados} day(s)** with logs in the last week."))
        coberturas = []
        for chave in chaves:
            alvo = nutrients.alvo_nutriente(chave, perfil["sexo"], alvos)
            if alvo:
                coberturas.append((chave, min(medias.get(chave, 0) / alvo, 9.99), alvo))

        em_falta = [c for c in coberturas if c[1] < 0.7]
        if not em_falta:
            st.success(_t("🎉 Excelente! Nenhuma carência relevante detetada na última semana.",
                          "🎉 Excellent! No relevant deficiencies detected in the last week."))
        else:
            st.subheader(_t(f"⚠️ {len(em_falta)} nutriente(s) abaixo de 70% do recomendado",
                            f"⚠️ {len(em_falta)} nutrient(s) below 70% of recommended"))
            for chave, fracao, alvo in em_falta:
                info = nutrients.carencia(chave)
                nome = nutrients.nome_de(chave)
                unidade = nutrients.unidade_de(chave)
                with st.expander(f"🔴 {nome} — {fracao:.0%} {_t('do alvo', 'of target')} "
                                 f"({medias.get(chave, 0):.0f}/{alvo:.0f} {unidade})"):
                    st.progress(min(fracao, 1.0))
                    if info:
                        st.markdown(f"**{_t('Se continuares assim, podes sentir:', 'If this continues, you may feel:')}** "
                                    f"{info['curto_prazo']}")
                        st.markdown(f"**{_t('A longo prazo:', 'Long term:')}** {info['longo_prazo']}")
                        st.markdown(f"**{_t('Onde encontrar:', 'Where to find it:')}** 🥗 {info['fontes']}")

        ok = [c for c in coberturas if c[1] >= 0.7]
        if ok:
            with st.expander(_t(f"✅ Nutrientes em dia ({len(ok)})",
                                f"✅ Nutrients on track ({len(ok)})")):
                for chave, fracao, alvo in ok:
                    st.markdown(f"🟢 **{nutrients.nome_de(chave)}** — {min(fracao, 1.0):.0%}")

    # ---- Tendências a 30 dias ----
    medias30, dias30 = _media_periodo(uid, 30)
    if dias30 >= 5:
        st.divider()
        st.subheader(_t("📉 Tendências a 30 dias", "📉 30-day trends"))
        st.caption(_t(f"Média de **{dias30} dia(s)** com registos no último mês — mostra o que "
                      "anda *sempre* em falta ou em excesso, para lá de um dia mau.",
                      f"Average of **{dias30} day(s)** with logs in the last month — shows what "
                      "is *consistently* lacking or excessive, beyond one bad day."))
        linhas = []
        for chave in chaves:
            alvo = nutrients.alvo_nutriente(chave, perfil["sexo"], alvos)
            if alvo:
                linhas.append({"nutriente": nutrients.nome_de(chave),
                               "cobertura": min(medias30.get(chave, 0) / alvo, 1.5)})
        if linhas:
            df = pd.DataFrame(linhas)
            df["estado"] = df["cobertura"].map(
                lambda f: "#D9534F" if f < 0.7 else ("#E8C220" if f < 0.9 else "#5B8C5A"))
            grafico = alt.Chart(df).mark_bar().encode(
                y=alt.Y("nutriente:N", sort=None, title=None),
                x=alt.X("cobertura:Q", title=_t("fração do alvo (média 30 dias)",
                                                "fraction of target (30-day avg)"),
                        axis=alt.Axis(format="%"), scale=alt.Scale(domain=[0, 1.5])),
                color=alt.Color("estado:N", scale=None),
                tooltip=[alt.Tooltip("nutriente:N"),
                         alt.Tooltip("cobertura:Q", format=".0%")])
            regra = alt.Chart(pd.DataFrame({"x": [1.0]})).mark_rule(
                strokeDash=[4, 3], color="#6b7a5e").encode(x="x:Q")
            st.altair_chart((grafico + regra).properties(height=max(220, 18 * len(linhas))),
                            use_container_width=True)

        cronicos_falta = [(c, medias30.get(c, 0) / nutrients.alvo_nutriente(c, perfil["sexo"], alvos))
                          for c in chaves
                          if nutrients.alvo_nutriente(c, perfil["sexo"], alvos)
                          and medias30.get(c, 0) / nutrients.alvo_nutriente(c, perfil["sexo"], alvos) < 0.7]
        efetivos = condicoes_mod.limites_efetivos(perfil.get("condicoes", []))
        cronicos_excesso = [(c, medias30.get(c, 0), info["limite"], info["por_condicao"])
                            for c, info in efetivos.items()
                            if medias30.get(c, 0) > info["limite"]]
        if cronicos_falta:
            st.markdown("**" + _t("🔴 Em falta crónica (média <70% do alvo):",
                                  "🔴 Chronically lacking (average <70% of target):") + "** "
                        + " · ".join(f"{nutrients.nome_de(c)} ({f:.0%})"
                                     for c, f in sorted(cronicos_falta, key=lambda x: x[1])))
        if cronicos_excesso:
            for c, m, lim, cond in cronicos_excesso:
                extra = (" — " + _t(f"limite da tua condição ({condicoes_mod.nome(cond).lower()})",
                                    f"your condition's limit ({condicoes_mod.nome(cond).lower()})")
                         if cond else "")
                st.markdown(f"⚠️ **{nutrients.nome_de(c)}** " +
                            _t("acima do limite em média", "above the limit on average") +
                            f": {m:.0f} / {lim:.0f} {nutrients.unidade_de(c)}" + extra)
        if not cronicos_falta and not cronicos_excesso:
            st.success(_t("💚 Nenhuma falta ou excesso crónico no último mês — consistência exemplar!",
                          "💚 No chronic lack or excess in the last month — great consistency!"))

    # ---- Explorador ----
    st.divider()
    st.subheader(_t("📖 Explorar um nutriente", "📖 Explore a nutrient"))
    opcoes = {nutrients.nome_de(c): c for c in chaves if c in nutrients.CARENCIAS}
    escolha = st.selectbox(_t("Escolhe um nutriente", "Choose a nutrient"), list(opcoes))
    chave = opcoes[escolha]
    info = nutrients.carencia(chave)
    alvo = nutrients.alvo_nutriente(chave, perfil["sexo"], alvos)

    if alvo:
        st.markdown(f"**{_t('Dose diária recomendada para ti:', 'Recommended daily amount for you:')}** "
                    f"{alvo:.0f} {nutrients.unidade_de(chave)}")
        if dias_com_dados:
            st.markdown(f"**{_t('A tua média (7 dias):', 'Your average (7 days):')}** "
                        f"{medias.get(chave, 0):.0f} {nutrients.unidade_de(chave)}")
    st.markdown(f"**{_t('Sintomas de carência a curto prazo:', 'Short-term deficiency symptoms:')}** "
                f"{info['curto_prazo']}")
    st.markdown(f"**{_t('Riscos a longo prazo:', 'Long-term risks:')}** {info['longo_prazo']}")
    st.markdown(f"**{_t('Boas fontes alimentares:', 'Good food sources:')}** 🥗 {info['fontes']}")

    # ---- Sugestões para repor o que falta ----
    if em_falta:
        st.divider()
        st.subheader(_t("🥗 O que comer para repor o que te falta",
                        "🥗 What to eat to top up what you're missing"))
        st.caption(_t("Alimentos da tabela que mais repõem os teus nutrientes em falta "
                      "(porção típica; % = quanto dessa falta diária fica reposta).",
                      "Foods from the table that best top up your missing nutrients "
                      "(typical portion; % = how much of that daily gap is covered)."))
        sugestoes = _sugestoes(em_falta, medias, perfil.get("alergias", []),
                               perfil.get("restricoes", []), perfil.get("condicoes", []))
        if perfil.get("alergias") or perfil.get("restricoes") or perfil.get("condicoes"):
            st.caption(_t("✅ As sugestões respeitam as tuas alergias, preferências e condições "
                          "de saúde (no Perfil).",
                          "✅ Suggestions respect your allergies, preferences and health "
                          "conditions (in Profile)."))
        if not sugestoes:
            st.caption(_t("Sem sugestões claras na tabela de alimentos para estas carências.",
                          "No clear suggestions in the food table for these deficiencies."))
        else:
            for pontuacao, alimento, rotulo, gramas, cobertura in sugestoes[:6]:
                partes = [f"{nutrients.nome_de(c)} **+{f:.0%}**"
                          for c, f in sorted(cobertura.items(), key=lambda x: -x[1])[:4]]
                st.markdown(f"- **{foods.nome(alimento['nome'])}** "
                            f"({foods.porcao(rotulo)}, {gramas} g) → "
                            + " · ".join(partes))

            # ideia de refeição: melhor alimento de até 3 categorias diferentes
            por_categoria: dict[str, tuple] = {}
            for s in sugestoes:
                por_categoria.setdefault(s[1]["categoria"], s)
            combo = sorted(por_categoria.values(), key=lambda x: -x[0])[:3]
            if len(combo) >= 2:
                nomes = " + ".join(foods.nome(s[1]["nome"]).lower() for s in combo)
                reposto = {}
                for *_resto, cobertura in combo:
                    for c, f in cobertura.items():
                        reposto[c] = min(reposto.get(c, 0) + f, 1.0)
                bem_repostos = sum(1 for f in reposto.values() if f >= 0.7)
                st.info(_t(f"💡 **Ideia de refeição:** {nomes} — juntos repõem ≥70% de "
                           f"**{bem_repostos} de {len(em_falta)}** nutrientes em falta.",
                           f"💡 **Meal idea:** {nomes} — together they top up ≥70% of "
                           f"**{bem_repostos} of {len(em_falta)}** missing nutrients."))

    st.divider()
    st.caption(_t("⚕️ Esta análise é informativa e baseia-se em estimativas — não substitui "
                  "análises clínicas nem o conselho de um médico ou nutricionista.",
                  "⚕️ This analysis is informational and based on estimates — it does not replace "
                  "clinical tests or the advice of a doctor or nutritionist."))
