"""Catálogo de nutrientes: doses diárias recomendadas (DDR) por sexo,
limites para nutrientes a moderar, e o que sentes quando faltam."""
import unicodedata

# Conjunto canónico de nutrientes seguidos pela app (totais de uma refeição).
# Tem de coincidir com as chaves usadas em foods.py, openfoodfacts.py e scores.py.
CAMPOS_NUTRIENTES = [
    "kcal", "proteina_g", "hidratos_g", "gordura_g", "gordura_saturada_g",
    "fibra_g", "acucar_g", "sodio_mg", "potassio_mg", "calcio_mg", "ferro_mg",
    "magnesio_mg", "zinco_mg", "vit_a_ug", "vit_c_mg", "vit_d_ug", "vit_e_mg",
    "vit_k_ug", "vit_b1_mg", "vit_b2_mg", "vit_b3_mg", "vit_b6_mg", "folato_ug",
    "vit_b12_ug", "omega3_g", "agua_ml", "cafeina_mg",
]


def escalar(por_100g: dict, gramas: float) -> dict:
    """Converte valores por 100 g para a quantidade indicada (em gramas/ml)."""
    fator = gramas / 100.0
    return {k: round(por_100g.get(k, 0) * fator, 3) for k in CAMPOS_NUTRIENTES}


# Nutrientes "quanto mais perto do alvo, melhor" — DDR para adultos (homem, mulher)
DDR = {
    "fibra_g":      {"nome": "Fibra",        "unidade": "g",  "homem": 38,   "mulher": 25},
    "potassio_mg":  {"nome": "Potássio",     "unidade": "mg", "homem": 3400, "mulher": 2600},
    "calcio_mg":    {"nome": "Cálcio",       "unidade": "mg", "homem": 1000, "mulher": 1000},
    "ferro_mg":     {"nome": "Ferro",        "unidade": "mg", "homem": 8,    "mulher": 18},
    "magnesio_mg":  {"nome": "Magnésio",     "unidade": "mg", "homem": 420,  "mulher": 320},
    "zinco_mg":     {"nome": "Zinco",        "unidade": "mg", "homem": 11,   "mulher": 8},
    "vit_a_ug":     {"nome": "Vitamina A",   "unidade": "µg", "homem": 900,  "mulher": 700},
    "vit_c_mg":     {"nome": "Vitamina C",   "unidade": "mg", "homem": 90,   "mulher": 75},
    "vit_d_ug":     {"nome": "Vitamina D",   "unidade": "µg", "homem": 15,   "mulher": 15},
    "vit_e_mg":     {"nome": "Vitamina E",   "unidade": "mg", "homem": 15,   "mulher": 15},
    "vit_k_ug":     {"nome": "Vitamina K",   "unidade": "µg", "homem": 120,  "mulher": 90},
    "vit_b1_mg":    {"nome": "Vitamina B1 (tiamina)",    "unidade": "mg", "homem": 1.2, "mulher": 1.1},
    "vit_b2_mg":    {"nome": "Vitamina B2 (riboflavina)","unidade": "mg", "homem": 1.3, "mulher": 1.1},
    "vit_b3_mg":    {"nome": "Vitamina B3 (niacina)",    "unidade": "mg", "homem": 16,  "mulher": 14},
    "vit_b6_mg":    {"nome": "Vitamina B6",  "unidade": "mg", "homem": 1.3,  "mulher": 1.3},
    "folato_ug":    {"nome": "Folato (B9)",  "unidade": "µg", "homem": 400,  "mulher": 400},
    "vit_b12_ug":   {"nome": "Vitamina B12", "unidade": "µg", "homem": 2.4,  "mulher": 2.4},
    "omega3_g":     {"nome": "Ómega-3",      "unidade": "g",  "homem": 1.6,  "mulher": 1.1},
}

# Nutrientes a moderar — passar o limite penaliza as pontuações
LIMITES = {
    "sodio_mg":            {"nome": "Sódio",            "unidade": "mg", "limite": 2300},
    "acucar_g":            {"nome": "Açúcar",           "unidade": "g",  "limite": 50},
    "gordura_saturada_g":  {"nome": "Gordura saturada", "unidade": "g",  "limite": 22},
    "cafeina_mg":          {"nome": "Cafeína",          "unidade": "mg", "limite": 400},
}

# O que podes sentir se um nutriente ficar consistentemente abaixo do recomendado
CARENCIAS = {
    "proteina_g": {
        "curto_prazo": "Fome constante, recuperação lenta após exercício, falta de força.",
        "longo_prazo": "Perda de massa muscular, cabelo e unhas frágeis, imunidade mais fraca.",
        "fontes": "Carne, peixe, ovos, leguminosas, lacticínios, tofu.",
    },
    "fibra_g": {
        "curto_prazo": "Obstipação, digestão pesada, fome pouco depois de comer.",
        "longo_prazo": "Colesterol mais alto, pior saúde intestinal, maior risco de diabetes tipo 2.",
        "fontes": "Aveia, leguminosas, fruta com casca, vegetais, pão integral.",
    },
    "agua_ml": {
        "curto_prazo": "Dores de cabeça, falta de energia, pele baça, má concentração.",
        "longo_prazo": "Pedras nos rins, má digestão, pele envelhecida.",
        "fontes": "Água, chá sem açúcar, sopa, fruta rica em água (melancia, laranja).",
    },
    "ferro_mg": {
        "curto_prazo": "Cansaço, palidez, falta de concentração, mãos e pés frios.",
        "longo_prazo": "Anemia, queda de cabelo, imunidade fraca, falta de ar em esforço.",
        "fontes": "Carne vermelha, marisco, leguminosas, espinafres (com vit. C para absorver melhor).",
    },
    "magnesio_mg": {
        "curto_prazo": "Cãibras, tensão muscular, pior qualidade de sono, irritabilidade.",
        "longo_prazo": "Enxaquecas frequentes, palpitações, ossos mais fracos.",
        "fontes": "Frutos secos, sementes, cacau/chocolate preto, leguminosas, aveia.",
    },
    "potassio_mg": {
        "curto_prazo": "Fraqueza muscular, cãibras, obstipação, fadiga.",
        "longo_prazo": "Tensão arterial alta, maior risco de pedras nos rins.",
        "fontes": "Banana, batata, feijão, abacate, espinafres, laranja.",
    },
    "calcio_mg": {
        "curto_prazo": "Formigueiro, cãibras musculares, unhas frágeis.",
        "longo_prazo": "Osteoporose, dentes fracos, maior risco de fraturas.",
        "fontes": "Lacticínios, couve, sardinha enlatada (com espinha), amêndoas.",
    },
    "zinco_mg": {
        "curto_prazo": "Paladar e olfato menos apurados, feridas que demoram a sarar.",
        "longo_prazo": "Queda de cabelo, pele seca/acne, imunidade fraca.",
        "fontes": "Carne, ostras e marisco, sementes de abóbora, grão-de-bico.",
    },
    "vit_a_ug": {
        "curto_prazo": "Pior visão noturna, olhos secos.",
        "longo_prazo": "Pele seca, infeções respiratórias frequentes.",
        "fontes": "Cenoura, batata-doce, fígado, ovos, espinafres.",
    },
    "vit_c_mg": {
        "curto_prazo": "Gengivas sensíveis, cicatrização lenta, cansaço.",
        "longo_prazo": "Imunidade fraca, pele baça (menos colagénio), nódoas negras fáceis.",
        "fontes": "Laranja, kiwi, pimentos, brócolos, morangos.",
    },
    "vit_d_ug": {
        "curto_prazo": "Cansaço, humor em baixo, dores musculares.",
        "longo_prazo": "Ossos fracos, imunidade reduzida, humor deprimido no inverno.",
        "fontes": "Sol (15-20 min/dia), peixes gordos (salmão, sardinha), ovos.",
    },
    "vit_e_mg": {
        "curto_prazo": "Raramente dá sinais imediatos.",
        "longo_prazo": "Fraqueza muscular, pior proteção das células (antioxidante).",
        "fontes": "Azeite, amêndoas, sementes de girassol, abacate.",
    },
    "vit_k_ug": {
        "curto_prazo": "Nódoas negras com facilidade, gengivas que sangram.",
        "longo_prazo": "Ossos mais fracos, pior coagulação do sangue.",
        "fontes": "Couve, espinafres, brócolos, couve-de-bruxelas.",
    },
    "vit_b1_mg": {
        "curto_prazo": "Cansaço, irritabilidade, falta de apetite.",
        "longo_prazo": "Problemas de memória e do sistema nervoso.",
        "fontes": "Cereais integrais, carne de porco, leguminosas, sementes.",
    },
    "vit_b2_mg": {
        "curto_prazo": "Lábios gretados, olhos sensíveis à luz.",
        "longo_prazo": "Anemia, problemas de pele.",
        "fontes": "Lacticínios, ovos, amêndoas, cogumelos.",
    },
    "vit_b3_mg": {
        "curto_prazo": "Fadiga, dores de cabeça, indigestão.",
        "longo_prazo": "Problemas de pele, digestão e memória.",
        "fontes": "Frango, atum, amendoins, cogumelos.",
    },
    "vit_b6_mg": {
        "curto_prazo": "Humor em baixo, irritabilidade, falta de foco.",
        "longo_prazo": "Anemia, formigueiro nas mãos e pés.",
        "fontes": "Grão-de-bico, banana, salmão, batata, frango.",
    },
    "folato_ug": {
        "curto_prazo": "Cansaço, falta de ar, irritabilidade.",
        "longo_prazo": "Anemia, níveis altos de homocisteína (coração).",
        "fontes": "Vegetais de folha verde, leguminosas, laranja, abacate.",
    },
    "vit_b12_ug": {
        "curto_prazo": "Cansaço extremo, formigueiro, lapsos de memória.",
        "longo_prazo": "Anemia, danos no sistema nervoso (pode ser irreversível).",
        "fontes": "Carne, peixe, ovos, lacticínios (vegans: suplemento).",
    },
    "omega3_g": {
        "curto_prazo": "Pele seca, foco reduzido, humor mais instável.",
        "longo_prazo": "Pior saúde do coração e do cérebro, mais inflamação.",
        "fontes": "Salmão, sardinha, cavala, nozes, sementes de linhaça/chia.",
    },
}


# Tradução EN do texto de carências (mesmas chaves de CARENCIAS)
_CARENCIAS_EN = {
    "proteina_g": {
        "curto_prazo": "Constant hunger, slow recovery after exercise, lack of strength.",
        "longo_prazo": "Muscle loss, brittle hair and nails, weaker immunity.",
        "fontes": "Meat, fish, eggs, legumes, dairy, tofu.",
    },
    "fibra_g": {
        "curto_prazo": "Constipation, heavy digestion, hunger soon after eating.",
        "longo_prazo": "Higher cholesterol, worse gut health, higher type 2 diabetes risk.",
        "fontes": "Oats, legumes, fruit with skin, vegetables, wholegrain bread.",
    },
    "agua_ml": {
        "curto_prazo": "Headaches, low energy, dull skin, poor concentration.",
        "longo_prazo": "Kidney stones, poor digestion, aged skin.",
        "fontes": "Water, unsweetened tea, soup, water-rich fruit (watermelon, orange).",
    },
    "ferro_mg": {
        "curto_prazo": "Tiredness, paleness, poor concentration, cold hands and feet.",
        "longo_prazo": "Anaemia, hair loss, weak immunity, breathlessness on effort.",
        "fontes": "Red meat, shellfish, legumes, spinach (with vit. C for better absorption).",
    },
    "magnesio_mg": {
        "curto_prazo": "Cramps, muscle tension, worse sleep quality, irritability.",
        "longo_prazo": "Frequent migraines, palpitations, weaker bones.",
        "fontes": "Nuts, seeds, cocoa/dark chocolate, legumes, oats.",
    },
    "potassio_mg": {
        "curto_prazo": "Muscle weakness, cramps, constipation, fatigue.",
        "longo_prazo": "High blood pressure, higher kidney stone risk.",
        "fontes": "Banana, potato, beans, avocado, spinach, orange.",
    },
    "calcio_mg": {
        "curto_prazo": "Tingling, muscle cramps, brittle nails.",
        "longo_prazo": "Osteoporosis, weak teeth, higher fracture risk.",
        "fontes": "Dairy, kale, canned sardines (with bones), almonds.",
    },
    "zinco_mg": {
        "curto_prazo": "Dulled taste and smell, wounds that heal slowly.",
        "longo_prazo": "Hair loss, dry skin/acne, weak immunity.",
        "fontes": "Meat, oysters and shellfish, pumpkin seeds, chickpeas.",
    },
    "vit_a_ug": {
        "curto_prazo": "Worse night vision, dry eyes.",
        "longo_prazo": "Dry skin, frequent respiratory infections.",
        "fontes": "Carrot, sweet potato, liver, eggs, spinach.",
    },
    "vit_c_mg": {
        "curto_prazo": "Sensitive gums, slow healing, tiredness.",
        "longo_prazo": "Weak immunity, dull skin (less collagen), easy bruising.",
        "fontes": "Orange, kiwi, peppers, broccoli, strawberries.",
    },
    "vit_d_ug": {
        "curto_prazo": "Tiredness, low mood, muscle aches.",
        "longo_prazo": "Weak bones, reduced immunity, low mood in winter.",
        "fontes": "Sun (15-20 min/day), oily fish (salmon, sardines), eggs.",
    },
    "vit_e_mg": {
        "curto_prazo": "Rarely gives immediate signs.",
        "longo_prazo": "Muscle weakness, worse cell protection (antioxidant).",
        "fontes": "Olive oil, almonds, sunflower seeds, avocado.",
    },
    "vit_k_ug": {
        "curto_prazo": "Easy bruising, bleeding gums.",
        "longo_prazo": "Weaker bones, worse blood clotting.",
        "fontes": "Kale, spinach, broccoli, Brussels sprouts.",
    },
    "vit_b1_mg": {
        "curto_prazo": "Tiredness, irritability, lack of appetite.",
        "longo_prazo": "Memory and nervous system problems.",
        "fontes": "Wholegrains, pork, legumes, seeds.",
    },
    "vit_b2_mg": {
        "curto_prazo": "Cracked lips, eyes sensitive to light.",
        "longo_prazo": "Anaemia, skin problems.",
        "fontes": "Dairy, eggs, almonds, mushrooms.",
    },
    "vit_b3_mg": {
        "curto_prazo": "Fatigue, headaches, indigestion.",
        "longo_prazo": "Skin, digestion and memory problems.",
        "fontes": "Chicken, tuna, peanuts, mushrooms.",
    },
    "vit_b6_mg": {
        "curto_prazo": "Low mood, irritability, lack of focus.",
        "longo_prazo": "Anaemia, tingling in hands and feet.",
        "fontes": "Chickpeas, banana, salmon, potato, chicken.",
    },
    "folato_ug": {
        "curto_prazo": "Tiredness, breathlessness, irritability.",
        "longo_prazo": "Anaemia, high homocysteine levels (heart).",
        "fontes": "Leafy green vegetables, legumes, orange, avocado.",
    },
    "vit_b12_ug": {
        "curto_prazo": "Extreme tiredness, tingling, memory lapses.",
        "longo_prazo": "Anaemia, nervous system damage (can be irreversible).",
        "fontes": "Meat, fish, eggs, dairy (vegans: supplement).",
    },
    "omega3_g": {
        "curto_prazo": "Dry skin, reduced focus, more unstable mood.",
        "longo_prazo": "Worse heart and brain health, more inflammation.",
        "fontes": "Salmon, sardines, mackerel, walnuts, flax/chia seeds.",
    },
}


def carencia(chave: str) -> dict | None:
    """Texto de carência (curto_prazo/longo_prazo/fontes) no idioma ativo."""
    from core import i18n
    if i18n.idioma() == "en" and chave in _CARENCIAS_EN:
        return _CARENCIAS_EN[chave]
    return CARENCIAS.get(chave)


def ddr_para(chave: str, sexo: str) -> float:
    """Dose diária recomendada de um nutriente para o sexo do utilizador."""
    info = DDR[chave]
    return info["mulher"] if sexo == "Mulher" else info["homem"]


_NOMES_EN = {
    "kcal": "Calories", "proteina_g": "Protein", "hidratos_g": "Carbs", "gordura_g": "Fat",
    "gordura_saturada_g": "Saturated fat", "fibra_g": "Fibre", "acucar_g": "Sugar",
    "sodio_mg": "Sodium", "potassio_mg": "Potassium", "calcio_mg": "Calcium", "ferro_mg": "Iron",
    "magnesio_mg": "Magnesium", "zinco_mg": "Zinc", "vit_a_ug": "Vitamin A", "vit_c_mg": "Vitamin C",
    "vit_d_ug": "Vitamin D", "vit_e_mg": "Vitamin E", "vit_k_ug": "Vitamin K",
    "vit_b1_mg": "Vitamin B1 (thiamine)", "vit_b2_mg": "Vitamin B2 (riboflavin)",
    "vit_b3_mg": "Vitamin B3 (niacin)", "vit_b6_mg": "Vitamin B6", "folato_ug": "Folate (B9)",
    "vit_b12_ug": "Vitamin B12", "omega3_g": "Omega-3", "agua_ml": "Water", "cafeina_mg": "Caffeine",
    "creatina_g": "Creatine",
}


def nome_de(chave: str) -> str:
    from core import i18n
    if i18n.idioma() == "en" and chave in _NOMES_EN:
        return _NOMES_EN[chave]
    if chave in DDR:
        return DDR[chave]["nome"]
    if chave in LIMITES:
        return LIMITES[chave]["nome"]
    return {"kcal": "Calorias", "proteina_g": "Proteína", "hidratos_g": "Hidratos de carbono",
            "gordura_g": "Gordura", "agua_ml": "Água", "creatina_g": "Creatina"}.get(chave, chave)


def unidade_de(chave: str) -> str:
    if chave in DDR:
        return DDR[chave]["unidade"]
    if chave in LIMITES:
        return LIMITES[chave]["unidade"]
    return {"kcal": "kcal", "proteina_g": "g", "hidratos_g": "g",
            "gordura_g": "g", "agua_ml": "ml", "creatina_g": "g"}.get(chave, "")


def normalizar(texto: str) -> str:
    """Remove acentos e põe em minúsculas — para ordenação alfabética correta."""
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def ordenar(chaves) -> list[str]:
    """Ordena chaves de nutrientes alfabeticamente pelo nome apresentado."""
    return sorted(chaves, key=lambda c: normalizar(nome_de(c)))


def alvo_nutriente(chave: str, sexo: str, alvos: dict | None) -> float | None:
    """Alvo diário de um nutriente: do perfil (kcal/macros/água) ou da DDR."""
    if alvos and chave in alvos:
        return alvos[chave]
    if chave in DDR:
        return ddr_para(chave, sexo)
    return None
