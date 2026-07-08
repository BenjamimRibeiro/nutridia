"""Progresso — sequências (streaks), medalhas e projeção do peso-alvo."""
from datetime import date

import streamlit as st

from core import calc, db, i18n, metas, nutrients, scores
from views import tema

_t = i18n.t


def _relatorio_md(perfil: dict, r: dict, periodo: int, historico_peso: list) -> str:
    """Relatório do período em markdown, pronto a descarregar/partilhar."""
    hoje = date.today().strftime("%d/%m/%Y")
    linhas = [
        _t(f"# 🥗 Relatório NutriDia — últimos {periodo} dias",
           f"# 🥗 NutriDia report — last {periodo} days"),
        _t(f"Gerado a {hoje} para {st.session_state.get('nome', 'ti')}.",
           f"Generated on {hoje} for {st.session_state.get('nome', 'you')}."), "",
        _t("## Registo e disciplina", "## Logging and discipline"),
        _t(f"- Dias com registos: **{r['dias']}/{periodo}**",
           f"- Days logged: **{r['dias']}/{periodo}**"),
        _t(f"- Dias com calorias no alvo: **{r['no_alvo']}/{r['dias']}**",
           f"- Days with calories on target: **{r['no_alvo']}/{r['dias']}**"),
        _t(f"- Dias saudáveis (qualidade a sério): **{r['saudaveis']}/{r['dias']}**",
           f"- Healthy days (real quality): **{r['saudaveis']}/{r['dias']}**"), "",
        _t("## Médias diárias", "## Daily averages"),
        f"- {_t('Calorias', 'Calories')}: **{r['kcal']:.0f} kcal**",
        f"- {_t('Proteína', 'Protein')}: **{r['proteina_g']:.0f} g**",
        f"- {_t('Fibra', 'Fibre')}: **{r['fibra_g']:.0f} g**",
        f"- {_t('Água', 'Water')}: **{r['agua_ml']:.0f} ml**", "",
    ]
    if r["pontuacoes"]:
        linhas.append(_t("## Bem-estar (média das pontuações)",
                         "## Wellbeing (average scores)"))
        for n, v in sorted(r["pontuacoes"].items(), key=lambda x: -x[1]):
            linhas.append(f"- {scores.PONTUACOES[n]['emoji']} {scores.nome(n)}: **{v}%**")
        linhas.append("")
    if r.get("fracas"):
        linhas.append(_t("## Nutrientes a reforçar (média <70% do alvo)",
                         "## Nutrients to boost (average <70% of target)"))
        for c, f in r["fracas"]:
            linhas.append(f"- {nutrients.nome_de(c)}: {f:.0%} " + _t("do alvo", "of target"))
        linhas.append("")
    if historico_peso:
        primeiro, ultimo = historico_peso[0], historico_peso[-1]
        linhas += [_t("## Peso", "## Weight"),
                   _t(f"- Último registo: **{ultimo['kg']:.1f} kg** ({ultimo['data']})",
                      f"- Latest entry: **{ultimo['kg']:.1f} kg** ({ultimo['data']})"),
                   _t(f"- Evolução desde {primeiro['data']}: "
                      f"**{ultimo['kg'] - primeiro['kg']:+.1f} kg**",
                      f"- Change since {primeiro['data']}: "
                      f"**{ultimo['kg'] - primeiro['kg']:+.1f} kg**"), ""]
    linhas.append(_t("⚕️ Estimativas informativas — não substituem aconselhamento "
                     "médico ou nutricional.",
                     "⚕️ Informational estimates — not a substitute for medical or "
                     "nutritional advice."))
    return "\n".join(linhas)


def mostrar():
    tema.cabecalho("🎯", i18n.t("Progresso", "Progress"),
                   i18n.t("As tuas sequências, medalhas e o caminho até ao peso-alvo",
                          "Your streaks, medals and the path to your target weight"))

    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid)
    if not perfil:
        st.info(_t("Preenche primeiro o teu **Perfil** para acompanhares o teu progresso.",
                   "Fill in your **Profile** first to track your progress."))
        return

    alvos = calc.alvos_diarios(perfil)

    # ---- Sequências ----
    seq = metas.sequencia_atual(uid, alvos)
    seq_saud = metas.sequencia_saudavel(uid, alvos)
    dia_s = _t("dia(s)", "day(s)")
    c1, c2 = st.columns(2)
    c1.metric(_t("🔥 Calorias no alvo", "🔥 Calories on target"), f"{seq} {dia_s}",
              help=_t("Dias seguidos com as calorias entre 80% e 110% do alvo.",
                      "Days in a row with calories between 80% and 110% of target."))
    c2.metric(_t("🥗 Dias saudáveis", "🥗 Healthy days"), f"{seq_saud} {dia_s}",
              help=_t("Dias seguidos a sério: calorias na zona E proteína E fibra ok E sem "
                      "rebentar os limites de açúcar/sódio/gordura saturada.",
                      "Real days in a row: calories in zone AND protein AND fibre ok AND without "
                      "breaking the sugar/sodium/saturated fat limits."))
    if seq_saud >= 3:
        st.success(_t(f"💚 Estás a cuidar mesmo do teu corpo — {seq_saud} dia(s) saudáveis seguidos!",
                      f"💚 You're really taking care of your body — {seq_saud} healthy day(s) in a row!"))
    elif seq >= 1:
        st.info(_t("A sequência de **calorias** é fácil de manter; a de **dias saudáveis** é a "
                   "que mostra que estás a cuidar do corpo (não basta não passar das calorias — "
                   "conta a qualidade). Tenta fazê-las crescer juntas! 🌱",
                   "The **calories** streak is easy to keep; the **healthy days** streak is the one "
                   "that shows you're caring for your body (not exceeding calories isn't enough — "
                   "quality counts). Try to grow them together! 🌱"))
    else:
        st.info(_t("Fica dentro do alvo de calorias e come equilibrado hoje para começares as "
                   "tuas sequências! 🌱",
                   "Stay within your calorie target and eat balanced today to start your "
                   "streaks! 🌱"))

    # ---- Desafios da semana ----
    st.divider()
    st.subheader(i18n.t("🎯 Desafios desta semana", "🎯 This week's challenges"))
    desafios = metas.desafios_semanais(uid, perfil, alvos)
    feitos = sum(1 for d in desafios if d["completo"])
    st.caption(i18n.t(f"Completaste **{feitos} de {len(desafios)}** desafios esta semana. "
                      "Reiniciam todas as segundas-feiras.",
                      f"You completed **{feitos} of {len(desafios)}** challenges this week. "
                      "They reset every Monday."))
    cols = st.columns(2)
    for k, d in enumerate(desafios):
        with cols[k % 2]:
            marca = "✅" if d["completo"] else f"{d['atual']}/{d['alvo']}"
            st.markdown(f"{d['emoji']} **{d['nome']}** — {d['desc']} · {marca}")
            st.progress(d["atual"] / d["alvo"])

    # ---- Relatório do período ----
    st.divider()
    st.subheader(i18n.t("📊 Relatório", "📊 Report"))
    periodo = st.radio(_t("Período", "Period"),
                       [7, 30], horizontal=True, key="rel_periodo",
                       format_func=lambda d: _t(f"Últimos {d} dias", f"Last {d} days"))
    r = metas.resumo_periodo(uid, perfil, alvos, periodo)
    if r["dias"] == 0:
        st.caption(_t("Ainda sem registos neste período — regista refeições e o boletim aparece aqui.",
                      "No logs in this period yet — log meals and the summary will appear here."))
    else:
        do_alvo = _t("do alvo", "of target")
        c1, c2, c3 = st.columns(3)
        c1.metric(_t("Dias registados", "Days logged"), f"{r['dias']}/{periodo}")
        c2.metric(_t("🔥 Dias no alvo", "🔥 Days on target"), f"{r['no_alvo']}/{r['dias']}")
        c3.metric(_t("🥗 Dias saudáveis", "🥗 Healthy days"), f"{r['saudaveis']}/{r['dias']}")
        c1, c2, c3 = st.columns(3)
        c1.metric(_t("Média de calorias", "Avg. calories"), f"{r['kcal']:.0f} kcal")
        c2.metric(_t("Média de proteína", "Avg. protein"), f"{r['proteina_g']:.0f} g")
        c3.metric(_t("Média de água", "Avg. water"), f"{r['agua_ml']:.0f} ml")

        if r["melhor"] and r["pior"]:
            mc, mf = r["melhor"]
            pc, pf = r["pior"]
            st.markdown(f"🟢 **{_t('Onde brilhas:', 'Where you shine:')}** "
                        f"{nutrients.nome_de(mc)} ({min(mf, 1):.0%} {do_alvo}) "
                        f"· 🔴 **{_t('A melhorar:', 'To improve:')}** "
                        f"{nutrients.nome_de(pc)} ({min(pf, 1):.0%} {do_alvo})")
        if r["pontuacoes"]:
            top3 = sorted(r["pontuacoes"].items(), key=lambda x: -x[1])[:3]
            baixo = min(r["pontuacoes"].items(), key=lambda x: x[1])
            fortes = " · ".join(f"{scores.PONTUACOES[n]['emoji']} {scores.nome(n)} {v}%"
                                for n, v in top3)
            st.markdown(f"**{_t('Bem-estar médio — melhores:', 'Average wellbeing — best:')}** {fortes}")
            st.caption(_t(f"A área a precisar de mais atenção: "
                          f"{scores.PONTUACOES[baixo[0]]['emoji']} {scores.nome(baixo[0])} ({baixo[1]}%).",
                          f"The area needing most attention: "
                          f"{scores.PONTUACOES[baixo[0]]['emoji']} {scores.nome(baixo[0])} ({baixo[1]}%)."))

        st.download_button(
            _t("⬇️ Descarregar relatório (.md)", "⬇️ Download report (.md)"),
            _relatorio_md(perfil, r, periodo, db.historico_peso(uid)),
            file_name=f"relatorio_nutridia_{periodo}dias_{date.today().strftime('%Y-%m-%d')}.md",
            mime="text/markdown")

    # ---- Medalhas ----
    st.subheader(_t("🏅 Medalhas", "🏅 Medals"))
    lista = metas.medalhas(uid, perfil, alvos)
    cols = st.columns(3)
    for k, m in enumerate(lista):
        with cols[k % 3]:
            if m["conquistada"]:
                st.success(f"## {m['emoji']}\n**{m['nome']}**\n\n{m['desc']}")
            else:
                st.markdown(
                    f"<div style='opacity:.55;background:#fff;border-radius:14px;padding:14px;"
                    f"border:1px dashed #B9C7A6;text-align:center;'>"
                    f"<div style='font-size:34px;filter:grayscale(1);'>{m['emoji']}</div>"
                    f"<b>{m['nome']}</b><br><span style='font-size:13px;'>{m['desc']}</span><br>"
                    f"<span style='font-size:12px;color:#6b7a5e;'>📊 {m['progresso']}</span></div>",
                    unsafe_allow_html=True)

    # ---- Projeção de peso ----
    st.divider()
    st.subheader(_t("⚖️ Caminho até ao peso-alvo", "⚖️ Path to your target weight"))
    historico = db.historico_peso(uid)
    proj = calc.projecao_peso(perfil, historico)

    if proj is None:
        st.info(_t("Define um **peso-alvo** no teu Perfil para veres aqui a projeção de quando "
                   "o vais atingir, ao teu ritmo.",
                   "Set a **target weight** in your Profile to see here a projection of when "
                   "you'll reach it, at your pace."))
    elif proj.get("atingido"):
        st.success(_t(f"🎉 Já estás no teu peso-alvo ({proj['alvo']:.0f} kg)! Parabéns!",
                      f"🎉 You're already at your target weight ({proj['alvo']:.0f} kg)! Congrats!"))
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric(_t("Peso atual", "Current weight"), f"{proj['atual']:.1f} kg")
        c2.metric(_t("Peso-alvo", "Target weight"), f"{proj['alvo']:.1f} kg",
                  delta=f"{proj['delta']:+.1f} kg", delta_color="off")
        c3.metric(_t("Faltam", "To go"), f"{abs(proj['delta']):.1f} kg")
        if proj["incoerente"]:
            st.warning(_t("⚠️ O teu peso-alvo vai no sentido contrário ao teu objetivo definido "
                          "no Perfil. Confirma o objetivo (emagrecer/engordar) e o peso-alvo.",
                          "⚠️ Your target weight goes the opposite way to the goal set in your "
                          "Profile. Check the goal (lose/gain) and the target weight."))
        else:
            data_txt = proj["data"].strftime("%d/%m/%Y")
            fonte = _t("tendência real", "actual trend") if proj["fonte"] == "tendência real" \
                else _t("ritmo planeado", "planned pace")
            st.success(_t(f"📅 Ao ritmo atual (~{proj['ritmo']:.2f} kg/semana, pela "
                          f"{fonte}), atinges o teu objetivo por volta de **{data_txt}** "
                          f"(~{proj['semanas']:.0f} semanas).",
                          f"📅 At the current pace (~{proj['ritmo']:.2f} kg/week, by "
                          f"{fonte}), you'll reach your goal around **{data_txt}** "
                          f"(~{proj['semanas']:.0f} weeks)."))
        st.caption(_t("A projeção usa a tua tendência real de peso quando há registos suficientes; "
                      "caso contrário, usa o ritmo planeado no Perfil. Regista o peso no Histórico.",
                      "The projection uses your actual weight trend when there's enough data; "
                      "otherwise it uses the planned pace in your Profile. Log weight in History."))
