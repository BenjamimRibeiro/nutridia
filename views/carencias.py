"""Carências — o que pode faltar na tua alimentação, o que sentirias,
e sugestões de alimentos para repor."""
from datetime import date, timedelta

import streamlit as st

from core import calc, db, dieta, foods, i18n, nutrients
from views import tema

_t = i18n.t


def _media_7_dias(uid) -> tuple[dict, int]:
    """Média diária de nutrientes nos últimos 7 dias COM refeições registadas."""
    somas: dict[str, float] = {}
    dias_com_dados = 0
    for i in range(7):
        dia = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        if db.tem_refeicoes(uid, dia):
            dias_com_dados += 1
            for chave, valor in db.totais_do_dia(uid, dia).items():
                somas[chave] = somas.get(chave, 0) + valor
    if dias_com_dados == 0:
        return {}, 0
    return {k: v / dias_com_dados for k, v in somas.items()}, dias_com_dados


def _sugestoes(em_falta: list, medias: dict, alergias: list, preferencias: list) -> list:
    """Alimentos compatíveis ordenados por quanto repõem dos nutrientes em falta.

    Devolve [(pontuacao, alimento, rotulo_porcao, gramas, {nutriente: fracao_do_gap})]."""
    gaps = {chave: max(alvo - medias.get(chave, 0), 0) for chave, _, alvo in em_falta}
    pontuados = []
    for alimento in foods.ALIMENTOS:
        if not dieta.compativel(alimento, alergias, preferencias):
            continue
        rotulo, gramas = alimento["porcoes"][0]
        nut = nutrients.escalar(alimento["por_100g"], gramas)
        cobertura = {}
        for chave, falta in gaps.items():
            if falta > 0 and nut.get(chave, 0) > 0:
                fracao = min(nut[chave] / falta, 1.0)
                if fracao >= 0.10:  # só conta se repuser pelo menos 10% do que falta
                    cobertura[chave] = fracao
        if cobertura:
            pontuados.append((sum(cobertura.values()), alimento, rotulo, gramas, cobertura))
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
                               perfil.get("restricoes", []))
        if perfil.get("alergias") or perfil.get("restricoes"):
            st.caption(_t("✅ As sugestões respeitam as tuas alergias e preferências (no Perfil).",
                          "✅ Suggestions respect your allergies and preferences (in Profile)."))
        if not sugestoes:
            st.caption(_t("Sem sugestões claras na tabela de alimentos para estas carências.",
                          "No clear suggestions in the food table for these deficiencies."))
        else:
            for pontuacao, alimento, rotulo, gramas, cobertura in sugestoes[:6]:
                partes = [f"{nutrients.nome_de(c)} **+{f:.0%}**"
                          for c, f in sorted(cobertura.items(), key=lambda x: -x[1])[:4]]
                st.markdown(f"- **{foods.nome(alimento['nome'])}** ({rotulo}, {gramas} g) → "
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
