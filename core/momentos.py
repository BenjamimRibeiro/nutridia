"""Momentos do dia para classificar as refeições."""
from datetime import datetime

MOMENTOS = ["Pequeno-almoço", "Almoço", "Lanche", "Jantar", "Ceia", "Snack"]

EMOJI = {"Pequeno-almoço": "🌅", "Almoço": "🍲", "Lanche": "🥪", "Jantar": "🌙",
         "Ceia": "🌜", "Snack": "🍎", "Outras": "🍽️"}


def emoji(momento: str | None) -> str:
    return EMOJI.get(momento or "", "🍽️")


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
