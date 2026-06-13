"""Construtor de refeição reutilizável — usado no Registar e na edição do Histórico.

Um "cesto" é uma lista de itens {nome, gramas, por_100g}. Os nutrientes são
calculados a partir de por_100g + gramas sempre que necessário (nutrients.escalar).
"""
import streamlit as st

from core import db, foods, nutrients
from core import openfoodfacts as off
from views import components

# vitaminas/minerais (exceto fibra) — para o aviso de dados em falta na OFF
_MICROS = [c for c in nutrients.DDR if c != "fibra_g"]
_CAT_MEUS = "⭐ Os meus"


def _resumo(nut: dict) -> str:
    return (f"{nut.get('kcal', 0):.0f} kcal · {nut.get('proteina_g', 0):.0f} g prot · "
            f"{nut.get('hidratos_g', 0):.0f} g hid · {nut.get('gordura_g', 0):.0f} g gord")


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


def adicionar_alimento(cesto: list, prefixo: str, pais: str, uid=None) -> None:
    """Separadores para escolher um alimento (comuns/OFF/recentes) e juntar ao cesto."""
    recentes = db.alimentos_recentes(uid) if uid is not None else []
    etiquetas = ["🍎 Alimentos", "🔍 Pesquisar produto"] + (["🕘 Recentes"] if recentes else [])
    tabs = st.tabs(etiquetas)
    with tabs[0]:
        _aba_comuns(cesto, prefixo, uid)
    with tabs[1]:
        _aba_off(cesto, prefixo, pais)
    if recentes:
        with tabs[2]:
            _aba_recentes(cesto, prefixo, recentes)


def _aba_recentes(cesto: list, prefixo: str, recentes: list) -> None:
    st.caption("Os teus alimentos mais recentes — com a porção que usaste da última vez.")
    i = st.selectbox("Alimento recente", range(len(recentes)),
                     format_func=lambda i: f"{recentes[i]['nome']} ({recentes[i]['gramas']:.0f} g)",
                     key=f"{prefixo}_rec_sel")
    r = recentes[i]
    gramas = st.number_input("Peso (g/ml)", 1.0, 2000.0, float(r["gramas"]), step=10.0,
                             key=f"{prefixo}_rec_g")
    st.caption(f"➡️ {gramas:.0f} g · {_resumo(nutrients.escalar(r['por_100g'], gramas))}")
    if st.button("➕ Adicionar à refeição", key=f"{prefixo}_rec_add", type="primary"):
        cesto.append({"nome": r["nome"], "gramas": float(gramas), "por_100g": r["por_100g"]})
        st.rerun()


def _aba_comuns(cesto: list, prefixo: str, uid) -> None:
    cat = st.selectbox("Categoria", _categorias(uid), key=f"{prefixo}_cat")
    lista = _alimentos(cat, uid)
    idx = st.selectbox("Alimento", range(len(lista)),
                       format_func=lambda i: lista[i]["nome"], key=f"{prefixo}_al_{cat}")
    alimento = lista[idx]

    porcoes = alimento["porcoes"]
    etiquetas = [f"{lbl} ({g} g)" for lbl, g in porcoes] + ["✏️ Peso personalizado"]
    escolha = st.radio("Porção", etiquetas, horizontal=True, key=f"{prefixo}_po_{cat}_{idx}")
    if escolha == "✏️ Peso personalizado":
        gramas = st.number_input("Peso (g/ml)", 1.0, 2000.0, 100.0, step=10.0,
                                 key=f"{prefixo}_gc_{cat}_{idx}")
    else:
        base_g = porcoes[etiquetas.index(escolha)][1]
        qtd = st.number_input("Quantidade", 1, 20, 1, key=f"{prefixo}_qt_{cat}_{idx}")
        gramas = base_g * qtd

    nut = nutrients.escalar(alimento["por_100g"], gramas)
    st.caption(f"➡️ {gramas:.0f} g · {_resumo(nut)}")
    if st.button("➕ Adicionar à refeição", key=f"{prefixo}_add_comum", type="primary"):
        cesto.append({"nome": alimento["nome"], "gramas": float(gramas),
                      "por_100g": alimento["por_100g"]})
        st.rerun()


def _aba_off(cesto: list, prefixo: str, pais: str) -> None:
    st.caption(f"Produtos de marca na Open Food Facts ({pais.upper()}). Gratuito, sem chave. "
               "Escreve e carrega **Enter** para procurar.")
    with st.form(f"{prefixo}_off_form"):
        c1, c2 = st.columns([3, 1])
        termo = c1.text_input("Produto ou marca", key=f"{prefixo}_termo",
                              label_visibility="collapsed",
                              placeholder="Ex.: iogurte grego, bolachas belVita…")
        if c2.form_submit_button("🔍 Pesquisar", use_container_width=True):
            try:
                with st.spinner("A procurar na Open Food Facts…"):
                    st.session_state[f"{prefixo}_res"] = off.pesquisar(termo, pais)
            except ValueError as e:
                st.error(str(e))
                st.session_state[f"{prefixo}_res"] = []

    with st.expander("📷 Tenho o código de barras"):
        with st.form(f"{prefixo}_cb_form"):
            cb = st.text_input("Código de barras", key=f"{prefixo}_cb",
                               placeholder="Ex.: 5601234567890")
            if st.form_submit_button("Procurar código") and cb.strip():
                try:
                    with st.spinner("A procurar…"):
                        st.session_state[f"{prefixo}_res"] = [off.por_codigo(cb.strip(), pais)]
                except ValueError as e:
                    st.error(str(e))

    res = st.session_state.get(f"{prefixo}_res")
    if res:
        i = st.selectbox("Resultado", range(len(res)),
                         format_func=lambda i: res[i]["nome"], key=f"{prefixo}_sel")
        prod = res[i]
        if prod.get("quantidade"):
            st.caption(f"Embalagem: {prod['quantidade']}")
        micros = sum(1 for c in _MICROS if prod["por_100g"].get(c, 0) > 0)
        if micros < 5:
            enriquecido, fonte = off.enriquecer(prod)
            if fonte:
                prod = enriquecido
                st.info(f"ℹ️ A Open Food Facts não tinha as vitaminas/minerais deste produto — "
                        f"**estimei** a partir de «{fonte}» (alimento parecido). Valores aproximados; "
                        "podes corrigir o peso/escolher outro produto.")
            else:
                st.warning(f"⚠️ Este produto só tem **{micros} de {len(_MICROS)}** "
                           "vitaminas/minerais na Open Food Facts. Os que faltam contam como 0 "
                           "— as pontuações e carências podem ficar subestimadas.")
        gramas = st.number_input("Peso consumido (g/ml)", 1.0, 2000.0, 100.0, step=10.0,
                                 key=f"{prefixo}_g")
        st.caption(f"➡️ {gramas:.0f} g · {_resumo(nutrients.escalar(prod['por_100g'], gramas))}")
        if st.button("➕ Adicionar à refeição", key=f"{prefixo}_add_off", type="primary"):
            cesto.append({"nome": prod["nome"], "gramas": float(gramas),
                          "por_100g": prod["por_100g"]})
            st.rerun()
    elif res == []:
        st.info("Sem resultados com valores nutricionais. Tenta outro termo ou os "
                "alimentos comuns.")


def mostrar_itens(cesto: list, prefixo: str, sexo: str | None = None,
                  alvos: dict | None = None) -> None:
    """Lista os itens do cesto, com detalhe por alimento e botão de remover."""
    for j, item in enumerate(cesto):
        nut = nutrients.escalar(item["por_100g"], item["gramas"])
        c1, c2, c3 = st.columns([5, 1.4, 0.8])
        c1.markdown(f"**{item['nome']} · {item['gramas']:.0f} g** — "
                    f"{nut['kcal']:.0f} kcal, {nut['proteina_g']:.0f} g proteína")
        with c2.popover("🔍 Detalhe"):
            st.markdown(f"**{item['nome']} ({item['gramas']:.0f} g) dá-te:**")
            st.markdown(components.lista_nutrientes(nut, sexo, alvos))
        if c3.button("🗑️", key=f"{prefixo}_rm_{j}", help="Remover"):
            cesto.pop(j)
            st.rerun()
