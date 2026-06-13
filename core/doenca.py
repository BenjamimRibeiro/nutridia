"""Modo doente — tipos de mal-estar e sugestões de conforto à base de comida.

⚠️ Informação de bem-estar alimentar, NÃO é conselho médico.
"""
TIPOS = ["Constipação", "Gripe", "Dor de garganta", "Febre",
         "Indisposição estomacal", "Outra"]

CONFORTO = {
    "Constipação": {
        "alimentos": "canja, sopas quentes, laranja e kiwi, mel e limão, gengibre, alho",
        "nutrientes": "Vitamina C, zinco e líquidos ajudam as defesas",
        "dica": "Bebe muitos líquidos quentes e descansa.",
    },
    "Gripe": {
        "alimentos": "canja, caldos, sopas, citrinos, gengibre, mel, chá",
        "nutrientes": "Líquidos, vitamina C e zinco para o sistema imunitário",
        "dica": "Repousa e hidrata-te bem; come leve e quente.",
    },
    "Dor de garganta": {
        "alimentos": "mel e limão, chá morno, sopas suaves, gelatina, alimentos macios",
        "nutrientes": "Líquidos mornos e mel acalmam a garganta",
        "dica": "Evita comida muito seca, picante ou ácida em excesso.",
    },
    "Febre": {
        "alimentos": "muita água, sopas, canja, fruta rica em água (melancia, laranja)",
        "nutrientes": "Hidratação é o mais importante; come leve",
        "dica": "Bebe líquidos com frequência mesmo sem fome.",
    },
    "Indisposição estomacal": {
        "alimentos": "arroz, banana, maçã, torrada, canja leve (dieta suave)",
        "nutrientes": "Alimentos simples e líquidos; repõe potássio (banana)",
        "dica": "Come pouco e muitas vezes; evita gordura e lacticínios por agora.",
    },
    "Outra": {
        "alimentos": "sopas, canja, fruta, muita água, alimentos leves",
        "nutrientes": "Hidratação e alimentos leves ajudam a recuperar",
        "dica": "Ouve o teu corpo, come leve e descansa.",
    },
}


_TIPOS_EN = {"Constipação": "Cold", "Gripe": "Flu", "Dor de garganta": "Sore throat",
             "Febre": "Fever", "Indisposição estomacal": "Upset stomach", "Outra": "Other"}

_CONFORTO_EN = {
    "Constipação": {
        "alimentos": "chicken soup, warm soups, orange and kiwi, honey and lemon, ginger, garlic",
        "nutrientes": "Vitamin C, zinc and fluids support your immune system",
        "dica": "Drink plenty of warm fluids and rest.",
    },
    "Gripe": {
        "alimentos": "chicken soup, broths, soups, citrus, ginger, honey, tea",
        "nutrientes": "Fluids, vitamin C and zinc for the immune system",
        "dica": "Rest and hydrate well; eat light and warm.",
    },
    "Dor de garganta": {
        "alimentos": "honey and lemon, warm tea, smooth soups, jelly, soft foods",
        "nutrientes": "Warm fluids and honey soothe the throat",
        "dica": "Avoid very dry, spicy or overly acidic food.",
    },
    "Febre": {
        "alimentos": "plenty of water, soups, chicken soup, water-rich fruit (watermelon, orange)",
        "nutrientes": "Hydration matters most; eat light",
        "dica": "Drink fluids often even without appetite.",
    },
    "Indisposição estomacal": {
        "alimentos": "rice, banana, apple, toast, light chicken soup (bland diet)",
        "nutrientes": "Simple foods and fluids; replace potassium (banana)",
        "dica": "Eat little and often; avoid fat and dairy for now.",
    },
    "Outra": {
        "alimentos": "soups, chicken soup, fruit, plenty of water, light foods",
        "nutrientes": "Hydration and light foods help you recover",
        "dica": "Listen to your body, eat light and rest.",
    },
}


def nome(tipo: str) -> str:
    from core import i18n
    return _TIPOS_EN.get(tipo, tipo) if i18n.idioma() == "en" else tipo


def conforto(tipo: str) -> dict:
    from core import i18n
    if i18n.idioma() == "en":
        return _CONFORTO_EN.get(tipo, _CONFORTO_EN["Outra"])
    return CONFORTO.get(tipo, CONFORTO["Outra"])
