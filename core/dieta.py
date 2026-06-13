"""Alergias e preferências alimentares — compatibilidade de alimentos por palavras-chave."""
from core import nutrients

PREFERENCIAS = ["Vegetariano", "Vegano", "Pescetariano", "Sem carne vermelha"]
ALERGIAS = ["Glúten", "Lactose", "Ovo", "Peixe", "Marisco", "Frutos de casca rija",
            "Amendoim", "Soja", "Frutos vermelhos", "Mostarda", "Sésamo", "Aipo"]

# palavras (sem acentos) que indicam o alergénio no nome do alimento
_ALERGIA_KW = {
    "Glúten": ["pao", "tosta", "massa", "bolacha", "bolo", "croissant", "broa", "francesinha",
               "lasanha", "esparguete", "rissol", "croquete", "pizza", "berlim", "queijada",
               "tarte", "cereais", "aletria", "migas", "acorda", "sonhos", "bola de bolacha",
               "bechamel", "panado", "empada"],
    "Lactose": ["leite", "queijo", "iogurte", "requeijao", "manteiga", "natas", "leite-creme",
                "gelado", "com natas", "pudim", "mousse", "tosta mista", "arroz doce", "kefir",
                "bechamel", "mozzarella", "parmesao", "philadelphia", "serra"],
    "Ovo": ["ovo", "omelete", "pudim", "mousse", "pastel de nata", "queijada", "rissol",
            "croquete", "sonhos", "leite-creme", "maionese", "panado"],
    "Peixe": ["bacalhau", "salmao", "atum", "sardinha", "peixe", "caldeirada", "pataniscas"],
    "Marisco": ["camarao", "marisco", "polvo"],
    "Frutos de casca rija": ["amendoa", "noz", "nozes", "pesto"],
    "Amendoim": ["amendoim"],
    "Soja": ["soja", "tofu"],
    "Frutos vermelhos": ["morango", "framboesa", "mirtilo", "amora", "frutos vermelhos"],
    "Mostarda": ["mostarda"],
    "Sésamo": ["sesamo", "tahini"],
    "Aipo": ["aipo"],
}

# palavras que tornam um alimento incompatível com uma preferência
_CARNE = ["frango", "vaca", "porco", "bife", "carne", "fiambre", "hamburguer", "rojoes",
          "bifana", "prego", "pato", "cozido", "feijoada", "alentejana", "bolonhesa",
          "jardineira", "bitoque", "caril de frango", "lombo", "canja", "rissol de carne",
          "croquete de carne", "francesinha", "lasanha"]
_CARNE_VERMELHA = ["vaca", "porco", "bife", "rojoes", "feijoada", "alentejana", "fiambre",
                   "hamburguer de vaca", "hamburguer de porco", "cozido"]
_PEIXE_MARISCO = _ALERGIA_KW["Peixe"] + _ALERGIA_KW["Marisco"]
_ANIMAL = (_CARNE + _PEIXE_MARISCO + _ALERGIA_KW["Lactose"] + ["ovo", "omelete", "mel"])

_PREF_KW = {
    "Vegetariano": _CARNE + _PEIXE_MARISCO,
    "Vegano": _ANIMAL,
    "Pescetariano": _CARNE,            # permite peixe/marisco
    "Sem carne vermelha": _CARNE_VERMELHA,
}


def _contem(nome_norm: str, palavras: list[str]) -> bool:
    return any(kw in nome_norm for kw in palavras)


def motivo_incompativel(food: dict, alergias: list[str], preferencias: list[str]) -> str | None:
    """Devolve o motivo se o alimento não serve, ou None se for compatível."""
    nome = nutrients.normalizar(food["nome"])
    for a in alergias:
        if _contem(nome, _ALERGIA_KW.get(a, [])):
            return f"contém {a.lower()}"
    for p in preferencias:
        if _contem(nome, _PREF_KW.get(p, [])):
            return "não vegano" if p == "Vegano" else f"não {p.lower()}"
    return None


def compativel(food: dict, alergias: list[str], preferencias: list[str]) -> bool:
    return motivo_incompativel(food, alergias, preferencias) is None
