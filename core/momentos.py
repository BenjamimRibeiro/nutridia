"""Momentos do dia para classificar as refeições."""
from datetime import datetime

from core import i18n

MOMENTOS = ["Pequeno-almoço", "Almoço", "Lanche", "Jantar", "Ceia", "Snack"]

EMOJI = {"Pequeno-almoço": "🌅", "Almoço": "🍲", "Lanche": "🥪", "Jantar": "🌙",
         "Ceia": "🌜", "Snack": "🍎", "Outras": "🍽️"}

_EN = {"Pequeno-almoço": "Breakfast", "Almoço": "Lunch", "Lanche": "Snack", "Jantar": "Dinner",
       "Ceia": "Supper", "Snack": "Snack", "Outras": "Other"}


def emoji(momento: str | None) -> str:
    return EMOJI.get(momento or "", "🍽️")


def nome(momento: str | None) -> str:
    """Nome do momento no idioma ativo (o valor guardado mantém-se em PT)."""
    m = momento or "Outras"
    return _EN.get(m, m) if i18n.idioma() == "en" else m


def sugerir(hora: int | None = None) -> str:
    """Sugere o momento provável com base na hora (0-23)."""
    h = datetime.now().hour if hora is None else hora
    if h < 11:
        return "Pequeno-almoço"
    if h < 15:
        return "Almoço"
    if h < 18:
        return "Lanche"
    if h < 22:
        return "Jantar"
    return "Ceia"
