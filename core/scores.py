"""Pontuações diárias de bem-estar (0-100%) calculadas a partir do que comeste."""
from core import nutrients

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
    return resultado


def cor_da_pontuacao(valor: int) -> str:
    if valor >= 80:
        return "🟢"
    if valor >= 60:
        return "🟡"
    if valor >= 40:
        return "🟠"
    return "🔴"
