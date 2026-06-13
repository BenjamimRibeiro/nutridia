"""Carências — o que pode faltar na tua alimentação, o que sentirias,
e sugestões de alimentos para repor."""
from datetime import date, timedelta

import streamlit as st

from core import calc, db, dieta, foods, nutrients
from views import tema


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
    tema.cabecalho("🔬", "Carências e sintomas",
                   "O que pode faltar na tua semana — e o que comer para repor")

    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid)
    if not perfil:
        st.info("Preenche primeiro o teu **Perfil** para personalizar esta análise.")
        return

    alvos = calc.alvos_diarios(perfil)
    medias, dias_com_dados = _media_7_dias(uid)

    # macros relevantes + micros com DDR, sem duplicados, em ordem alfabética
    chaves = nutrients.ordenar(dict.fromkeys(["proteina_g", "agua_ml", *nutrients.DDR]))

    em_falta = []
    if dias_com_dados == 0:
        st.warning("Ainda não tens registos suficientes. Regista refeições durante alguns "
                   "dias e volta cá. Entretanto, podes explorar qualquer nutriente em baixo. 👇")
    else:
        st.caption(f"Análise baseada em **{dias_com_dados} dia(s)** com registos na última semana.")
        coberturas = []
        for chave in chaves:
            alvo = nutrients.alvo_nutriente(chave, perfil["sexo"], alvos)
            if alvo:
                coberturas.append((chave, min(medias.get(chave, 0) / alvo, 9.99), alvo))

        em_falta = [c for c in coberturas if c[1] < 0.7]
        if not em_falta:
            st.success("🎉 Excelente! Nenhuma carência relevante detetada na última semana.")
        else:
            st.subheader(f"⚠️ {len(em_falta)} nutriente(s) abaixo de 70% do recomendado")
            for chave, fracao, alvo in em_falta:
                info = nutrients.CARENCIAS.get(chave)
                nome = nutrients.nome_de(chave)
                unidade = nutrients.unidade_de(chave)
                with st.expander(f"🔴 {nome} — {fracao:.0%} do alvo "
                                 f"({medias.get(chave, 0):.0f}/{alvo:.0f} {unidade})"):
                    st.progress(min(fracao, 1.0))
                    if info:
                        st.markdown(f"**Se continuares assim, podes sentir:** {info['curto_prazo']}")
                        st.markdown(f"**A longo prazo:** {info['longo_prazo']}")
                        st.markdown(f"**Onde encontrar:** 🥗 {info['fontes']}")

        ok = [c for c in coberturas if c[1] >= 0.7]
        if ok:
            with st.expander(f"✅ Nutrientes em dia ({len(ok)})"):
                for chave, fracao, alvo in ok:
                    st.markdown(f"🟢 **{nutrients.nome_de(chave)}** — {min(fracao, 1.0):.0%}")

    # ---- Explorador ----
    st.divider()
    st.subheader("📖 Explorar um nutriente")
    opcoes = {nutrients.nome_de(c): c for c in chaves if c in nutrients.CARENCIAS}
    escolha = st.selectbox("Escolhe um nutriente", list(opcoes))
    chave = opcoes[escolha]
    info = nutrients.CARENCIAS[chave]
    alvo = nutrients.alvo_nutriente(chave, perfil["sexo"], alvos)

    if alvo:
        st.markdown(f"**Dose diária recomendada para ti:** {alvo:.0f} {nutrients.unidade_de(chave)}")
        if dias_com_dados:
            st.markdown(f"**A tua média (7 dias):** {medias.get(chave, 0):.0f} "
                        f"{nutrients.unidade_de(chave)}")
    st.markdown(f"**Sintomas de carência a curto prazo:** {info['curto_prazo']}")
    st.markdown(f"**Riscos a longo prazo:** {info['longo_prazo']}")
    st.markdown(f"**Boas fontes alimentares:** 🥗 {info['fontes']}")

    # ---- Sugestões para repor o que falta ----
    if em_falta:
        st.divider()
        st.subheader("🥗 O que comer para repor o que te falta")
        st.caption("Alimentos da tabela que mais repõem os teus nutrientes em falta "
                   "(porção típica; % = quanto dessa falta diária fica reposta).")
        sugestoes = _sugestoes(em_falta, medias, perfil.get("alergias", []),
                               perfil.get("restricoes", []))
        if perfil.get("alergias") or perfil.get("restricoes"):
            st.caption("✅ As sugestões respeitam as tuas alergias e preferências (no Perfil).")
        if not sugestoes:
            st.caption("Sem sugestões claras na tabela de alimentos para estas carências.")
        else:
            for pontuacao, alimento, rotulo, gramas, cobertura in sugestoes[:6]:
                partes = [f"{nutrients.nome_de(c)} **+{f:.0%}**"
                          for c, f in sorted(cobertura.items(), key=lambda x: -x[1])[:4]]
                st.markdown(f"- **{alimento['nome']}** ({rotulo}, {gramas} g) → "
                            + " · ".join(partes))

            # ideia de refeição: melhor alimento de até 3 categorias diferentes
            por_categoria: dict[str, tuple] = {}
            for s in sugestoes:
                por_categoria.setdefault(s[1]["categoria"], s)
            combo = sorted(por_categoria.values(), key=lambda x: -x[0])[:3]
            if len(combo) >= 2:
                nomes = " + ".join(s[1]["nome"].lower() for s in combo)
                reposto = {}
                for *_resto, cobertura in combo:
                    for c, f in cobertura.items():
                        reposto[c] = min(reposto.get(c, 0) + f, 1.0)
                bem_repostos = sum(1 for f in reposto.values() if f >= 0.7)
                st.info(f"💡 **Ideia de refeição:** {nomes} — juntos repõem ≥70% de "
                        f"**{bem_repostos} de {len(em_falta)}** nutrientes em falta.")

    st.divider()
    st.caption("⚕️ Esta análise é informativa e baseia-se em estimativas — não substitui "
               "análises clínicas nem o conselho de um médico ou nutricionista.")
