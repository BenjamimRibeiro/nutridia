"""Metas, sequências (streaks) e medalhas — calculadas a partir dos registos."""
from datetime import date, timedelta

from core import db, nutrients


def dia_dentro_alvo(totais: dict, alvo_kcal: float) -> bool:
    """Um dia conta como 'dentro do alvo' se teve registos e as calorias ficaram
    entre 80% e 110% do alvo (já com o exercício somado)."""
    kcal = totais.get("kcal", 0)
    if kcal <= 0:
        return False
    return 0.80 * alvo_kcal <= kcal <= 1.10 * alvo_kcal


def sequencia_atual(uid, alvos: dict) -> int:
    """Dias seguidos dentro do alvo, a contar a partir de hoje (ou ontem, se hoje
    ainda não houver registos). O exercício do dia soma ao alvo de calorias."""
    hoje = date.today()
    inicio = 0
    if not db.tem_refeicoes(uid, hoje.strftime("%Y-%m-%d")):
        inicio = 1  # ainda não comeste hoje: a sequência mantém-se a partir de ontem
    seguidos = 0
    for i in range(inicio, 365):
        dia = (hoje - timedelta(days=i)).strftime("%Y-%m-%d")
        if db.obter_estado(uid, dia)["estado"] == "Doente":
            seguidos += 1  # dia doente não quebra a sequência (com compreensão)
            continue
        alvo_kcal = alvos["kcal"] + db.exercicio_kcal_do_dia(uid, dia)
        if dia_dentro_alvo(db.totais_do_dia(uid, dia), alvo_kcal):
            seguidos += 1
        else:
            break
    return seguidos


def dia_saudavel(totais: dict, alvo_kcal: float, alvos: dict) -> bool:
    """Um dia 'a sério': calorias na zona E proteína E fibra ok E sem rebentar os
    limites de açúcar/sódio/gordura saturada. Difícil de enganar com fast food."""
    kcal = totais.get("kcal", 0)
    if kcal <= 0 or not (0.80 * alvo_kcal <= kcal <= 1.10 * alvo_kcal):
        return False
    if totais.get("proteina_g", 0) < 0.85 * alvos["proteina_g"]:
        return False
    if totais.get("fibra_g", 0) < 0.70 * alvos["fibra_g"]:
        return False
    for chave in ("sodio_mg", "acucar_g", "gordura_saturada_g"):
        if totais.get(chave, 0) > nutrients.LIMITES[chave]["limite"]:
            return False
    return True


def sequencia_saudavel(uid, alvos: dict) -> int:
    """Dias seguidos 'saudáveis' (qualidade, não só calorias). Dias doentes não quebram."""
    hoje = date.today()
    inicio = 0 if db.tem_refeicoes(uid, hoje.strftime("%Y-%m-%d")) else 1
    seguidos = 0
    for i in range(inicio, 365):
        dia = (hoje - timedelta(days=i)).strftime("%Y-%m-%d")
        if db.obter_estado(uid, dia)["estado"] == "Doente":
            seguidos += 1
            continue
        if not db.tem_refeicoes(uid, dia):
            break
        alvo_kcal = alvos["kcal"] + db.exercicio_kcal_do_dia(uid, dia)
        if dia_saudavel(db.totais_do_dia(uid, dia), alvo_kcal, alvos):
            seguidos += 1
        else:
            break
    return seguidos


def _medias_n_dias(uid, n: int) -> tuple[dict, int]:
    somas: dict[str, float] = {}
    dias = 0
    for i in range(n):
        dia = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        totais = db.totais_do_dia(uid, dia)
        if totais.get("kcal", 0) > 0:
            dias += 1
            for k, v in totais.items():
                somas[k] = somas.get(k, 0) + v
    return ({k: v / dias for k, v in somas.items()} if dias else {}), dias


def medalhas(uid, perfil: dict, alvos: dict) -> list[dict]:
    """Lista de medalhas com estado (conquistada ou não)."""
    seq = sequencia_atual(uid, alvos)
    seq_saud = sequencia_saudavel(uid, alvos)
    medias7, dias7 = _medias_n_dias(uid, 7)
    sexo = perfil["sexo"]

    # dias da última semana com a água em dia
    dias_agua = sum(
        1 for i in range(7)
        if db.agua_do_dia(uid, (date.today() - timedelta(days=i)).strftime("%Y-%m-%d"))
        >= alvos["agua_ml"])

    # nutrientes (com DDR) em dia, em média, na última semana
    micros_ok = 0
    if dias7:
        for chave in nutrients.DDR:
            alvo = nutrients.alvo_nutriente(chave, sexo, alvos)
            if alvo and medias7.get(chave, 0) >= alvo:
                micros_ok += 1

    return [
        {"emoji": "🔥", "nome": "Em chamas", "desc": "3 dias seguidos dentro do alvo",
         "conquistada": seq >= 3, "progresso": f"{min(seq, 3)}/3 dias"},
        {"emoji": "🏆", "nome": "Semana perfeita", "desc": "7 dias seguidos dentro do alvo",
         "conquistada": seq >= 7, "progresso": f"{min(seq, 7)}/7 dias"},
        {"emoji": "🥦", "nome": "Corpo cuidado", "desc": "3 dias saudáveis seguidos",
         "conquistada": seq_saud >= 3, "progresso": f"{min(seq_saud, 3)}/3 dias"},
        {"emoji": "🥇", "nome": "Semana impecável", "desc": "7 dias saudáveis seguidos",
         "conquistada": seq_saud >= 7, "progresso": f"{min(seq_saud, 7)}/7 dias"},
        {"emoji": "💪", "nome": "Semana proteica", "desc": "Média de proteína na meta (7 dias)",
         "conquistada": dias7 >= 3 and medias7.get("proteina_g", 0) >= alvos["proteina_g"],
         "progresso": f"{medias7.get('proteina_g', 0):.0f}/{alvos['proteina_g']} g" if dias7 else "sem dados"},
        {"emoji": "💧", "nome": "Hidratado", "desc": "Água em dia em 5 dos últimos 7 dias",
         "conquistada": dias_agua >= 5, "progresso": f"{dias_agua}/7 dias"},
        {"emoji": "🌈", "nome": "Arco-íris", "desc": "≥12 vitaminas/minerais na meta (média 7 dias)",
         "conquistada": micros_ok >= 12, "progresso": f"{micros_ok}/{len(nutrients.DDR)}"},
    ]
