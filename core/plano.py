"""Plano semanal de refeições — gerado da tabela local de alimentos, respeitando
alvos de calorias, alergias, preferências e condições de saúde do perfil."""
import random

from core import dieta, foods, i18n, nutrients, sugestoes

DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
_DIAS_EN = {"Segunda": "Monday", "Terça": "Tuesday", "Quarta": "Wednesday",
            "Quinta": "Thursday", "Sexta": "Friday", "Sábado": "Saturday",
            "Domingo": "Sunday"}

# hidratos de "Pão e cereais" que não fazem sentido ao pequeno-almoço/lanche
_NAO_PEQALMOCO = ["batata", "arroz", "massa", "esparguete"]
# ingredientes/temperos que NUNCA são prato ou snack sozinhos (removidos do pool).
# Deteção pelo INÍCIO do nome (o item É o ingrediente) — assim "Natas (para cozinhar)"
# sai mas "Bacalhau com natas" (prato) fica.
_INGREDIENTE_INICIO = [
    "natas", "azeite", "manteiga", "oleo", "banha", "margarina", "vinagre",
    "alho", "cebola", "molho", "maionese", "ketchup", "mostarda", "pesto",
]
# … e alguns detetados por conterem a palavra (toppings/temperos)
_INGREDIENTE_CONTEM = ["ralado", "bechamel"]


def _e_ingrediente(nome: str) -> bool:
    n = nutrients.normalizar(nome)
    return (any(n.startswith(k) for k in _INGREDIENTE_INICIO)
            or any(k in n for k in _INGREDIENTE_CONTEM))

# (momento, emoji, fração das kcal do dia, slots de categorias — 1 alimento por slot)
_REFEICOES = [
    ("Pequeno-almoço", "🌅", 0.22, [["Pão e cereais"], ["Lacticínios"], ["Fruta"]]),
    ("Almoço", "🍽️", 0.33, [["Sopas e pratos"], ["Vegetais", "Fruta"]]),
    ("Lanche", "🥪", 0.15, [["Lacticínios", "Fruta", "Gorduras e frutos secos",
                             "Pão e cereais"]]),
    ("Jantar", "🌙", 0.30, [["Sopas e pratos", "Carne", "Peixe"],
                            ["Vegetais", "Leguminosas"], ["Fruta"]]),
]


_MOMENTOS_EN = {"Pequeno-almoço": "Breakfast", "Almoço": "Lunch",
                "Lanche": "Snack", "Jantar": "Dinner"}


def dia_nome(d: str) -> str:
    return _DIAS_EN.get(d, d) if i18n.idioma() == "en" else d


def momento_nome(m: str) -> str:
    return _MOMENTOS_EN.get(m, m) if i18n.idioma() == "en" else m


def _pool(perfil: dict) -> dict[str, list[dict]]:
    """Alimentos compatíveis com o perfil, agrupados por categoria."""
    alergias = perfil.get("alergias", [])
    prefs = perfil.get("restricoes", [])
    cond = perfil.get("condicoes", [])
    grupos: dict[str, list[dict]] = {}
    for a in foods.ALIMENTOS:
        if not dieta.compativel(a, alergias, prefs):
            continue
        if _e_ingrediente(a["nome"]):
            continue  # ingrediente/tempero — nunca é prato nem snack sozinho
        nut = nutrients.escalar(a["por_100g"], a["porcoes"][0][1])
        if sugestoes.fator_condicoes(nut, cond) is None:
            continue
        grupos.setdefault(a["categoria"], []).append(a)
    return grupos


def gerar(perfil: dict, alvos: dict, semente: int = 0) -> list[dict]:
    """Plano de 7 dias. Devolve [{dia, refeicoes: [{momento, emoji, itens, kcal}], kcal}]
    onde itens = [(nome_alimento, rotulo_porcao, gramas, kcal)]."""
    rng = random.Random(semente)
    grupos = _pool(perfil)
    kcal_dia = alvos["kcal"]
    plano = []
    usados_ontem: set[str] = set()

    for dia in DIAS:
        refeicoes_dia = []
        usados_hoje: set[str] = set()
        for momento, emoji, fracao, slots in _REFEICOES:
            alvo_kcal = kcal_dia * fracao
            itens, kcal_ref = [], 0.0
            for cats in slots:
                resto = alvo_kcal - kcal_ref
                if resto < 40:
                    break
                candidatos = []
                for cat in cats:
                    for a in grupos.get(cat, []):
                        nome_norm = nutrients.normalizar(a["nome"])
                        if momento in ("Pequeno-almoço", "Lanche") and \
                                any(kw in nome_norm for kw in _NAO_PEQALMOCO):
                            continue
                        rotulo, gramas = a["porcoes"][0]
                        k = nutrients.escalar(a["por_100g"], gramas)["kcal"]
                        # cabe no que resta (com folga) e dá variedade
                        if 0 < k <= resto * 1.25 and a["nome"] not in usados_hoje:
                            peso = 0.35 if a["nome"] in usados_ontem else 1.0
                            candidatos.append((peso, a, rotulo, gramas, k))
                if not candidatos:
                    continue
                pesos = [c[0] for c in candidatos]
                _, a, rotulo, gramas, k = rng.choices(candidatos, weights=pesos, k=1)[0]
                itens.append((a["nome"], rotulo, gramas, k))
                usados_hoje.add(a["nome"])
                kcal_ref += k
            # porções pequenas → escala até perto do alvo da refeição (máx. 2×)
            if itens and kcal_ref < alvo_kcal * 0.85:
                fator = min(alvo_kcal / kcal_ref, 2.0)
                itens = [(n, rot, round(g * fator), k * fator) for n, rot, g, k in itens]
                kcal_ref *= fator
            refeicoes_dia.append({"momento": momento, "emoji": emoji,
                                  "itens": itens, "kcal": kcal_ref})
        # reforço: se o dia ficou leve, acrescenta snacks ao lanche até ~90% do alvo
        kcal_total = sum(r["kcal"] for r in refeicoes_dia)
        lanche = next(r for r in refeicoes_dia if r["momento"] == "Lanche")
        tentativas = 0
        while kcal_total < kcal_dia * 0.90 and tentativas < 6:
            tentativas += 1
            falta = kcal_dia - kcal_total
            candidatos = []
            for cat in ("Gorduras e frutos secos", "Pão e cereais", "Lacticínios",
                        "Fruta", "Leguminosas"):
                for a in grupos.get(cat, []):
                    nome_norm = nutrients.normalizar(a["nome"])
                    if any(kw in nome_norm for kw in _NAO_PEQALMOCO) \
                            or a["nome"] in usados_hoje:
                        continue
                    rotulo, gramas = a["porcoes"][0]
                    k = nutrients.escalar(a["por_100g"], gramas)["kcal"]
                    if 0 < k <= falta * 1.1:
                        candidatos.append((a, rotulo, gramas, k))
            if not candidatos:
                break
            a, rotulo, gramas, k = max(candidatos, key=lambda c: c[3])  # o mais substancial
            lanche["itens"].append((a["nome"], rotulo, gramas, k))
            lanche["kcal"] += k
            usados_hoje.add(a["nome"])
            kcal_total += k
        plano.append({"dia": dia, "refeicoes": refeicoes_dia, "kcal": kcal_total})
        usados_ontem = usados_hoje
    return plano
