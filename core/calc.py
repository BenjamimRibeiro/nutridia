"""Cálculos energéticos: TMB (Mifflin-St Jeor), TDEE e alvos diários."""
from datetime import date, datetime, timedelta

FATORES_ATIVIDADE = {
    "Sedentário (pouco ou nenhum exercício)": 1.2,
    "Leve (exercício 1-3x/semana)": 1.375,
    "Moderado (exercício 3-5x/semana)": 1.55,
    "Intenso (exercício 6-7x/semana)": 1.725,
    "Atleta (2 treinos/dia ou trabalho físico)": 1.9,
}

OBJETIVOS = ["Manter peso", "Emagrecer", "Engordar / ganhar massa"]

KCAL_POR_KG = 7700  # défice/excedente necessário para variar 1 kg de gordura


def tmb(sexo: str, peso_kg: float, altura_cm: float, idade: int) -> float:
    """Taxa metabólica basal — equação de Mifflin-St Jeor."""
    base = 10 * peso_kg + 6.25 * altura_cm - 5 * idade
    return base + 5 if sexo == "Homem" else base - 161


def tdee(perfil: dict) -> float:
    """Gasto energético diário total (manutenção)."""
    return tmb(perfil["sexo"], perfil["peso_kg"], perfil["altura_cm"], perfil["idade"]) \
        * FATORES_ATIVIDADE.get(perfil["atividade"], 1.2)


def alvo_calorias(perfil: dict) -> float:
    """Calorias diárias ajustadas ao objetivo e ritmo (kg/semana)."""
    manutencao = tdee(perfil)
    delta_diario = perfil.get("ritmo_kg_semana", 0.5) * KCAL_POR_KG / 7
    if perfil["objetivo"] == "Emagrecer":
        # nunca descer abaixo da TMB — não é saudável nem sustentável
        return max(manutencao - delta_diario, tmb(perfil["sexo"], perfil["peso_kg"],
                                                  perfil["altura_cm"], perfil["idade"]))
    if perfil["objetivo"] == "Engordar / ganhar massa":
        return manutencao + delta_diario
    return manutencao


def projecao_peso(perfil: dict, historico: list[dict]) -> dict | None:
    """Estima quando se atinge o peso-alvo, com base no ritmo planeado e na tendência real.

    Devolve None se não houver peso-alvo. Caso contrário um dict com semanas, data,
    ritmo usado e um aviso se o objetivo não bate certo com o alvo."""
    alvo = perfil.get("peso_alvo_kg")
    if not alvo:
        return None
    atual = historico[-1]["kg"] if historico else perfil["peso_kg"]
    delta = alvo - atual  # negativo = perder, positivo = ganhar
    if abs(delta) < 0.3:
        return {"atingido": True, "atual": atual, "alvo": alvo}

    ritmo_planeado = perfil.get("ritmo_kg_semana", 0.5)
    sentido = -1 if delta < 0 else 1  # queremos descer ou subir

    # tendência real, se houver dois pesos com pelo menos 7 dias de intervalo
    ritmo_real = None
    if len(historico) >= 2:
        d0 = datetime.fromisoformat(historico[0]["data"])
        d1 = datetime.fromisoformat(historico[-1]["data"])
        semanas = (d1 - d0).days / 7
        if semanas >= 1:
            ritmo_real = (historico[-1]["kg"] - historico[0]["kg"]) / semanas

    # usa a tendência real se for no sentido certo; senão o ritmo planeado
    if ritmo_real is not None and (ritmo_real < 0) == (sentido < 0) and abs(ritmo_real) > 0.05:
        ritmo = abs(ritmo_real)
        fonte = "tendência real"
    else:
        ritmo = ritmo_planeado
        fonte = "ritmo planeado"

    semanas_faltam = abs(delta) / max(ritmo, 0.05)
    data_estimada = date.today() + timedelta(weeks=semanas_faltam)

    objetivo = perfil["objetivo"]
    incoerente = ((delta < 0 and objetivo == "Engordar / ganhar massa")
                  or (delta > 0 and objetivo == "Emagrecer"))

    return {
        "atingido": False, "atual": atual, "alvo": alvo, "delta": delta,
        "semanas": semanas_faltam, "data": data_estimada, "ritmo": ritmo,
        "fonte": fonte, "incoerente": incoerente,
    }


def alvos_diarios(perfil: dict) -> dict:
    """Alvos de calorias, macros e água com base no perfil."""
    kcal = alvo_calorias(perfil)
    peso = perfil["peso_kg"]
    # proteína mais alta a emagrecer (preservar músculo) e a ganhar massa
    g_prot_kg = {"Emagrecer": 1.8, "Engordar / ganhar massa": 1.7}.get(perfil["objetivo"], 1.4)
    proteina = g_prot_kg * peso
    gordura = kcal * 0.30 / 9          # ~30% das calorias
    hidratos = (kcal - proteina * 4 - gordura * 9) / 4
    return {
        "kcal": round(kcal),
        "proteina_g": round(proteina),
        "hidratos_g": round(max(hidratos, 0)),
        "gordura_g": round(gordura),
        "fibra_g": 38 if perfil["sexo"] == "Homem" else 25,
        "agua_ml": round(peso * 35),   # ~35 ml por kg
    }
