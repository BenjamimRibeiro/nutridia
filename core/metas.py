"""Metas, sequências (streaks) e medalhas — calculadas a partir dos registos."""
from datetime import date, timedelta

from core import db, nutrients, scores


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


def resumo_semanal(uid, perfil: dict, alvos: dict) -> dict:
    """Boletim dos últimos 7 dias: médias, dias no alvo/saudáveis, pontuações e
    o nutriente mais forte / a melhorar."""
    sexo = perfil["sexo"]
    medias, dias = _medias_n_dias(uid, 7)
    no_alvo = saudaveis = n_pont = 0
    pont_acc: dict[str, float] = {}
    for i in range(7):
        d = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        if not db.tem_refeicoes(uid, d):
            continue
        totais = db.totais_do_dia(uid, d)
        alvo_kcal = alvos["kcal"] + db.exercicio_kcal_do_dia(uid, d)
        if dia_dentro_alvo(totais, alvo_kcal):
            no_alvo += 1
        if dia_saudavel(totais, alvo_kcal, alvos):
            saudaveis += 1
        n_pont += 1
        for nome, valor in scores.calcular(totais, {**alvos, "kcal": alvo_kcal}, sexo).items():
            pont_acc[nome] = pont_acc.get(nome, 0) + valor

    coberturas = []
    for c in ["proteina_g", "fibra_g", *nutrients.DDR]:
        alvo = nutrients.alvo_nutriente(c, sexo, alvos)
        if alvo:
            coberturas.append((c, min(medias.get(c, 0) / alvo, 2.0)))
    return {
        "dias": dias, "no_alvo": no_alvo, "saudaveis": saudaveis,
        "kcal": medias.get("kcal", 0), "proteina_g": medias.get("proteina_g", 0),
        "fibra_g": medias.get("fibra_g", 0), "agua_ml": medias.get("agua_ml", 0),
        "pontuacoes": {k: round(v / n_pont) for k, v in pont_acc.items()} if n_pont else {},
        "melhor": max(coberturas, key=lambda x: x[1]) if coberturas else None,
        "pior": min(coberturas, key=lambda x: x[1]) if coberturas else None,
    }


def desafios_semanais(uid, perfil: dict, alvos: dict) -> list[dict]:
    """Desafios da semana atual (segunda → hoje), com progresso automático."""
    hoje = date.today()
    inicio = hoje - timedelta(days=hoje.weekday())  # segunda-feira
    dias = [(inicio + timedelta(days=i)) for i in range((hoje - inicio).days + 1)]

    agua_ok = saud = fibra_ok = acucar_ok = registados = sessoes = 0
    for d in dias:
        ds = d.strftime("%Y-%m-%d")
        sessoes += len(db.exercicios_do_dia(uid, ds))
        if not db.tem_refeicoes(uid, ds):
            continue
        registados += 1
        totais = db.totais_do_dia(uid, ds)
        if db.agua_do_dia(uid, ds) >= alvos["agua_ml"]:
            agua_ok += 1
        alvo_kcal = alvos["kcal"] + db.exercicio_kcal_do_dia(uid, ds)
        if dia_saudavel(totais, alvo_kcal, alvos):
            saud += 1
        if totais.get("fibra_g", 0) >= alvos["fibra_g"]:
            fibra_ok += 1
        if totais.get("acucar_g", 0) <= nutrients.LIMITES["acucar_g"]["limite"]:
            acucar_ok += 1

    crus = [
        ("💧", "Bem hidratado", "Água em dia em 5 dias", agua_ok, 5),
        ("🥗", "Comer a sério", "3 dias saudáveis", saud, 3),
        ("🏃", "Mexe-te", "3 treinos esta semana", sessoes, 3),
        ("🌿", "Cheio de fibra", "Fibra na meta em 4 dias", fibra_ok, 4),
        ("🍬", "Açúcar sob controlo", "Sem exagerar no açúcar em 5 dias", acucar_ok, 5),
        ("📋", "Consistente", "Registar refeições em 6 dias", registados, 6),
    ]
    return [{"emoji": e, "nome": n, "desc": d, "atual": min(a, alvo), "alvo": alvo,
             "completo": a >= alvo} for e, n, d, a, alvo in crus]


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
