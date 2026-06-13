"""Tradução simples PT/EN. `t(pt, en)` devolve a string no idioma ativo."""

_IDIOMA = "pt"


def definir(idioma_: str) -> None:
    global _IDIOMA
    _IDIOMA = "en" if str(idioma_).lower().startswith("en") else "pt"


def idioma() -> str:
    return _IDIOMA


def t(pt: str, en: str) -> str:
    return en if _IDIOMA == "en" else pt
