"""Painel — resumo do dia: calorias, macros, água e pontuações de bem-estar."""
from datetime import date, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from core import (calc, db, doenca, exercicios, i18n, metas, momentos, nutrients, scores,
                  sugestoes)
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
        dia_s = d.strftime("%Y-%m-%d")
        totais_dia = db.totais_do_dia(uid, dia_s)
        if totais_dia.get("kcal", 0) > 0:
            alvos_d = {**alvos, "kcal": alvos["kcal"] + db.exercicio_kcal_do_dia(uid, dia_s)}
            valor = scores.calcular(totais_dia, alvos_d, sexo)[escolha]
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
    tema.cabecalho("📊", i18n.t("O teu dia", "Your day"),
                   i18n.t("Calorias, nutrientes e bem-estar de hoje num relance",
                          "Today's calories, nutrients and wellbeing at a glance"))

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

    # exercício de hoje soma ao alvo de calorias (podes comer mais nos dias que treinas)
    kcal_ex = db.exercicio_kcal_do_dia(uid, hoje)
    alvo_kcal = alvos["kcal"] + kcal_ex
    alvos_aj = {**alvos, "kcal": alvo_kcal}

    # ---- Como te sentes hoje? (modo doente) ----
    estado = db.obter_estado(uid, hoje)
    doente_inicial = estado["estado"] == "Doente"
    with st.expander("🤒 Como te sentes hoje?", expanded=doente_inicial):
        doente = st.toggle("Estou doente", value=doente_inicial, key="doente_tg")
        tipo = None
        if doente:
            idx = doenca.TIPOS.index(estado["tipo"]) if estado.get("tipo") in doenca.TIPOS else 0
            tipo = st.selectbox("O que tens?", doenca.TIPOS, index=idx, key="doente_tipo")
        novo = "Doente" if doente else "Saudável"
        if novo != estado["estado"] or (doente and tipo != estado.get("tipo")):
            db.definir_estado(uid, novo, tipo)
            estado = {"estado": novo, "tipo": tipo}
        if doente:
            c = doenca.conforto(tipo)
            st.info(f"💛 As melhoras! Para **{tipo.lower()}**, conforto à base de comida:\n\n"
                    f"🍲 **Come:** {c['alimentos']}\n\n"
                    f"✨ {c['nutrientes']}\n\n"
                    f"💡 {c['dica']}")
            st.caption("Hoje a app não te martela com as metas — recupera com calma. "
                       "⚕️ Isto é conforto alimentar, não conselho médico; se persistir, "
                       "consulta um médico.")

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
    col_kcal.metric("Calorias", f"{kcal:.0f} / {alvo_kcal}",
                    delta=f"{kcal - alvo_kcal:+.0f} kcal",
                    delta_color="off",
                    help=f"Alvo para {objetivo_txt}")
    col_prot.metric("Proteína", f"{totais.get('proteina_g', 0):.0f} / {alvos['proteina_g']} g")
    col_hid.metric("Hidratos", f"{totais.get('hidratos_g', 0):.0f} / {alvos['hidratos_g']} g")
    col_gord.metric("Gordura", f"{totais.get('gordura_g', 0):.0f} / {alvos['gordura_g']} g")
    if kcal_ex:
        st.caption(f"🏃 Alvo base {alvos['kcal']} + {kcal_ex} kcal de exercício = "
                   f"**{alvo_kcal} kcal** disponíveis hoje.")

    for chave, alvo in [("kcal", alvo_kcal), ("proteina_g", alvos["proteina_g"])]:
        fracao = min(totais.get(chave, 0) / alvo, 1.0) if alvo else 0
        st.progress(fracao, text=f"{nutrients.nome_de(chave)}: {fracao:.0%} do alvo")

    # ---- Sugestão inteligente: o que comer a seguir ----
    if estado["estado"] != "Doente":
        sug = sugestoes.para_agora(totais, alvos_aj, perfil["sexo"],
                                   perfil.get("alergias", []), perfil.get("restricoes", []))
        if sug["saudaveis"] or sug["treat"]:
            with st.expander("🤖 Sugestão: o que comer a seguir", expanded=False):
                if sug["saudaveis"]:
                    st.markdown(f"Tens ~**{sug['resto_kcal']:.0f} kcal** disponíveis. Opções "
                                "saudáveis e variadas que te dão o que ainda falta hoje:")
                    for s in sug["saudaveis"]:
                        ajuda = ", ".join(nutrients.nome_de(c) for c, _ in s["cobre"][:3])
                        st.markdown(f"- 🥗 **{s['nome']}** ({s['rotulo']}, {s['gramas']} g) → "
                                    f"bom para **{ajuda}** · {s['kcal']:.0f} kcal")
                if sug["treat"]:
                    t = sug["treat"]
                    st.markdown(f"😋 E se te apetecer algo bom (sabe sempre bem de vez em quando!): "
                                f"**{t['nome']}** ({t['rotulo']}, {t['gramas']} g) · {t['kcal']:.0f} kcal")
                st.caption("Sugestões que respeitam as tuas alergias e preferências (Perfil).")

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

    # ---- Exercício de hoje ----
    st.subheader("🏃 Exercício de hoje")
    ca, cb, cc = st.columns([2, 1, 1])
    atividade = ca.selectbox("Atividade", list(exercicios.ATIVIDADES), key="ex_at")
    minutos = cb.number_input("Minutos", 1, 600, 30, step=5, key="ex_min")
    kcal_est = exercicios.kcal(exercicios.ATIVIDADES[atividade], perfil["peso_kg"], minutos)
    cc.metric("Gasto estimado", f"{kcal_est} kcal")
    if st.button("➕ Registar exercício", type="primary"):
        db.registar_exercicio(uid, atividade, minutos, kcal_est)
        st.rerun()
    exs = db.exercicios_do_dia(uid, hoje)
    for e in exs:
        c1, c2 = st.columns([6, 1])
        c1.markdown(f"🔥 **{e['nome']}** — {e['duracao_min']} min · {e['kcal']} kcal")
        if c2.button("🗑️", key=f"exdel_{e['id']}", help="Remover"):
            db.apagar_exercicio(e["id"])
            st.rerun()
    if exs:
        st.caption(f"Total queimado hoje: **{kcal_ex} kcal** — já somados ao teu alvo de calorias.")

    # ---- Pontuações de bem-estar ----
    st.subheader("Pontuações de bem-estar")
    if not refeicoes:
        st.caption("Regista a tua primeira refeição de hoje para veres as pontuações. 🍽️")
    else:
        pontuacoes = scores.calcular(totais, alvos_aj, perfil["sexo"])
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
        components.graficos_cobertura(totais, perfil["sexo"], alvos_aj)
        with st.expander("📋 Ver tabela detalhada"):
            components.tabela_cobertura(totais, perfil["sexo"], alvos_aj)

    # ---- Refeições de hoje (agrupadas por momento) ----
    st.subheader(f"Refeições de hoje ({len(refeicoes)})")
    if not refeicoes:
        st.caption("Ainda não registaste nada hoje.")
    else:
        st.caption("✏️ Para corrigir quantidades ou apagar, vai ao **Histórico**.")
        por_momento: dict[str, list] = {}
        for ref in refeicoes:
            por_momento.setdefault(ref.get("momento") or "Outras", []).append(ref)
        for momento in momentos.MOMENTOS + ["Outras"]:
            refs = por_momento.get(momento)
            if not refs:
                continue
            kcal_m = sum(r["nutrientes"].get("kcal", 0) for r in refs)
            st.markdown(f"**{momentos.emoji(momento)} {momento}** — {kcal_m:.0f} kcal")
            for ref in refs:
                n = ref["nutrientes"]
                st.markdown(f"&nbsp;&nbsp;&nbsp;{ref['hora']} · {ref['nome']} · "
                            f"{n.get('kcal', 0):.0f} kcal · {n.get('proteina_g', 0):.0f} g prot",
                            unsafe_allow_html=True)
