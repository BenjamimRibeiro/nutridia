"""Refeições inteligentes — sugestões de alimentos para tapar carências ou
preencher o que falta hoje, respeitando alergias e preferências."""
from core import dieta, foods, nutrients


def _compativeis(alergias: list[str], preferencias: list[str]) -> list[dict]:
    return [a for a in foods.ALIMENTOS if dieta.compativel(a, alergias, preferencias)]


def _porcao(alimento: dict) -> tuple[str, int]:
    return alimento["porcoes"][0]


def para_carencia(chave: str, alergias: list[str], preferencias: list[str],
                  n: int = 3) -> list[dict]:
    """Top-N alimentos compatíveis que mais fornecem o nutriente `chave` (por porção)."""
    resultado = []
    for alimento in _compativeis(alergias, preferencias):
        rotulo, gramas = _porcao(alimento)
        aporte = nutrients.escalar(alimento["por_100g"], gramas).get(chave, 0)
        if aporte > 0:
            resultado.append({"nome": alimento["nome"], "rotulo": rotulo,
                              "gramas": gramas, "aporte": aporte})
    resultado.sort(key=lambda x: x["aporte"], reverse=True)
    return resultado[:n]


def para_agora(totais: dict, alvos: dict, alergias: list[str],
               preferencias: list[str], n: int = 3) -> dict:
    """Sugere alimentos ricos em proteína que cabem nas calorias que faltam hoje."""
    falta_prot = alvos["proteina_g"] - totais.get("proteina_g", 0)
    resto_kcal = alvos["kcal"] - totais.get("kcal", 0)
    if falta_prot < 8 or resto_kcal < 80:
        return {"falta_prot": falta_prot, "resto_kcal": resto_kcal, "alimentos": []}

    candidatos = []
    for alimento in _compativeis(alergias, preferencias):
        rotulo, gramas = _porcao(alimento)
        nut = nutrients.escalar(alimento["por_100g"], gramas)
        if 0 < nut["kcal"] <= resto_kcal * 1.2 and nut["proteina_g"] >= 5:
            candidatos.append({"nome": alimento["nome"], "rotulo": rotulo, "gramas": gramas,
                               "kcal": nut["kcal"], "proteina_g": nut["proteina_g"]})
    candidatos.sort(key=lambda x: x["proteina_g"], reverse=True)
    return {"falta_prot": falta_prot, "resto_kcal": resto_kcal, "alimentos": candidatos[:n]}
