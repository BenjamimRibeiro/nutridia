"""Explorar — procurar um único alimento/ingrediente e ver todos os micronutrientes
que tem (por 100 g, por porção ou peso à escolha), com a % do teu dia.

Página só de leitura: não escreve nada na base de dados nem mexe em refeições."""
import streamlit as st

from core import db, foods, i18n, nutrients
from core import openfoodfacts as off
from views import components, tema

_t = i18n.t
_MICROS = [c for c in nutrients.DDR if c != "fibra_g"]
# nutrientes que contam para a manchete "Rico em…"
_RICO = ["proteina_g", "fibra_g", *nutrients.DDR]


def _ricos(nut: dict, sexo: str | None, alvos: dict | None) -> list[str]:
    """Nutrientes em que esta porção é forte (≥20% do alvo diário), top 4."""
    if not sexo:
        return []
    cobs = []
    for chave in dict.fromkeys(_RICO):
        alvo = nutrients.alvo_nutriente(chave, sexo, alvos)
        if alvo and nut.get(chave, 0) > 0:
            pct = nut[chave] / alvo
            if pct >= 0.20:
                cobs.append((pct, chave))
    cobs.sort(reverse=True)
    return [f"{nutrients.nome_de(c)} ({pct:.0%})" for pct, c in cobs[:4]]


def _detalhe(por_100g: dict, porcoes: list, perfil: dict | None, sexo: str | None,
             alvos: dict | None, prefixo: str) -> None:
    """Seletor de quantidade + manchete + tabela de todos os nutrientes."""
    custom = _t("✏️ Peso à escolha", "✏️ Custom weight")
    por_100 = _t("Por 100 g/ml", "Per 100 g/ml")
    opcoes = [por_100] + [f"{foods.porcao(lbl)} ({g} g)" for lbl, g in porcoes] + [custom]
    escolha = st.radio(_t("Quantidade", "Amount"), opcoes, horizontal=True, key=f"{prefixo}_q")

    if escolha == por_100:
        gramas = 100.0
    elif escolha == custom:
        gramas = st.number_input(_t("Peso (g/ml)", "Weight (g/ml)"), 1.0, 3000.0, 100.0,
                                 step=10.0, key=f"{prefixo}_g")
    else:
        gramas = porcoes[opcoes.index(escolha) - 1][1]

    nut = nutrients.escalar(por_100g, gramas)

    # manchete: calorias + "rico em"
    c1, c2 = st.columns([1, 2])
    c1.metric(_t("Energia", "Energy"), f"{nut.get('kcal', 0):.0f} kcal", help=f"{gramas:.0f} g")
    ricos = _ricos(nut, sexo, alvos)
    if ricos:
        c2.markdown(_t("**🌟 Rico em:** ", "**🌟 Rich in:** ") + " · ".join(ricos))
    cc1, cc2, cc3, cc4 = st.columns(4)
    cc1.metric(_t("Proteína", "Protein"), f"{nut.get('proteina_g', 0):.1f} g")
    cc2.metric(_t("Hidratos", "Carbs"), f"{nut.get('hidratos_g', 0):.1f} g")
    cc3.metric(_t("Gordura", "Fat"), f"{nut.get('gordura_g', 0):.1f} g")
    cc4.metric(_t("Fibra", "Fibre"), f"{nut.get('fibra_g', 0):.1f} g")

    st.markdown("**" + _t("Todos os nutrientes nesta quantidade:",
                          "All nutrients in this amount:") + "**")
    if perfil:
        components.tabela_cobertura(nut, sexo, alvos, apenas_consumidos=True)
    else:
        st.markdown(components.lista_nutrientes(nut))
        st.caption(_t("Preenche o **Perfil** para veres a % do teu dia em cada nutriente.",
                      "Fill in your **Profile** to see the % of your day for each nutrient."))


def _aba_comuns(perfil, sexo, alvos) -> None:
    todos = sorted(foods.ALIMENTOS, key=lambda a: nutrients.normalizar(foods.nome(a["nome"])))
    idx = st.selectbox(
        _t("Procura um alimento (escreve para filtrar)", "Search a food (type to filter)"),
        range(len(todos)), format_func=lambda i: foods.nome(todos[i]["nome"]), key="exp_comum")
    alimento = todos[idx]
    st.caption(foods.categoria_nome(alimento["categoria"]))
    _detalhe(alimento["por_100g"], alimento["porcoes"], perfil, sexo, alvos, "expc")


def _aba_off(perfil, sexo, alvos, pais) -> None:
    st.caption(_t(f"Produtos de marca na Open Food Facts ({pais.upper()}). Gratuito, sem chave. "
                  "Escreve e carrega **Enter** para procurar.",
                  f"Branded products on Open Food Facts ({pais.upper()}). Free, no key. "
                  "Type and press **Enter** to search."))
    with st.form("exp_off_form"):
        c1, c2 = st.columns([3, 1])
        termo = c1.text_input(_t("Produto ou marca", "Product or brand"), key="exp_termo",
                              label_visibility="collapsed",
                              placeholder=_t("Ex.: iogurte grego, manteiga de amendoim…",
                                             "E.g.: greek yogurt, peanut butter…"))
        if c2.form_submit_button(_t("🔍 Pesquisar", "🔍 Search"), use_container_width=True):
            try:
                with st.spinner(_t("A procurar na Open Food Facts…", "Searching Open Food Facts…")):
                    st.session_state["exp_res"] = off.pesquisar(termo, pais)
            except ValueError as e:
                st.error(str(e))
                st.session_state["exp_res"] = []

    with st.expander(_t("📷 Tenho o código de barras", "📷 I have the barcode")):
        with st.form("exp_cb_form"):
            cb = st.text_input(_t("Código de barras", "Barcode"), key="exp_cb",
                               placeholder="Ex.: 5601234567890")
            if st.form_submit_button(_t("Procurar código", "Search barcode")) and cb.strip():
                try:
                    with st.spinner(_t("A procurar…", "Searching…")):
                        st.session_state["exp_res"] = [off.por_codigo(cb.strip(), pais)]
                except ValueError as e:
                    st.error(str(e))

    res = st.session_state.get("exp_res")
    if res:
        i = st.selectbox(_t("Resultado", "Result"), range(len(res)),
                         format_func=lambda i: res[i]["nome"], key="exp_sel")
        prod = res[i]
        if prod.get("quantidade"):
            st.caption(_t("Embalagem", "Package") + f": {prod['quantidade']}")
        micros = sum(1 for c in _MICROS if prod["por_100g"].get(c, 0) > 0)
        if micros < 5:
            enriquecido, fonte = off.enriquecer(prod)
            if fonte:
                prod = enriquecido
                st.info(_t(f"ℹ️ A Open Food Facts não tinha as vitaminas/minerais deste produto — "
                           f"**estimei** a partir de «{fonte}» (alimento parecido).",
                           f"ℹ️ Open Food Facts had no vitamins/minerals for this product — "
                           f"I **estimated** them from “{fonte}” (a similar food)."))
            else:
                st.warning(_t(f"⚠️ Este produto só tem **{micros} de {len(_MICROS)}** "
                              "vitaminas/minerais na Open Food Facts.",
                              f"⚠️ This product only has **{micros} of {len(_MICROS)}** "
                              "vitamins/minerals on Open Food Facts."))
        _detalhe(prod["por_100g"], [], perfil, sexo, alvos, "expo")
    elif res == []:
        st.info(_t("Sem resultados com valores nutricionais. Tenta outro termo ou os "
                   "alimentos comuns.",
                   "No results with nutrition values. Try another term or the common foods."))


def mostrar():
    tema.cabecalho("🔍", i18n.t("Explorar alimento", "Explore a food"),
                   i18n.t("Procura um ingrediente e vê tudo o que ele tem — sem registar nada",
                          "Search an ingredient and see everything it has — without logging it"))

    from core import calc
    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid)
    alvos = calc.alvos_diarios(perfil) if perfil else None
    sexo = perfil["sexo"] if perfil else None
    pais = db.obter_definicao("off_pais", "pt")

    tab_comum, tab_off = st.tabs([_t("🍎 Alimentos comuns", "🍎 Common foods"),
                                  _t("🔍 Produtos de marca", "🔍 Branded products")])
    with tab_comum:
        _aba_comuns(perfil, sexo, alvos)
    with tab_off:
        _aba_off(perfil, sexo, alvos, pais)
