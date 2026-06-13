"""Exposição solar → vitamina D produzida pela pele (estimativa diária).

O sol é a principal fonte de vitamina D. Valores aproximados de síntese cutânea
para uma exposição típica (cara/braços, sol do meio-dia), em µg/dia.
"""
NIVEIS = {
    "Nenhuma (quase sempre dentro)": 0,
    "Pouca (~10 min/dia)": 5,
    "Moderada (15–30 min/dia)": 20,
    "Boa (30–45 min/dia)": 30,
    "Bastante (>45 min ao ar livre)": 40,
}

PREDEFINIDO = "Pouca (~10 min/dia)"

_EN = {
    "Nenhuma (quase sempre dentro)": "None (mostly indoors)",
    "Pouca (~10 min/dia)": "Little (~10 min/day)",
    "Moderada (15–30 min/dia)": "Moderate (15–30 min/day)",
    "Boa (30–45 min/dia)": "Good (30–45 min/day)",
    "Bastante (>45 min ao ar livre)": "Lots (>45 min outdoors)",
}


def vit_d(nivel: str | None) -> float:
    return NIVEIS.get(nivel or "", 0)


def nome(nivel: str) -> str:
    from core import i18n
    return _EN.get(nivel, nivel) if i18n.idioma() == "en" else nivel
