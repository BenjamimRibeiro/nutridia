"""Refeições inteligentes — sugestões de alimentos para tapar carências ou
preencher o que falta hoje, respeitando alergias e preferências."""
import random

from core import dieta, foods, nutrients

_TREAT = "Doces e snacks"


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


def para_agora(totais: dict, alvos: dict, sexo: str, alergias: list[str],
               preferencias: list[str], n: int = 4) -> dict:
    """Sugere alimentos saudáveis e variados que dão o que ainda falta hoje (não só
    proteína/calorias — também micronutrientes), mais um miminho ocasional que caiba."""
    resto_kcal = alvos["kcal"] - totais.get("kcal", 0)
    resultado = {"resto_kcal": resto_kcal, "saudaveis": [], "treat": None}
    if resto_kcal < 60:
        return resultado

    # o que ainda falta hoje: proteína, fibra e micros (vitaminas/minerais)
    chaves = ["proteina_g", "fibra_g"] + list(nutrients.DDR)
    gaps = {}
    for c in chaves:
        alvo = nutrients.alvo_nutriente(c, sexo, alvos)
        if alvo:
            falta = alvo - totais.get(c, 0)
            if falta > 0:
                gaps[c] = falta

    pontuados = []
    for alimento in _compativeis(alergias, preferencias):
        if alimento["categoria"] == _TREAT:
            continue
        rotulo, gramas = _porcao(alimento)
        nut = nutrients.escalar(alimento["por_100g"], gramas)
        if not (0 < nut["kcal"] <= resto_kcal * 1.15):
            continue
        cobre, score = [], 0.0
        for c, falta in gaps.items():
            if nut.get(c, 0) > 0:
                fracao = min(nut[c] / falta, 1.0)
                if fracao >= 0.12:
                    # micros valem mais que proteína/calorias → incentiva variedade saudável
                    peso = 1.0 if c in ("proteina_g", "fibra_g") else 1.5
                    score += fracao * peso
                    cobre.append((c, fracao))
        if score > 0:
            cobre.sort(key=lambda x: -x[1])
            pontuados.append({"nome": alimento["nome"], "categoria": alimento["categoria"],
                              "rotulo": rotulo, "gramas": gramas, "kcal": nut["kcal"],
                              "cobre": cobre, "score": score})
    pontuados.sort(key=lambda x: -x["score"])

    # diversificar: evitar repetir categoria ou o mesmo nutriente-topo
    saudaveis, cats, tops = [], set(), set()
    for p in pontuados:
        topo = p["cobre"][0][0]
        if p["categoria"] in cats or topo in tops:
            continue
        saudaveis.append(p)
        cats.add(p["categoria"])
        tops.add(topo)
        if len(saudaveis) >= n:
            break
    for p in pontuados:  # completa se faltarem, já sem a restrição de diversidade
        if len(saudaveis) >= n:
            break
        if p not in saudaveis:
            saudaveis.append(p)
    resultado["saudaveis"] = saudaveis

    # miminho: algo guloso compatível que caiba nas calorias que sobram
    treats = [a for a in _compativeis(alergias, preferencias)
              if a["categoria"] == _TREAT
              and 0 < nutrients.escalar(a["por_100g"], a["porcoes"][0][1])["kcal"] <= resto_kcal]
    if treats:
        a = random.choice(treats)
        rotulo, gramas = _porcao(a)
        resultado["treat"] = {"nome": a["nome"], "rotulo": rotulo, "gramas": gramas,
                              "kcal": nutrients.escalar(a["por_100g"], gramas)["kcal"]}
    return resultado
