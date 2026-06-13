"""Progresso — sequências (streaks), medalhas e projeção do peso-alvo."""
from datetime import date

import streamlit as st

from core import calc, db, metas, nutrients, scores
from views import tema


def mostrar():
    tema.cabecalho("🎯", "Progresso", "As tuas sequências, medalhas e o caminho até ao peso-alvo")

    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid)
    if not perfil:
        st.info("Preenche primeiro o teu **Perfil** para acompanhares o teu progresso.")
        return

    alvos = calc.alvos_diarios(perfil)

    # ---- Sequências ----
    seq = metas.sequencia_atual(uid, alvos)
    seq_saud = metas.sequencia_saudavel(uid, alvos)
    c1, c2 = st.columns(2)
    c1.metric("🔥 Calorias no alvo", f"{seq} dia(s)",
              help="Dias seguidos com as calorias entre 80% e 110% do alvo.")
    c2.metric("🥗 Dias saudáveis", f"{seq_saud} dia(s)",
              help="Dias seguidos a sério: calorias na zona E proteína E fibra ok E sem "
                   "rebentar os limites de açúcar/sódio/gordura saturada.")
    if seq_saud >= 3:
        st.success(f"💚 Estás a cuidar mesmo do teu corpo — {seq_saud} dia(s) saudáveis seguidos!")
    elif seq >= 1:
        st.info("A sequência de **calorias** é fácil de manter; a de **dias saudáveis** é a "
                "que mostra que estás a cuidar do corpo (não basta não passar das calorias — "
                "conta a qualidade). Tenta fazê-las crescer juntas! 🌱")
    else:
        st.info("Fica dentro do alvo de calorias e come equilibrado hoje para começares as "
                "tuas sequências! 🌱")

    # ---- Resumo da semana ----
    st.divider()
    st.subheader("📊 Resumo da semana")
    r = metas.resumo_semanal(uid, perfil, alvos)
    if r["dias"] == 0:
        st.caption("Ainda sem registos esta semana — regista refeições e o boletim aparece aqui.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Dias registados", f"{r['dias']}/7")
        c2.metric("🔥 Dias no alvo", f"{r['no_alvo']}/{r['dias']}")
        c3.metric("🥗 Dias saudáveis", f"{r['saudaveis']}/{r['dias']}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Média de calorias", f"{r['kcal']:.0f} kcal")
        c2.metric("Média de proteína", f"{r['proteina_g']:.0f} g")
        c3.metric("Média de água", f"{r['agua_ml']:.0f} ml")

        if r["melhor"] and r["pior"]:
            mc, mf = r["melhor"]
            pc, pf = r["pior"]
            st.markdown(f"🟢 **Onde brilhas:** {nutrients.nome_de(mc)} ({min(mf, 1):.0%} do alvo) "
                        f"· 🔴 **A melhorar:** {nutrients.nome_de(pc)} ({min(pf, 1):.0%} do alvo)")
        if r["pontuacoes"]:
            top3 = sorted(r["pontuacoes"].items(), key=lambda x: -x[1])[:3]
            baixo = min(r["pontuacoes"].items(), key=lambda x: x[1])
            fortes = " · ".join(f"{scores.PONTUACOES[n]['emoji']} {n} {v}%" for n, v in top3)
            st.markdown(f"**Bem-estar médio — melhores:** {fortes}")
            st.caption(f"A área a precisar de mais atenção: "
                       f"{scores.PONTUACOES[baixo[0]]['emoji']} {baixo[0]} ({baixo[1]}%).")

    # ---- Medalhas ----
    st.subheader("🏅 Medalhas")
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
    st.subheader("⚖️ Caminho até ao peso-alvo")
    historico = db.historico_peso(uid)
    proj = calc.projecao_peso(perfil, historico)

    if proj is None:
        st.info("Define um **peso-alvo** no teu Perfil para veres aqui a projeção de quando "
                "o vais atingir, ao teu ritmo.")
    elif proj.get("atingido"):
        st.success(f"🎉 Já estás no teu peso-alvo ({proj['alvo']:.0f} kg)! Parabéns!")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Peso atual", f"{proj['atual']:.1f} kg")
        c2.metric("Peso-alvo", f"{proj['alvo']:.1f} kg",
                  delta=f"{proj['delta']:+.1f} kg", delta_color="off")
        c3.metric("Faltam", f"{abs(proj['delta']):.1f} kg")
        if proj["incoerente"]:
            st.warning("⚠️ O teu peso-alvo vai no sentido contrário ao teu objetivo definido "
                       "no Perfil. Confirma o objetivo (emagrecer/engordar) e o peso-alvo.")
        else:
            data_txt = proj["data"].strftime("%d/%m/%Y")
            st.success(f"📅 Ao ritmo atual (~{proj['ritmo']:.2f} kg/semana, pela "
                       f"{proj['fonte']}), atinges o teu objetivo por volta de **{data_txt}** "
                       f"(~{proj['semanas']:.0f} semanas).")
        st.caption("A projeção usa a tua tendência real de peso quando há registos suficientes; "
                   "caso contrário, usa o ritmo planeado no Perfil. Regista o peso no Histórico.")
