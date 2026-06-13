"""Catálogo de atividades físicas e estimativa de calorias gastas (valores MET).

kcal ≈ MET × peso (kg) × duração (horas). O MET é a intensidade da atividade.
"""

# atividade -> MET (intensidade média)
ATIVIDADES = {
    "Caminhada (lenta)": 3.0,
    "Caminhada (rápida)": 4.3,
    "Passear o cão": 3.0,
    "Corrida (8 km/h)": 8.3,
    "Corrida (12 km/h)": 11.5,
    "Ciclismo (lazer)": 6.0,
    "Ciclismo (intenso)": 10.0,
    "Natação": 7.0,
    "Futebol": 7.0,
    "Basquetebol": 6.5,
    "Ténis": 7.0,
    "Padel": 6.0,
    "Ginásio / musculação": 5.0,
    "HIIT / crossfit": 9.0,
    "Saltar à corda": 11.0,
    "Remo": 7.0,
    "Elíptica": 5.0,
    "Subir escadas": 8.0,
    "Dança": 5.0,
    "Yoga": 2.5,
    "Pilates": 3.0,
    "Surf": 5.0,
    "Jardinagem": 3.5,
    "Limpeza da casa": 3.0,
}


def kcal(met: float, peso_kg: float, minutos: int) -> int:
    return round(met * peso_kg * minutos / 60)
