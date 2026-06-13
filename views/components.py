"""Componentes visuais partilhados entre páginas."""
import altair as alt
import pandas as pd
import streamlit as st

from core import nutrients

# grupos de nutrientes para gráficos separados
_GRUPOS = [
    ("🥑 Macronutrientes", ["proteina_g", "hidratos_g", "gordura_g", "fibra_g", "omega3_g"]),
    ("⛏️ Minerais", ["calcio_mg", "ferro_mg", "magnesio_mg", "potassio_mg", "zinco_mg"]),
    ("🍊 Vitaminas", ["vit_a_ug", "vit_c_mg", "vit_d_ug", "vit_e_mg", "vit_k_ug",
                      "vit_b1_mg", "vit_b2_mg", "vit_b3_mg", "vit_b6_mg", "folato_ug", "vit_b12_ug"]),
]
_CORES = {"Em falta": "#E8743B", "Quase lá": "#F2C14E",
          "Completo": "#5B8C5A", "OK": "#5B8C5A", "Excesso": "#C0392B"}


def _fmt(valor: float) -> str:
    return f"{valor:.0f}" if abs(valor) >= 10 else f"{valor:.1f}"


def _estado(pct: float, limite: bool = False) -> str:
    if limite:
        return "Excesso" if pct > 100 else "OK"
    if pct >= 100:
        return "Completo"
    return "Quase lá" if pct >= 70 else "Em falta"


def _grafico(dados: list, titulo: str, x_titulo: str = "% do objetivo diário"):
    df = pd.DataFrame(dados).sort_values("ord")
    ordem = df["Nutriente"].tolist()
    barras = alt.Chart(df).mark_bar(size=18, cornerRadiusTopRight=6,
                                    cornerRadiusBottomRight=6).encode(
        x=alt.X("pct:Q", title=x_titulo, scale=alt.Scale(domain=[0, 150]),
                axis=alt.Axis(labelFontSize=11, titleFontSize=12, titlePadding=8,
                              grid=True, gridDash=[2, 3], gridColor="#E0E6D6")),
        y=alt.Y("Nutriente:N", sort=ordem, title=None,
                axis=alt.Axis(labelFontSize=12.5, labelLimit=200, labelPadding=8,
                              domain=False, ticks=False)),
        color=alt.Color("Estado:N",
                        scale=alt.Scale(domain=list(_CORES), range=list(_CORES.values())),
                        legend=None),
        tooltip=[alt.Tooltip("Nutriente:N", title="Nutriente"),
                 alt.Tooltip("texto:N", title="Consumido / alvo"),
                 alt.Tooltip("real:Q", title="% do objetivo", format=".0f")],
    )
    regra = alt.Chart(pd.DataFrame({"x": [100]})).mark_rule(
        color="#9AA79A", strokeDash=[4, 3], size=1.5).encode(x="x:Q")
    return (barras + regra).properties(
        height=max(46 * len(df) + 20, 120), padding={"left": 6, "right": 14, "top": 6, "bottom": 6},
        title=alt.TitleParams(titulo, anchor="start", fontSize=15, dy=-6, color="#243024"),
    ).configure_view(strokeWidth=0)


def graficos_cobertura(totais: dict, sexo: str, alvos: dict) -> None:
    """Vários gráficos de barras (macros, minerais, vitaminas, a moderar) do dia."""
    for titulo, chaves in _GRUPOS:
        dados = []
        for c in chaves:
            alvo = nutrients.alvo_nutriente(c, sexo, alvos)
            if not alvo:
                continue
            cons = totais.get(c, 0)
            pct = cons / alvo * 100
            dados.append({"Nutriente": nutrients.nome_de(c), "pct": min(pct, 150), "real": pct,
                          "Estado": _estado(pct), "ord": nutrients.normalizar(nutrients.nome_de(c)),
                          "texto": f"{_fmt(cons)} / {_fmt(alvo)} {nutrients.unidade_de(c)}"})
        if dados:
            st.altair_chart(_grafico(dados, titulo), use_container_width=True)

    dados = []
    for c, info in nutrients.LIMITES.items():
        cons = totais.get(c, 0)
        pct = cons / info["limite"] * 100
        dados.append({"Nutriente": info["nome"], "pct": min(pct, 150), "real": pct,
                      "Estado": _estado(pct, limite=True), "ord": nutrients.normalizar(info["nome"]),
                      "texto": f"{_fmt(cons)} / máx. {_fmt(info['limite'])} {info['unidade']}"})
    if dados:
        st.altair_chart(_grafico(dados, "🧂 A moderar (limite diário)", "% do limite diário"),
                        use_container_width=True)

    st.caption("Barra cheia = objetivo atingido · linha tracejada = 100%. "
               "Nos itens 🧂 *a moderar*, o ideal é ficar **abaixo** da linha.")


def tabela_cobertura(totais: dict, sexo: str, alvos: dict,
                     apenas_consumidos: bool = False) -> None:
    """Tabela com barras de progresso: nutrientes do dia alcançados e em falta.

    Nutrientes benéficos: % do alvo. Nutrientes a moderar: % do limite (⚠️ se passar).
    Ordenada alfabeticamente."""
    linhas = []

    beneficos = list(dict.fromkeys(
        ["kcal", "proteina_g", "hidratos_g", "gordura_g", "agua_ml", *nutrients.DDR]))
    for chave in beneficos:
        alvo = nutrients.alvo_nutriente(chave, sexo, alvos)
        if not alvo:
            continue
        consumido = totais.get(chave, 0)
        if apenas_consumidos and consumido <= 0:
            continue
        pct = consumido / alvo * 100
        estado = "✅" if pct >= 100 else ("🟡" if pct >= 70 else "🔴")
        unidade = nutrients.unidade_de(chave)
        linhas.append({"Estado": estado, "Nutriente": nutrients.nome_de(chave),
                       "Consumido": f"{_fmt(consumido)} {unidade}",
                       "Alvo": f"{_fmt(alvo)} {unidade}",
                       "Progresso": min(round(pct), 100)})

    for chave, info in nutrients.LIMITES.items():
        consumido = totais.get(chave, 0)
        if apenas_consumidos and consumido <= 0:
            continue
        pct = consumido / info["limite"] * 100
        estado = "⚠️" if pct > 100 else "✅"
        linhas.append({"Estado": estado, "Nutriente": f"{info['nome']} (a moderar)",
                       "Consumido": f"{_fmt(consumido)} {info['unidade']}",
                       "Alvo": f"máx. {_fmt(info['limite'])} {info['unidade']}",
                       "Progresso": min(round(pct), 100)})

    if not linhas:
        st.caption("Sem valores para mostrar.")
        return

    linhas.sort(key=lambda l: nutrients.normalizar(l["Nutriente"]))
    st.dataframe(
        pd.DataFrame(linhas),
        hide_index=True,
        column_config={
            "Estado": st.column_config.TextColumn("", width="small"),
            "Progresso": st.column_config.ProgressColumn(
                "Progresso", min_value=0, max_value=100, format="%d%%"),
        },
    )
    st.caption("✅ alvo atingido · 🟡 acima de 70% · 🔴 em falta · "
               "⚠️ ultrapassaste um limite a moderar")


def lista_nutrientes(nut: dict, sexo: str | None = None,
                     alvos: dict | None = None) -> str:
    """Markdown com os nutrientes não-nulos de um alimento/refeição (alfabético),
    com a % do dia que representam quando há perfil."""
    chaves = [c for c in nutrients.CAMPOS_NUTRIENTES if nut.get(c, 0) > 0]
    chaves.sort(key=lambda c: nutrients.normalizar(nutrients.nome_de(c)))
    linhas = []
    for chave in chaves:
        valor = nut[chave]
        extra = ""
        if sexo:
            if chave in nutrients.LIMITES:
                extra = f" — {valor / nutrients.LIMITES[chave]['limite']:.0%} do limite diário"
            else:
                alvo = nutrients.alvo_nutriente(chave, sexo, alvos)
                if alvo:
                    extra = f" — {valor / alvo:.0%} do teu dia"
        linhas.append(f"- **{nutrients.nome_de(chave)}**: {_fmt(valor)} "
                      f"{nutrients.unidade_de(chave)}{extra}")
    return "\n".join(linhas) if linhas else "_Sem valores nutricionais registados._"
