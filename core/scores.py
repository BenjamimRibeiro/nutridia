"""Pontuações diárias de bem-estar (0-100%) calculadas a partir do que comeste."""
from core import alcool, i18n, nutrients

# Quanto o álcool EM EXCESSO corta cada pontuação (fração máxima de corte, atingida
# quando o álcool do dia duplica o limite). Sono é o mais afetado. Só corta acima do
# limite — beber com moderação não mexe nas pontuações.
_ALCOOL_AFETA = {
    "Descanso & Sono": 0.40,
    "Humor": 0.30,
    "Cérebro & Foco": 0.30,
    "Vitalidade & Libido": 0.30,
    "Energia": 0.25,
    "Músculo & Recuperação": 0.25,
    "Imunidade": 0.20,
    "Coração": 0.20,
    "Pele & Cabelo": 0.20,
    "Digestão": 0.20,
}

# Cada pontuação combina nutrientes benéficos (peso positivo) e
# penalizadores (excesso acima do limite baixa a nota).
PONTUACOES = {
    "Cérebro & Foco": {
        "emoji": "🧠",
        "descricao": "Concentração, memória e clareza mental",
        "dica": "salmão e sardinha, nozes, ovos, espinafres, leguminosas",
        "beneficos": {"omega3_g": 3, "vit_b12_ug": 2, "folato_ug": 2, "ferro_mg": 2,
                      "zinco_mg": 1, "agua_ml": 2, "vit_b6_mg": 1},
        "penalizadores": {"acucar_g": 1},
    },
    "Energia": {
        "emoji": "⚡",
        "descricao": "Disposição e vitalidade ao longo do dia",
        "dica": "aveia, banana, carne magra, leguminosas, frutos secos e água",
        "beneficos": {"kcal": 3, "ferro_mg": 2, "vit_b1_mg": 1, "vit_b2_mg": 1,
                      "vit_b3_mg": 1, "magnesio_mg": 2, "agua_ml": 2},
        "penalizadores": {"acucar_g": 1},
    },
    "Descanso & Sono": {
        "emoji": "😴",
        "descricao": "Qualidade do sono e relaxamento",
        "dica": "frutos secos, sementes, lacticínios, banana (e menos café à tarde)",
        "beneficos": {"magnesio_mg": 3, "calcio_mg": 2, "vit_b6_mg": 2, "potassio_mg": 1},
        "penalizadores": {"cafeina_mg": 3, "acucar_g": 1},
    },
    "Imunidade": {
        "emoji": "🛡️",
        "descricao": "Defesas contra constipações e infeções",
        "dica": "laranja e kiwi, pimentos, ovos, marisco, iogurte",
        "beneficos": {"vit_c_mg": 3, "vit_d_ug": 3, "zinco_mg": 2, "vit_a_ug": 2, "proteina_g": 2},
        "penalizadores": {"acucar_g": 1},
    },
    "Músculo & Recuperação": {
        "emoji": "💪",
        "descricao": "Construção muscular e recuperação do treino",
        "dica": "frango, ovos, atum, iogurte, leguminosas, batata",
        "beneficos": {"proteina_g": 4, "kcal": 2, "potassio_mg": 1, "magnesio_mg": 1, "calcio_mg": 1},
        "penalizadores": {},
    },
    "Coração": {
        "emoji": "❤️",
        "descricao": "Saúde cardiovascular e tensão arterial",
        "dica": "aveia, leguminosas, azeite, peixes gordos, banana (e menos sal)",
        "beneficos": {"potassio_mg": 3, "fibra_g": 3, "omega3_g": 2, "magnesio_mg": 1},
        "penalizadores": {"sodio_mg": 3, "gordura_saturada_g": 2},
    },
    "Pele & Cabelo": {
        "emoji": "✨",
        "descricao": "Aparência e saúde da pele, cabelo e unhas",
        "dica": "cenoura, abacate, amêndoas, citrinos e muita água",
        "beneficos": {"vit_a_ug": 2, "vit_c_mg": 2, "vit_e_mg": 2, "zinco_mg": 2,
                      "agua_ml": 3, "proteina_g": 1},
        "penalizadores": {"acucar_g": 2},
    },
    "Digestão": {
        "emoji": "🌿",
        "descricao": "Trânsito intestinal e conforto digestivo",
        "dica": "aveia, leguminosas, fruta com casca, vegetais e muita água",
        "beneficos": {"fibra_g": 4, "agua_ml": 3, "magnesio_mg": 1},
        "penalizadores": {"gordura_saturada_g": 1},
    },
    "Humor": {
        "emoji": "🙂",
        "descricao": "Estabilidade emocional e boa disposição",
        "dica": "peixes gordos, banana, espinafres, chocolate preto, leguminosas",
        "beneficos": {"omega3_g": 2, "vit_d_ug": 2, "vit_b6_mg": 2, "folato_ug": 2,
                      "vit_b12_ug": 1, "magnesio_mg": 2},
        "penalizadores": {"acucar_g": 2, "cafeina_mg": 1},
    },
    "Vitalidade & Libido": {
        "emoji": "💗",
        "descricao": "Energia sexual, libido e equilíbrio hormonal",
        "dica": "marisco e ostras, chocolate preto, frutos secos, abacate, ovos",
        "beneficos": {"zinco_mg": 3, "vit_d_ug": 2, "omega3_g": 2, "magnesio_mg": 2,
                      "vit_e_mg": 1, "folato_ug": 1},
        "penalizadores": {"acucar_g": 2, "gordura_saturada_g": 1},
    },
}


def _cobertura(chave: str, totais: dict, alvos: dict, sexo: str) -> float:
    """0..1 — fração do alvo atingida. Para calorias, estar perto do alvo é o ideal."""
    consumido = totais.get(chave, 0)
    if chave == "kcal":
        alvo = alvos.get("kcal", 2000)
        return max(0.0, 1.0 - abs(consumido - alvo) / alvo) if alvo else 0.0
    alvo = alvos.get(chave) or (nutrients.ddr_para(chave, sexo) if chave in nutrients.DDR else None)
    if not alvo:
        return 0.0
    return min(consumido / alvo, 1.0)


def _penalizacao(chave: str, totais: dict) -> float:
    """0..1 — 1 se dentro do limite; desce à medida que o excesso cresce."""
    consumido = totais.get(chave, 0)
    limite = nutrients.LIMITES[chave]["limite"]
    if consumido <= limite:
        return 1.0
    return max(0.0, 1.0 - (consumido - limite) / limite)


def calcular(totais: dict, alvos: dict, sexo: str) -> dict[str, int]:
    """Devolve {nome_da_pontuacao: 0-100} para o dia."""
    resultado = {}
    for nome, cfg in PONTUACOES.items():
        soma, pesos = 0.0, 0.0
        for chave, peso in cfg["beneficos"].items():
            soma += _cobertura(chave, totais, alvos, sexo) * peso
            pesos += peso
        for chave, peso in cfg["penalizadores"].items():
            soma += _penalizacao(chave, totais) * peso
            pesos += peso
        resultado[nome] = round(100 * soma / pesos) if pesos else 0

    # penalização por álcool em excesso (só acima do limite diário)
    exc = alcool.excesso(totais.get("alcool_g", 0))
    if exc:
        for nome, sensibilidade in _ALCOOL_AFETA.items():
            if nome in resultado:
                resultado[nome] = round(resultado[nome] * (1 - sensibilidade * exc))
    return resultado


def cor_da_pontuacao(valor: int) -> str:
    if valor >= 80:
        return "🟢"
    if valor >= 60:
        return "🟡"
    if valor >= 40:
        return "🟠"
    return "🔴"


# ---- Tradução para inglês ----
_NOMES_EN = {
    "Cérebro & Foco": "Brain & Focus", "Energia": "Energy", "Descanso & Sono": "Rest & Sleep",
    "Imunidade": "Immunity", "Músculo & Recuperação": "Muscle & Recovery", "Coração": "Heart",
    "Pele & Cabelo": "Skin & Hair", "Digestão": "Digestion", "Humor": "Mood",
    "Vitalidade & Libido": "Vitality & Libido",
}
_DESC_EN = {
    "Cérebro & Foco": "Concentration, memory and mental clarity",
    "Energia": "Drive and vitality throughout the day",
    "Descanso & Sono": "Sleep quality and relaxation",
    "Imunidade": "Defences against colds and infections",
    "Músculo & Recuperação": "Muscle building and workout recovery",
    "Coração": "Cardiovascular health and blood pressure",
    "Pele & Cabelo": "Skin, hair and nail health",
    "Digestão": "Gut transit and digestive comfort",
    "Humor": "Emotional stability and good mood",
    "Vitalidade & Libido": "Sexual energy, libido and hormonal balance",
}
_DICA_EN = {
    "Cérebro & Foco": "salmon and sardines, walnuts, eggs, spinach, legumes",
    "Energia": "oats, banana, lean meat, legumes, nuts and water",
    "Descanso & Sono": "nuts, seeds, dairy, banana (and less coffee in the afternoon)",
    "Imunidade": "orange and kiwi, peppers, eggs, shellfish, yogurt",
    "Músculo & Recuperação": "chicken, eggs, tuna, yogurt, legumes, potato",
    "Coração": "oats, legumes, olive oil, oily fish, banana (and less salt)",
    "Pele & Cabelo": "carrot, avocado, almonds, citrus and plenty of water",
    "Digestão": "oats, legumes, fruit with skin, vegetables and plenty of water",
    "Humor": "oily fish, banana, spinach, dark chocolate, legumes",
    "Vitalidade & Libido": "shellfish and oysters, dark chocolate, nuts, avocado, eggs",
}


def nome(n: str) -> str:
    return _NOMES_EN.get(n, n) if i18n.idioma() == "en" else n


def descricao(n: str) -> str:
    return _DESC_EN[n] if i18n.idioma() == "en" else PONTUACOES[n]["descricao"]


def dica(n: str) -> str:
    return _DICA_EN[n] if i18n.idioma() == "en" else PONTUACOES[n]["dica"]
