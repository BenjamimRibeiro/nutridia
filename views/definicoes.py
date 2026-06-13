"""Definições — idioma, região da base de produtos e exportação de dados."""
import pandas as pd
import streamlit as st

from core import db, i18n
from views import tema

PAISES = {"pt": "🇵🇹 Portugal", "br": "🇧🇷 Brasil", "world": "🌍 Mundo (todos os países)"}
IDIOMAS = {"pt": "🇵🇹 Português", "en": "🇬🇧 English"}
_t = i18n.t


def mostrar():
    tema.cabecalho("⚙️", _t("Definições", "Settings"),
                   _t("Idioma e base de dados de produtos", "Language and product database"))

    # ---- Idioma ----
    st.subheader(_t("🌐 Idioma", "🌐 Language"))
    atual_idioma = db.obter_definicao("idioma", "pt")
    chaves_i = list(IDIOMAS)
    escolha_i = st.radio(_t("Idioma da aplicação", "App language"), chaves_i,
                         index=chaves_i.index(atual_idioma) if atual_idioma in chaves_i else 0,
                         format_func=lambda k: IDIOMAS[k], horizontal=True)
    if escolha_i != atual_idioma:
        db.guardar_definicao("idioma", escolha_i)
        st.rerun()
    st.caption(_t("🔧 Tradução em curso: o menu, os títulos e esta página já estão em inglês; "
                  "o resto das páginas será traduzido em breve.",
                  "🔧 Translation in progress: the menu, titles and this page are already in "
                  "English; the rest of the pages will be translated soon."))

    st.divider()
    st.success(_t(
        "Esta app **não precisa de configuração nem de chaves pagas**. Os valores nutricionais "
        "vêm da tabela de alimentos comuns e da base gratuita **Open Food Facts**.",
        "This app **needs no configuration or paid keys**. Nutrition values come from the "
        "common-foods table and the free **Open Food Facts** database."))

    # ---- Base de dados de produtos ----
    st.subheader(_t("Base de dados de produtos", "Product database"))
    atual = db.obter_definicao("off_pais", "pt")
    chaves = list(PAISES)
    escolha = st.radio(
        _t("Região a usar quando pesquisas produtos de marca pelo nome",
           "Region to use when searching branded products by name"),
        chaves, index=chaves.index(atual) if atual in chaves else 0,
        format_func=lambda k: PAISES[k])
    if st.button(_t("💾 Guardar", "💾 Save"), type="primary"):
        db.guardar_definicao("off_pais", escolha)
        st.success(_t("Guardado!", "Saved!"))

    st.caption(_t("A pesquisa por nome dá prioridade a produtos da região escolhida. "
                  "A pesquisa por código de barras funciona em qualquer região.",
                  "Name search prioritises products from the chosen region. Barcode search "
                  "works in any region."))

    # ---- Exportar dados ----
    st.divider()
    st.subheader(_t("💾 Exportar os meus dados", "💾 Export my data"))
    uid = st.session_state.get("uid")
    refs = db.todas_refeicoes(uid)
    pesos = db.historico_peso(uid)
    exs = db.todos_exercicios(uid)
    if not (refs or pesos or exs):
        st.caption(_t("Ainda não há dados para exportar.", "No data to export yet."))
    else:
        st.caption(_t("Descarrega os teus dados em CSV (abre no Excel).",
                      "Download your data as CSV (opens in Excel)."))
        c1, c2, c3 = st.columns(3)
        if refs:
            linhas = []
            for r in refs:
                n = r["nutrientes"]
                linhas.append({
                    "data": r["data"], "hora": r["hora"], "momento": r.get("momento") or "",
                    "refeicao": r["nome"], "kcal": round(n.get("kcal", 0)),
                    "proteina_g": round(n.get("proteina_g", 0)),
                    "hidratos_g": round(n.get("hidratos_g", 0)),
                    "gordura_g": round(n.get("gordura_g", 0)),
                    "fibra_g": round(n.get("fibra_g", 0))})
            csv = pd.DataFrame(linhas).to_csv(index=False).encode("utf-8-sig")
            c1.download_button(_t("⬇️ Refeições", "⬇️ Meals"), csv,
                               "nutridia_refeicoes.csv", "text/csv", use_container_width=True)
        if pesos:
            csv = pd.DataFrame(pesos).to_csv(index=False).encode("utf-8-sig")
            c2.download_button(_t("⬇️ Peso", "⬇️ Weight"), csv,
                               "nutridia_peso.csv", "text/csv", use_container_width=True)
        if exs:
            df = pd.DataFrame([{"data": e["data"], "exercicio": e["nome"],
                                "minutos": e["duracao_min"], "kcal": e["kcal"]} for e in exs])
            csv = df.to_csv(index=False).encode("utf-8-sig")
            c3.download_button(_t("⬇️ Exercício", "⬇️ Exercise"), csv,
                               "nutridia_exercicio.csv", "text/csv", use_container_width=True)

    st.divider()
    st.caption(_t("ℹ️ Open Food Facts (openfoodfacts.org) é uma base de dados colaborativa e "
                  "gratuita. Os valores são aproximados e contribuídos por voluntários.",
                  "ℹ️ Open Food Facts (openfoodfacts.org) is a free, collaborative database. "
                  "Values are approximate and contributed by volunteers."))
