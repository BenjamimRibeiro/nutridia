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
