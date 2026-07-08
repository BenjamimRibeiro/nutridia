"""Construtor de refeição reutilizável — usado no Registar e na edição do Histórico.

Um "cesto" é uma lista de itens {nome, gramas, por_100g}. Os nutrientes são
calculados a partir de por_100g + gramas sempre que necessário (nutrients.escalar).
"""
import streamlit as st

from core import barcode, condicoes, db, foods, i18n, nutrients
from core import openfoodfacts as off
from views import components

_t = i18n.t
# vitaminas/minerais (exceto fibra) — para o aviso de dados em falta na OFF
_MICROS = [c for c in nutrients.DDR if c != "fibra_g"]
_CAT_MEUS = "⭐ Os meus"


def _resumo(nut: dict) -> str:
    return (f"{nut.get('kcal', 0):.0f} kcal · {nut.get('proteina_g', 0):.0f} g "
            + _t("prot", "prot") + f" · {nut.get('hidratos_g', 0):.0f} g "
            + _t("hid", "carb") + f" · {nut.get('gordura_g', 0):.0f} g " + _t("gord", "fat"))


def _categorias(uid) -> list[str]:
    cats = foods.categorias()
    if uid is not None and db.listar_alimentos_custom(uid):
        return [_CAT_MEUS] + cats
    return cats


def _alimentos(cat: str, uid) -> list[dict]:
    if cat == _CAT_MEUS:
        return db.listar_alimentos_custom(uid)
    return foods.por_categoria(cat)


def totais(cesto: list) -> dict:
    tot = {k: 0.0 for k in nutrients.CAMPOS_NUTRIENTES}
    for item in cesto:
        for c, v in nutrients.escalar(item["por_100g"], item["gramas"]).items():
            tot[c] += v
    return tot


def semaforo(tot: dict, condicoes_ativas: list[str] | None = None) -> None:
    """Semáforo instantâneo da refeição nos nutrientes a moderar (açúcar/sal/…)."""
    avaliacao = condicoes.semaforo_refeicao(tot, condicoes_ativas)
    partes = []
    for a in avaliacao:
        chip = (f"{a['emoji']} {nutrients.nome_de(a['chave'])} {a['consumido']:.0f} "
                f"{nutrients.unidade_de(a['chave'])} ({a['fracao']:.0%})")
        if a["por_condicao"]:
            chip += " " + _t(f"· limite da tua condição ({condicoes.nome(a['por_condicao']).lower()})",
                             f"· your condition's limit ({condicoes.nome(a['por_condicao']).lower()})")
        partes.append(chip)
    st.markdown(" &nbsp; ".join(partes))
    st.caption(_t("🚦 % = fatia do limite diário que esta refeição gasta "
                  "(🟢 ≤25% · 🟡 ≤50% · 🔴 >50%).",
                  "🚦 % = share of the daily limit this meal uses "
                  "(🟢 ≤25% · 🟡 ≤50% · 🔴 >50%)."))


def adicionar_alimento(cesto: list, prefixo: str, pais: str, uid=None) -> None:
    """Separadores para escolher um alimento (comuns/OFF/recentes) e juntar ao cesto."""
    recentes = db.alimentos_recentes(uid) if uid is not None else []
    etiquetas = [_t("🍎 Alimentos", "🍎 Foods"), _t("🔍 Pesquisar produto", "🔍 Search product")] \
        + ([_t("🕘 Recentes", "🕘 Recent")] if recentes else [])
    tabs = st.tabs(etiquetas)
    with tabs[0]:
        _aba_comuns(cesto, prefixo, uid)
    with tabs[1]:
        _aba_off(cesto, prefixo, pais)
    if recentes:
        with tabs[2]:
            _aba_recentes(cesto, prefixo, recentes)


def _aba_recentes(cesto: list, prefixo: str, recentes: list) -> None:
    st.caption(_t("Os teus alimentos mais recentes — com a porção que usaste da última vez.",
                  "Your most recent foods — with the portion you last used."))
    i = st.selectbox(_t("Alimento recente", "Recent food"), range(len(recentes)),
                     format_func=lambda i: f"{foods.nome(recentes[i]['nome'])} "
                                           f"({recentes[i]['gramas']:.0f} g)",
                     key=f"{prefixo}_rec_sel")
    r = recentes[i]
    gramas = st.number_input(_t("Peso (g/ml)", "Weight (g/ml)"), 1.0, 2000.0, float(r["gramas"]),
                             step=10.0, key=f"{prefixo}_rec_g")
    st.caption(f"➡️ {gramas:.0f} g · {_resumo(nutrients.escalar(r['por_100g'], gramas))}")
    if st.button(_t("➕ Adicionar à refeição", "➕ Add to meal"), key=f"{prefixo}_rec_add", type="primary"):
        cesto.append({"nome": r["nome"], "gramas": float(gramas), "por_100g": r["por_100g"]})
        st.rerun()


def _aba_comuns(cesto: list, prefixo: str, uid) -> None:
    cat = st.selectbox(_t("Categoria", "Category"), _categorias(uid), key=f"{prefixo}_cat",
                       format_func=foods.categoria_nome)
    lista = _alimentos(cat, uid)
    idx = st.selectbox(_t("Alimento", "Food"), range(len(lista)),
                       format_func=lambda i: foods.nome(lista[i]["nome"]), key=f"{prefixo}_al_{cat}")
    alimento = lista[idx]

    porcoes = alimento["porcoes"]
    custom = _t("✏️ Peso personalizado", "✏️ Custom weight")
    etiquetas = [f"{foods.porcao(lbl)} ({g} g)" for lbl, g in porcoes] + [custom]
    escolha = st.radio(_t("Porção", "Portion"), etiquetas, horizontal=True, key=f"{prefixo}_po_{cat}_{idx}")
    if escolha == custom:
        gramas = st.number_input(_t("Peso (g/ml)", "Weight (g/ml)"), 1.0, 2000.0, 100.0, step=10.0,
                                 key=f"{prefixo}_gc_{cat}_{idx}")
    else:
        base_g = porcoes[etiquetas.index(escolha)][1]
        qtd = st.number_input(_t("Quantidade", "Quantity"), 1, 20, 1, key=f"{prefixo}_qt_{cat}_{idx}")
        gramas = base_g * qtd

    nut = nutrients.escalar(alimento["por_100g"], gramas)
    st.caption(f"➡️ {gramas:.0f} g · {_resumo(nut)}")
    if st.button(_t("➕ Adicionar à refeição", "➕ Add to meal"), key=f"{prefixo}_add_comum", type="primary"):
        cesto.append({"nome": alimento["nome"], "gramas": float(gramas),
                      "por_100g": alimento["por_100g"]})
        st.rerun()


def _aba_off(cesto: list, prefixo: str, pais: str) -> None:
    st.caption(_t(f"Produtos de marca na Open Food Facts ({pais.upper()}). Gratuito, sem chave. "
                  "Escreve e carrega **Enter** para procurar.",
                  f"Branded products on Open Food Facts ({pais.upper()}). Free, no key. "
                  "Type and press **Enter** to search."))
    with st.form(f"{prefixo}_off_form"):
        c1, c2 = st.columns([3, 1])
        termo = c1.text_input(_t("Produto ou marca", "Product or brand"), key=f"{prefixo}_termo",
                              label_visibility="collapsed",
                              placeholder=_t("Ex.: iogurte grego, bolachas belVita…",
                                             "E.g.: greek yogurt, digestive biscuits…"))
        if c2.form_submit_button(_t("🔍 Pesquisar", "🔍 Search"), use_container_width=True):
            try:
                with st.spinner(_t("A procurar na Open Food Facts…", "Searching Open Food Facts…")):
                    st.session_state[f"{prefixo}_res"] = off.pesquisar(termo, pais)
            except ValueError as e:
                st.error(str(e))
                st.session_state[f"{prefixo}_res"] = []

    with st.expander(_t("📷 Tenho o código de barras", "📷 I have the barcode")):
        if barcode.DISPONIVEL:
            ligar = st.toggle(_t("📸 Ler com a câmara", "📸 Scan with camera"),
                              key=f"{prefixo}_cam_on",
                              help=_t("Tira uma foto ao código de barras — eu leio-o e procuro "
                                      "o produto automaticamente.",
                                      "Take a photo of the barcode — I'll read it and look the "
                                      "product up automatically."))
            if ligar:
                foto = st.camera_input(_t("Aponta ao código de barras (bem iluminado e focado)",
                                          "Point at the barcode (well lit and in focus)"),
                                       key=f"{prefixo}_cam")
                if foto is not None:
                    codigo = barcode.ler(foto)
                    if not codigo:
                        st.warning(_t("Não consegui ler o código 😕 — aproxima a câmara, foca e "
                                      "tenta outra vez (ou escreve-o em baixo).",
                                      "Couldn't read the code 😕 — move closer, focus and try "
                                      "again (or type it below)."))
                    elif st.session_state.get(f"{prefixo}_cb_lido") != codigo:
                        st.session_state[f"{prefixo}_cb_lido"] = codigo
                        try:
                            with st.spinner(_t(f"Li **{codigo}** — a procurar…",
                                               f"Read **{codigo}** — searching…")):
                                st.session_state[f"{prefixo}_res"] = [off.por_codigo(codigo, pais)]
                            st.rerun()
                        except ValueError as e:
                            st.error(f"📷 {codigo}: {e}")
        with st.form(f"{prefixo}_cb_form"):
            cb = st.text_input(_t("Código de barras", "Barcode"), key=f"{prefixo}_cb",
                               placeholder="Ex.: 5601234567890")
            if st.form_submit_button(_t("Procurar código", "Search barcode")) and cb.strip():
                try:
                    with st.spinner(_t("A procurar…", "Searching…")):
                        st.session_state[f"{prefixo}_res"] = [off.por_codigo(cb.strip(), pais)]
                except ValueError as e:
                    st.error(str(e))

    res = st.session_state.get(f"{prefixo}_res")
    if res:
        i = st.selectbox(_t("Resultado", "Result"), range(len(res)),
                         format_func=lambda i: res[i]["nome"], key=f"{prefixo}_sel")
        prod = res[i]
        if prod.get("quantidade"):
            st.caption(_t("Embalagem", "Package") + f": {prod['quantidade']}")
        micros = sum(1 for c in _MICROS if prod["por_100g"].get(c, 0) > 0)
        if micros < 5:
            enriquecido, fonte = off.enriquecer(prod)
            if fonte:
                prod = enriquecido
                st.info(_t(f"ℹ️ A Open Food Facts não tinha as vitaminas/minerais deste produto — "
                           f"**estimei** a partir de «{fonte}» (alimento parecido). Valores "
                           "aproximados; podes corrigir o peso/escolher outro produto.",
                           f"ℹ️ Open Food Facts had no vitamins/minerals for this product — "
                           f"I **estimated** them from “{fonte}” (a similar food). Approximate "
                           "values; you can adjust the weight or pick another product."))
            else:
                st.warning(_t(f"⚠️ Este produto só tem **{micros} de {len(_MICROS)}** "
                              "vitaminas/minerais na Open Food Facts. Os que faltam contam como 0 "
                              "— as pontuações e carências podem ficar subestimadas.",
                              f"⚠️ This product only has **{micros} of {len(_MICROS)}** "
                              "vitamins/minerals on Open Food Facts. Missing ones count as 0 "
                              "— scores and deficiencies may be underestimated."))
        gramas = st.number_input(_t("Peso consumido (g/ml)", "Amount eaten (g/ml)"),
                                 1.0, 2000.0, 100.0, step=10.0, key=f"{prefixo}_g")
        st.caption(f"➡️ {gramas:.0f} g · {_resumo(nutrients.escalar(prod['por_100g'], gramas))}")
        if st.button(_t("➕ Adicionar à refeição", "➕ Add to meal"), key=f"{prefixo}_add_off", type="primary"):
            cesto.append({"nome": prod["nome"], "gramas": float(gramas),
                          "por_100g": prod["por_100g"]})
            st.rerun()
    elif res == []:
        st.info(_t("Sem resultados com valores nutricionais. Tenta outro termo ou os "
                   "alimentos comuns.",
                   "No results with nutrition values. Try another term or the common foods."))


def mostrar_itens(cesto: list, prefixo: str, sexo: str | None = None,
                  alvos: dict | None = None) -> None:
    """Lista os itens do cesto, com detalhe por alimento e botão de remover."""
    for j, item in enumerate(cesto):
        nut = nutrients.escalar(item["por_100g"], item["gramas"])
        nome_disp = foods.nome(item["nome"])
        c1, c2, c3 = st.columns([5, 1.4, 0.8])
        c1.markdown(f"**{nome_disp} · {item['gramas']:.0f} g** — "
                    f"{nut['kcal']:.0f} kcal, {nut['proteina_g']:.0f} g " + _t("proteína", "protein"))
        with c2.popover(_t("🔍 Detalhe", "🔍 Details")):
            st.markdown(_t(f"**{nome_disp} ({item['gramas']:.0f} g) dá-te:**",
                           f"**{nome_disp} ({item['gramas']:.0f} g) gives you:**"))
            st.markdown(components.lista_nutrientes(nut, sexo, alvos))
        if c3.button("🗑️", key=f"{prefixo}_rm_{j}", help=_t("Remover", "Remove")):
            cesto.pop(j)
            st.rerun()
