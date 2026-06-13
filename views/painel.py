"""Painel — resumo do dia: calorias, macros, água e pontuações de bem-estar."""
from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from core import calc, db, metas, nutrients, scores
from views import components, tema


# escala contínua vermelho → laranja → amarelo → verde
_PARAGENS = [(0, (217, 83, 79)), (28, (232, 116, 59)), (52, (232, 194, 32)),
             (76, (143, 185, 90)), (100, (46, 125, 79))]
# gradiente CSS reutilizado na própria barra
_GRADIENTE = ("linear-gradient(90deg,#D9534F 0%,#E8743B 28%,#E8C220 52%,"
              "#8FB95A 76%,#2E7D4F 100%)")


def _cor(valor: float) -> str:
    """Cor interpolada na escala vermelho→verde para um valor 0–100."""
    v = max(0, min(100, valor))
    for (p0, c0), (p1, c1) in zip(_PARAGENS, _PARAGENS[1:]):
        if v <= p1:
            t = (v - p0) / (p1 - p0) if p1 > p0 else 0
            r, g, b = (round(a + (c - a) * t) for a, c in zip(c0, c1))
            return f"#{r:02X}{g:02X}{b:02X}"
    return "#2E7D4F"


def _cartao_pontuacao(nome: str, valor: int, cfg: dict) -> None:
    cor = _cor(valor)
    st.markdown(
        f"""<div title="{cfg['descricao']}" style="background:#FBFCF6;border-radius:14px;
        padding:12px 14px;box-shadow:0 2px 8px rgba(36,48,36,.07);margin-bottom:10px;">
        <div style="display:flex;justify-content:space-between;align-items:center;
        font-weight:800;font-size:15px;">
        <span>{cfg['emoji']} {nome}</span><span style="color:{cor};">{valor}%</span></div>
        <div style="position:relative;height:11px;border-radius:99px;background:#E3EAD9;
        overflow:hidden;margin:8px 0 7px;">
        <div style="position:absolute;inset:0;background:{_GRADIENTE};"></div>
        <div style="position:absolute;top:0;bottom:0;left:{max(valor, 2)}%;right:0;
        background:#E3EAD9;"></div></div>
        <div style="font-size:12.5px;color:#5d6b52;line-height:1.35;">
        🍴 Ajuda: {cfg['dica']}</div></div>""",
        unsafe_allow_html=True,
    )


def _evolucao_pontuacoes(uid, alvos: dict, sexo: str) -> None:
    """Gráfico de linha com a progressão de uma pontuação nos últimos 7 dias."""
    nomes = list(scores.PONTUACOES)
    escolha = st.selectbox("Pontuação", nomes,
                           format_func=lambda n: f"{scores.PONTUACOES[n]['emoji']} {n}")
    linhas = []
    for i in range(6, -1, -1):
        d = date.today() - timedelta(days=i)
        totais_dia = db.totais_do_dia(uid, d.strftime("%Y-%m-%d"))
        if totais_dia.get("kcal", 0) > 0:
            valor = scores.calcular(totais_dia, alvos, sexo)[escolha]
            linhas.append({"Dia": d.strftime("%d/%m"), "Pontuação": valor,
                           "cor": _cor(valor), "ordem": 6 - i})
    if len(linhas) < 2:
        st.caption("Regista refeições em pelo menos 2 dias para veres a progressão. 📈")
        return
    df = pd.DataFrame(linhas)
    ordem_dias = df.sort_values("ordem")["Dia"].tolist()
    linha = alt.Chart(df).mark_line(color="#9AB88E", size=2.5).encode(
        x=alt.X("Dia:N", sort=ordem_dias, title=None),
        y=alt.Y("Pontuação:Q", scale=alt.Scale(domain=[0, 100]), title="%"))
    pontos = alt.Chart(df).mark_point(filled=True, size=140).encode(
        x=alt.X("Dia:N", sort=ordem_dias),
        y="Pontuação:Q",
        color=alt.Color("cor:N", scale=None),
        tooltip=[alt.Tooltip("Dia:N"), alt.Tooltip("Pontuação:Q", format=".0f")])
    st.altair_chart((linha + pontos).properties(height=220), use_container_width=True)


def mostrar():
    tema.cabecalho("📊", "O teu dia", "Calorias, nutrientes e bem-estar de hoje num relance")

    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid)
    if not perfil:
        st.info("👋 Bem-vindo! Começa por preencher o teu **Perfil** (no menu lateral) "
                "para calcularmos as tuas necessidades diárias.")
        return

    hoje = date.today().strftime("%Y-%m-%d")
    alvos = calc.alvos_diarios(perfil)
    totais = db.totais_do_dia(uid, hoje)
    refeicoes = db.refeicoes_do_dia(uid, hoje)

    # ---- Sequência (streak) ----
    seq = metas.sequencia_atual(uid, alvos)
    if seq >= 2:
        st.markdown(f"#### 🔥 Sequência de **{seq} dias** dentro do alvo — continua assim!")

    # ---- Calorias e macros ----
    st.subheader("Calorias e macros")
    col_kcal, col_prot, col_hid, col_gord = st.columns(4)
    objetivo_txt = {"Manter peso": "manter", "Emagrecer": "emagrecer",
                    "Engordar / ganhar massa": "ganhar massa"}[perfil["objetivo"]]
    kcal = totais.get("kcal", 0)
    col_kcal.metric("Calorias", f"{kcal:.0f} / {alvos['kcal']}",
                    delta=f"{kcal - alvos['kcal']:+.0f} kcal",
                    delta_color="off",
                    help=f"Alvo para {objetivo_txt}")
    col_prot.metric("Proteína", f"{totais.get('proteina_g', 0):.0f} / {alvos['proteina_g']} g")
    col_hid.metric("Hidratos", f"{totais.get('hidratos_g', 0):.0f} / {alvos['hidratos_g']} g")
    col_gord.metric("Gordura", f"{totais.get('gordura_g', 0):.0f} / {alvos['gordura_g']} g")

    for chave, alvo in [("kcal", alvos["kcal"]), ("proteina_g", alvos["proteina_g"])]:
        fracao = min(totais.get(chave, 0) / alvo, 1.0) if alvo else 0
        st.progress(fracao, text=f"{nutrients.nome_de(chave)}: {fracao:.0%} do alvo")

    # ---- Água ----
    st.subheader("💧 Água")
    agua = db.agua_do_dia(uid, hoje)
    st.progress(min(agua / alvos["agua_ml"], 1.0),
                text=f"{agua} / {alvos['agua_ml']} ml")
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

    # ---- Pontuações de bem-estar ----
    st.subheader("Pontuações de bem-estar")
    if not refeicoes:
        st.caption("Regista a tua primeira refeição de hoje para veres as pontuações. 🍽️")
    else:
        pontuacoes = scores.calcular(totais, alvos, perfil["sexo"])
        colunas = st.columns(3)
        for i, (nome, valor) in enumerate(pontuacoes.items()):
            with colunas[i % 3]:
                _cartao_pontuacao(nome, valor, scores.PONTUACOES[nome])
        st.caption("As pontuações sobem ao longo do dia à medida que registas refeições — "
                   "valores baixos de manhã são normais. Passa o rato por cima de um cartão "
                   "para veres o que mede.")
        with st.expander("📈 Progressão das pontuações (últimos 7 dias)"):
            _evolucao_pontuacoes(uid, alvos, perfil["sexo"])

    # ---- Nutrientes do dia (gráficos por grupo) ----
    st.subheader("📈 Nutrientes do dia — alcançados e em falta")
    if not refeicoes:
        st.caption("Regista refeições para preencheres estes gráficos.")
    else:
        components.graficos_cobertura(totais, perfil["sexo"], alvos)
        with st.expander("📋 Ver tabela detalhada"):
            components.tabela_cobertura(totais, perfil["sexo"], alvos)

    # ---- Refeições de hoje ----
    st.subheader(f"Refeições de hoje ({len(refeicoes)})")
    if not refeicoes:
        st.caption("Ainda não registaste nada hoje.")
    else:
        st.caption("✏️ Para corrigir quantidades ou apagar, vai ao **Histórico**.")
    for ref in refeicoes:
        n = ref["nutrientes"]
        st.markdown(f"**{ref['hora']}** — {ref['nome']} · "
                    f"{n.get('kcal', 0):.0f} kcal · {n.get('proteina_g', 0):.0f} g proteína")
