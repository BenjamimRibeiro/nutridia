"""Condições de saúde (patologias) — nutriente a moderar e orientação por condição.

⚕️ Os limites aqui são apenas orientativos para ajudar a moderar; NÃO substituem
aconselhamento médico. O utilizador deve seguir sempre as indicações do seu médico.
"""
from core import i18n

# nome -> nutriente a moderar (chave de nutrients.LIMITES), limite mais apertado
# sugerido (mais baixo que o limite geral da app) e conselho alimentar.
CONDICOES = {
    "Diabetes": {
        "emoji": "🩸",
        "nutriente": "acucar_g",
        "limite": 25,  # geral da app: 50 g
        "conselho": "Modera o açúcar e os hidratos rápidos; prefere fibra, leguminosas e "
                    "cereais integrais, que fazem subir menos a glicose.",
    },
    "Tensão alta": {
        "emoji": "🫀",
        "nutriente": "sodio_mg",
        "limite": 1500,  # geral da app: 2300 mg
        "conselho": "Reduz o sal e os alimentos processados; o potássio (banana, legumes) "
                    "ajuda a equilibrar a tensão arterial.",
    },
    "Colesterol alto": {
        "emoji": "🧈",
        "nutriente": "gordura_saturada_g",
        "limite": 15,  # geral da app: 22 g
        "conselho": "Modera a gordura saturada (carnes gordas, fritos, lacticínios gordos); "
                    "aveia, leguminosas e azeite ajudam a baixar o colesterol.",
    },
}

LISTA = list(CONDICOES)

_EN_NOME = {"Diabetes": "Diabetes", "Tensão alta": "High blood pressure",
            "Colesterol alto": "High cholesterol"}
_EN_CONSELHO = {
    "Diabetes": "Go easy on sugar and fast carbs; prefer fibre, legumes and wholegrains, "
                "which raise blood glucose more slowly.",
    "Tensão alta": "Cut down on salt and processed foods; potassium (banana, vegetables) "
                   "helps balance blood pressure.",
    "Colesterol alto": "Go easy on saturated fat (fatty meats, fried food, full-fat dairy); "
                       "oats, legumes and olive oil help lower cholesterol.",
}


def nome(c: str) -> str:
    return _EN_NOME.get(c, c) if i18n.idioma() == "en" else c


def conselho(c: str) -> str:
    return _EN_CONSELHO.get(c, "") if i18n.idioma() == "en" else CONDICOES[c]["conselho"]


def nutriente(c: str) -> str:
    return CONDICOES[c]["nutriente"]


def limite(c: str) -> float:
    return CONDICOES[c]["limite"]


def emoji(c: str) -> str:
    return CONDICOES[c]["emoji"]


def limites_efetivos(condicoes_ativas: list[str] | None) -> dict[str, dict]:
    """Limites diários a moderar: os gerais da app, apertados pelas condições ativas.

    Devolve {chave: {"limite": float, "por_condicao": nome_da_condicao | None}}."""
    from core import nutrients
    efetivos = {c: {"limite": info["limite"], "por_condicao": None}
                for c, info in nutrients.LIMITES.items()}
    for cond in condicoes_ativas or []:
        cfg = CONDICOES.get(cond)
        if cfg and cfg["limite"] < efetivos[cfg["nutriente"]]["limite"]:
            efetivos[cfg["nutriente"]] = {"limite": cfg["limite"], "por_condicao": cond}
    return efetivos


def semaforo_refeicao(totais: dict, condicoes_ativas: list[str] | None = None) -> list[dict]:
    """Avalia uma refeição nos nutrientes a moderar vs limite DIÁRIO efetivo.

    Cor pela fatia do limite diário que a refeição gasta: 🟢 ≤25%, 🟡 ≤50%, 🔴 >50%.
    Devolve [{chave, emoji, consumido, limite, fracao, por_condicao}] (cafeína só se >0)."""
    resultado = []
    for chave, info in limites_efetivos(condicoes_ativas).items():
        consumido = totais.get(chave, 0)
        if chave == "cafeina_mg" and consumido <= 0:
            continue
        fracao = consumido / info["limite"] if info["limite"] else 0.0
        cor = "🟢" if fracao <= 0.25 else ("🟡" if fracao <= 0.50 else "🔴")
        resultado.append({"chave": chave, "emoji": cor, "consumido": consumido,
                          "limite": info["limite"], "fracao": fracao,
                          "por_condicao": info["por_condicao"]})
    return resultado
