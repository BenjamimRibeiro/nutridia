"""Catálogo de suplementos comuns e o que cada dose contribui (por dia)."""

# nome -> nutrientes por dose diária (só os campos relevantes; o resto fica 0)
CATALOGO = {
    "Ómega-3 (1 cápsula)": {"omega3_g": 1.0},
    "Proteína em pó (1 dose ~30 g)": {"kcal": 120, "proteina_g": 24},
    "Multivitamínico": {
        "vit_a_ug": 800, "vit_c_mg": 80, "vit_d_ug": 5, "vit_e_mg": 12, "vit_k_ug": 30,
        "vit_b1_mg": 1.1, "vit_b2_mg": 1.4, "vit_b3_mg": 16, "vit_b6_mg": 1.4,
        "folato_ug": 200, "vit_b12_ug": 2.5, "ferro_mg": 5, "zinco_mg": 5,
        "magnesio_mg": 50, "calcio_mg": 120,
    },
    "Complexo B": {"vit_b1_mg": 1.4, "vit_b2_mg": 1.6, "vit_b3_mg": 18, "vit_b6_mg": 2,
                   "folato_ug": 200, "vit_b12_ug": 3},
    "Vitamina C (1 comprimido)": {"vit_c_mg": 1000},
    "Vitamina D (1000 UI)": {"vit_d_ug": 25},
    "Magnésio": {"magnesio_mg": 300},
    "Zinco": {"zinco_mg": 15},
    "Ferro": {"ferro_mg": 14},
    "Cálcio": {"calcio_mg": 500},
    "Vitamina B12": {"vit_b12_ug": 25},
    "Creatina (5 g)": {},
}


def nutrientes_de(nomes: list[str]) -> dict:
    """Soma os nutrientes de uma lista de suplementos do catálogo."""
    total: dict[str, float] = {}
    for nome in nomes:
        for chave, valor in CATALOGO.get(nome, {}).items():
            total[chave] = total.get(chave, 0) + valor
    return total
