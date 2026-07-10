"""Álcool das bebidas alcoólicas.

A app NÃO segue o álcool como nutriente (não há campo próprio). Mas conhece as
bebidas alcoólicas para penalizar as pontuações de bem-estar que o álcool, em
EXCESSO, prejudica (sono, humor, foco…). Só penaliza acima de um limite diário —
beber com moderação não corta pontuações.
"""

# gramas de álcool puro por 100 g/ml de bebida (≈ %vol × 0,789)
_ALCOOL_G_100 = {
    "Cerveja": 4.0,       # ~5% vol
    "Vinho tinto": 10.3,  # ~13% vol
}

# a partir de ~2 bebidas padrão (≈20 g de álcool) começa a penalizar
LIMITE_DIARIO_G = 20.0


def gramas_em(nome: str, gramas: float) -> float:
    """Gramas de álcool puro numa porção (0 se a bebida não for alcoólica)."""
    return _ALCOOL_G_100.get(nome, 0.0) * gramas / 100.0


def gramas_do_dia(refeicoes: list) -> float:
    """Álcool total (g) das bebidas alcoólicas registadas nas refeições do dia."""
    total = 0.0
    for ref in refeicoes:
        for item in ref.get("itens") or []:
            total += gramas_em(item.get("nome", ""), item.get("gramas", 0))
    return total


def excesso(alcool_g: float) -> float:
    """0 se dentro do limite; sobe até 1 quando o álcool duplica o limite (satura aí)."""
    if alcool_g <= LIMITE_DIARIO_G:
        return 0.0
    return min((alcool_g - LIMITE_DIARIO_G) / LIMITE_DIARIO_G, 1.0)
