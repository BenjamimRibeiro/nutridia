"""Progresso — sequências (streaks), medalhas e projeção do peso-alvo."""
from datetime import date

import streamlit as st

from core import calc, db, metas, nutrients
from views import tema


def mostrar():
    tema.cabecalho("🎯", "Progresso", "As tuas sequências, medalhas e o caminho até ao peso-alvo")

    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid)
    if not perfil:
        st.info("Preenche primeiro o teu **Perfil** para acompanhares o teu progresso.")
        return

    alvos = calc.alvos_diarios(perfil)

    # ---- Sequência ----
    seq = metas.sequencia_atual(uid, alvos)
    c1, c2 = st.columns([1, 2])
    c1.metric("🔥 Sequência atual", f"{seq} dia(s)")
    if seq == 0:
        c2.info("Fica dentro do teu alvo de calorias hoje para começares uma sequência! "
                "(entre 80% e 110% do alvo)")
    elif seq < 3:
        c2.success(f"Boa! Mais {3 - seq} dia(s) para a medalha 🔥 *Em chamas*.")
    else:
        c2.success(f"Excelente! Estás com uma sequência de {seq} dias. Não a quebres! 💪")

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
