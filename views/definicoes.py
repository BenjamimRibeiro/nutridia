"""Definições — idioma e região da base de dados de produtos (Open Food Facts)."""
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

    st.divider()
    st.caption(_t("ℹ️ Open Food Facts (openfoodfacts.org) é uma base de dados colaborativa e "
                  "gratuita. Os valores são aproximados e contribuídos por voluntários.",
                  "ℹ️ Open Food Facts (openfoodfacts.org) is a free, collaborative database. "
                  "Values are approximate and contributed by volunteers."))
