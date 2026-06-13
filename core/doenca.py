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


def conforto(tipo: str) -> dict:
    return CONFORTO.get(tipo, CONFORTO["Outra"])
