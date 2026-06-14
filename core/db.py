"""Base de dados multi-utilizador via SQLAlchemy.

Funciona com SQLite (local, predefinido) ou PostgreSQL (nuvem) — basta definir a
variável de ambiente NUTRIDIA_DB_URL (ex.: a connection string do Postgres).
O mesmo código serve os dois; não há SQL específico de um motor.
"""
import json
import os
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import (Column, Float, Integer, MetaData, String, Table, Text,
                        and_, create_engine, delete, func, insert, inspect, select,
                        text, update)

from core import auth, sol, suplementos as _sup

PASTA_DATA = Path(__file__).resolve().parent.parent / "data"
PASTA_FOTOS = PASTA_DATA / "fotos"
DB_PATH = PASTA_DATA / "nutridia.db"

metadata = MetaData()

utilizadores = Table(
    "utilizadores", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("nome", String(120), nullable=False),
    Column("username", String(120)),
    Column("pass_hash", String(255)),
    Column("pass_salt", String(64)),
    Column("criado_em", String(40), nullable=False),
)
perfis = Table(
    "perfis", metadata,
    Column("utilizador_id", Integer, primary_key=True),
    Column("sexo", String(10)), Column("idade", Integer), Column("peso_kg", Float),
    Column("altura_cm", Float), Column("atividade", String(80)),
    Column("objetivo", String(40)), Column("ritmo_kg_semana", Float),
    Column("peso_alvo_kg", Float),
    Column("restricoes", Text), Column("alergias", Text), Column("suplementos", Text),
    Column("sol_habitual", Text),
)
refeicoes = Table(
    "refeicoes", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("utilizador_id", Integer), Column("data", String(10), nullable=False),
    Column("hora", String(5), nullable=False), Column("nome", String(200), nullable=False),
    Column("descricao", Text), Column("foto_path", Text),
    Column("nutrientes", Text, nullable=False), Column("criado_em", String(40), nullable=False),
    Column("itens", Text), Column("momento", String(30)),
)
agua = Table(
    "agua", metadata,
    Column("utilizador_id", Integer, primary_key=True),
    Column("data", String(10), primary_key=True),
    Column("ml", Integer, nullable=False, default=0),
)
peso_registos = Table(
    "peso_registos", metadata,
    Column("utilizador_id", Integer, primary_key=True),
    Column("data", String(10), primary_key=True),
    Column("kg", Float, nullable=False),
)
alimentos_custom = Table(
    "alimentos_custom", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("utilizador_id", Integer, nullable=False), Column("nome", String(200), nullable=False),
    Column("por_100g", Text, nullable=False), Column("porcoes", Text, nullable=False),
    Column("criado_em", String(40), nullable=False),
)
favoritos = Table(
    "favoritos", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("utilizador_id", Integer, nullable=False), Column("nome", String(200), nullable=False),
    Column("itens", Text, nullable=False), Column("criado_em", String(40), nullable=False),
)
suplementos_custom = Table(
    "suplementos_custom", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("utilizador_id", Integer, nullable=False), Column("nome", String(120), nullable=False),
    Column("nutrientes", Text, nullable=False), Column("criado_em", String(40), nullable=False),
)
exercicios = Table(
    "exercicios", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("utilizador_id", Integer, nullable=False), Column("data", String(10), nullable=False),
    Column("nome", String(120), nullable=False), Column("duracao_min", Integer, nullable=False),
    Column("kcal", Integer, nullable=False), Column("criado_em", String(40), nullable=False),
)
estado_saude = Table(
    "estado_saude", metadata,
    Column("utilizador_id", Integer, primary_key=True),
    Column("data", String(10), primary_key=True),
    Column("estado", String(20), nullable=False), Column("tipo", String(40)),
)
definicoes = Table(
    "definicoes", metadata,
    Column("chave", String(80), primary_key=True), Column("valor", Text, nullable=False),
)

_ENGINE = None


def _engine():
    global _ENGINE
    if _ENGINE is None:
        url = os.environ.get("NUTRIDIA_DB_URL") or f"sqlite:///{DB_PATH}"
        if url.startswith("sqlite"):
            PASTA_DATA.mkdir(exist_ok=True)
            _ENGINE = create_engine(url, connect_args={"check_same_thread": False})
        else:
            _ENGINE = create_engine(url, pool_pre_ping=True)
        metadata.create_all(_ENGINE)
        _migrar(_ENGINE)
    return _ENGINE


def reset_engine() -> None:
    """Usado nos testes para trocar de base de dados."""
    global _ENGINE
    if _ENGINE is not None:
        _ENGINE.dispose()
    _ENGINE = None


def _migrar(engine) -> None:
    """Adiciona colunas novas a bases de dados antigas (auth e momento)."""
    insp = inspect(engine)
    cols_u = {c["name"] for c in insp.get_columns("utilizadores")}
    cols_r = {c["name"] for c in insp.get_columns("refeicoes")}
    cols_p = {c["name"] for c in insp.get_columns("perfis")}
    with engine.begin() as con:
        for coluna, tipo in [("username", "VARCHAR(120)"), ("pass_hash", "VARCHAR(255)"),
                             ("pass_salt", "VARCHAR(64)")]:
            if coluna not in cols_u:
                con.execute(text(f"ALTER TABLE utilizadores ADD COLUMN {coluna} {tipo}"))
        if "momento" not in cols_r:
            con.execute(text("ALTER TABLE refeicoes ADD COLUMN momento VARCHAR(30)"))
        for coluna in ("restricoes", "alergias", "suplementos", "sol_habitual"):
            if coluna not in cols_p:
                con.execute(text(f"ALTER TABLE perfis ADD COLUMN {coluna} TEXT"))


def inicializar() -> None:
    _engine()


# ---------- Utilizadores e autenticação ----------

def garantir_utilizador_default() -> int:
    """Garante um utilizador local (sem login). Devolve o id."""
    with _engine().begin() as con:
        linha = con.execute(select(utilizadores.c.id).order_by(utilizadores.c.id)).first()
        if linha:
            return linha[0]
        res = con.execute(insert(utilizadores).values(
            nome="Eu", criado_em=datetime.now().isoformat()))
        return res.inserted_primary_key[0]


def listar_utilizadores() -> list[dict]:
    with _engine().connect() as con:
        linhas = con.execute(select(utilizadores.c.id, utilizadores.c.nome)
                             .order_by(utilizadores.c.id)).mappings().all()
    return [dict(l) for l in linhas]


def username_existe(username: str) -> bool:
    with _engine().connect() as con:
        return con.execute(select(utilizadores.c.id).where(
            func.lower(utilizadores.c.username) == username.strip().lower())).first() is not None


def criar_conta(nome: str, username: str, password: str) -> int:
    hash_hex, salt_hex = auth.criar_hash(password)
    with _engine().begin() as con:
        res = con.execute(insert(utilizadores).values(
            nome=nome.strip(), username=username.strip(), pass_hash=hash_hex,
            pass_salt=salt_hex, criado_em=datetime.now().isoformat()))
        return res.inserted_primary_key[0]


def autenticar(username: str, password: str) -> dict | None:
    """Devolve {id, nome, username} se as credenciais baterem certo, senão None."""
    with _engine().connect() as con:
        linha = con.execute(select(utilizadores).where(
            func.lower(utilizadores.c.username) == username.strip().lower())).mappings().first()
    if linha and auth.verificar(password, linha["pass_hash"], linha["pass_salt"]):
        return {"id": linha["id"], "nome": linha["nome"], "username": linha["username"]}
    return None


def criar_utilizador(nome: str) -> int:
    with _engine().begin() as con:
        res = con.execute(insert(utilizadores).values(
            nome=nome.strip(), criado_em=datetime.now().isoformat()))
        return res.inserted_primary_key[0]


# ---------- Perfil ----------

def guardar_perfil(uid, sexo, idade, peso_kg, altura_cm, atividade, objetivo, ritmo,
                   peso_alvo=None) -> None:
    valores = dict(sexo=sexo, idade=idade, peso_kg=peso_kg, altura_cm=altura_cm,
                   atividade=atividade, objetivo=objetivo, ritmo_kg_semana=ritmo,
                   peso_alvo_kg=peso_alvo)
    with _engine().begin() as con:
        existe = con.execute(select(perfis.c.utilizador_id).where(
            perfis.c.utilizador_id == uid)).first()
        if existe:
            con.execute(update(perfis).where(perfis.c.utilizador_id == uid).values(**valores))
        else:
            con.execute(insert(perfis).values(utilizador_id=uid, **valores))


def obter_perfil(uid) -> dict | None:
    with _engine().connect() as con:
        linha = con.execute(select(perfis).where(perfis.c.utilizador_id == uid)).mappings().first()
    if not linha:
        return None
    d = dict(linha)
    for campo in ("restricoes", "alergias", "suplementos"):
        d[campo] = json.loads(d[campo]) if d.get(campo) else []
    return d


def guardar_preferencias(uid, restricoes: list, alergias: list, suplementos: list,
                         sol_habitual: str | None = None) -> None:
    with _engine().begin() as con:
        con.execute(update(perfis).where(perfis.c.utilizador_id == uid).values(
            restricoes=json.dumps(restricoes, ensure_ascii=False),
            alergias=json.dumps(alergias, ensure_ascii=False),
            suplementos=json.dumps(suplementos, ensure_ascii=False),
            sol_habitual=sol_habitual))


def criar_suplemento(uid, nome: str, nutrientes: dict) -> int:
    with _engine().begin() as con:
        res = con.execute(insert(suplementos_custom).values(
            utilizador_id=uid, nome=nome, nutrientes=json.dumps(nutrientes, ensure_ascii=False),
            criado_em=datetime.now().isoformat()))
        return res.inserted_primary_key[0]


def listar_suplementos_custom(uid) -> list[dict]:
    with _engine().connect() as con:
        linhas = con.execute(select(suplementos_custom).where(
            suplementos_custom.c.utilizador_id == uid).order_by(suplementos_custom.c.nome)).mappings().all()
    return [{"id": l["id"], "nome": l["nome"], "nutrientes": json.loads(l["nutrientes"])}
            for l in linhas]


def atualizar_suplemento(sup_id: int, nome: str, nutrientes: dict) -> None:
    with _engine().begin() as con:
        con.execute(update(suplementos_custom).where(suplementos_custom.c.id == sup_id).values(
            nome=nome, nutrientes=json.dumps(nutrientes, ensure_ascii=False)))


def apagar_suplemento(sup_id: int) -> None:
    with _engine().begin() as con:
        con.execute(delete(suplementos_custom).where(suplementos_custom.c.id == sup_id))


def suplementos_nutrientes(uid) -> dict:
    """Soma os nutrientes da rotina de suplementos (do catálogo + próprios)."""
    perfil = obter_perfil(uid)
    nomes = perfil.get("suplementos", []) if perfil else []
    custom = {c["nome"]: c["nutrientes"] for c in listar_suplementos_custom(uid)}
    total: dict[str, float] = {}
    for nome in nomes:
        fonte = _sup.CATALOGO.get(nome) or custom.get(nome)
        if fonte:
            for chave, valor in fonte.items():
                total[chave] = total.get(chave, 0) + valor
    return total


# ---------- Refeições ----------

def guardar_refeicao(uid, nome: str, nutrientes: dict, descricao: str = "",
                     foto_bytes: bytes | None = None, dia: str | None = None,
                     itens: list[dict] | None = None, momento: str | None = None,
                     hora: str | None = None) -> int:
    agora = datetime.now()
    dia = dia or agora.strftime("%Y-%m-%d")
    hora = hora or agora.strftime("%H:%M")
    foto_path = None
    if foto_bytes:
        PASTA_FOTOS.mkdir(exist_ok=True)
        foto_path = str(PASTA_FOTOS / f"{agora.strftime('%Y%m%d_%H%M%S')}.jpg")
        Path(foto_path).write_bytes(foto_bytes)
    with _engine().begin() as con:
        res = con.execute(insert(refeicoes).values(
            utilizador_id=uid, data=dia, hora=hora, nome=nome,
            descricao=descricao, foto_path=foto_path,
            nutrientes=json.dumps(nutrientes, ensure_ascii=False), criado_em=agora.isoformat(),
            itens=json.dumps(itens, ensure_ascii=False) if itens else None, momento=momento))
        return res.inserted_primary_key[0]


def atualizar_refeicao(refeicao_id: int, nome: str, nutrientes: dict,
                       itens: list[dict] | None = None, momento: str | None = None) -> None:
    valores = dict(nome=nome, nutrientes=json.dumps(nutrientes, ensure_ascii=False),
                   itens=json.dumps(itens, ensure_ascii=False) if itens else None)
    if momento is not None:
        valores["momento"] = momento
    with _engine().begin() as con:
        con.execute(update(refeicoes).where(refeicoes.c.id == refeicao_id).values(**valores))


def refeicoes_do_dia(uid, dia: str) -> list[dict]:
    with _engine().connect() as con:
        linhas = con.execute(select(refeicoes).where(
            and_(refeicoes.c.utilizador_id == uid, refeicoes.c.data == dia))
            .order_by(refeicoes.c.hora)).mappings().all()
    resultado = []
    for l in linhas:
        d = dict(l)
        d["nutrientes"] = json.loads(d["nutrientes"])
        d["itens"] = json.loads(d["itens"]) if d.get("itens") else None
        resultado.append(d)
    return resultado


def todas_refeicoes(uid) -> list[dict]:
    with _engine().connect() as con:
        linhas = con.execute(select(refeicoes).where(refeicoes.c.utilizador_id == uid)
                             .order_by(refeicoes.c.data, refeicoes.c.hora)).mappings().all()
    out = []
    for l in linhas:
        d = dict(l)
        d["nutrientes"] = json.loads(d["nutrientes"])
        out.append(d)
    return out


def todos_exercicios(uid) -> list[dict]:
    with _engine().connect() as con:
        linhas = con.execute(select(exercicios).where(exercicios.c.utilizador_id == uid)
                             .order_by(exercicios.c.data)).mappings().all()
    return [dict(l) for l in linhas]


def apagar_refeicao(refeicao_id: int) -> None:
    with _engine().begin() as con:
        linha = con.execute(select(refeicoes.c.foto_path).where(
            refeicoes.c.id == refeicao_id)).first()
        con.execute(delete(refeicoes).where(refeicoes.c.id == refeicao_id))
    if linha and linha[0]:
        Path(linha[0]).unlink(missing_ok=True)


def totais_do_dia(uid, dia: str) -> dict:
    refs = refeicoes_do_dia(uid, dia)
    totais: dict[str, float] = {}
    for ref in refs:
        for chave, valor in ref["nutrientes"].items():
            if isinstance(valor, (int, float)):
                totais[chave] = totais.get(chave, 0) + valor
    totais["agua_ml"] = totais.get("agua_ml", 0) + agua_do_dia(uid, dia)
    # suplementos (catálogo + próprios) e vitamina D do sol contam nos dias ativos ou hoje
    if refs or dia == date.today().strftime("%Y-%m-%d"):
        for chave, valor in suplementos_nutrientes(uid).items():
            totais[chave] = totais.get(chave, 0) + valor
        perfil = obter_perfil(uid)
        if perfil and perfil.get("sol_habitual"):
            totais["vit_d_ug"] = totais.get("vit_d_ug", 0) + sol.vit_d(perfil["sol_habitual"])
    return totais


def tem_refeicoes(uid, dia: str) -> bool:
    with _engine().connect() as con:
        return con.execute(select(refeicoes.c.id).where(
            and_(refeicoes.c.utilizador_id == uid, refeicoes.c.data == dia)).limit(1)).first() is not None


def dias_com_registos(uid, limite: int = 30) -> list[str]:
    with _engine().connect() as con:
        linhas = con.execute(select(refeicoes.c.data).where(refeicoes.c.utilizador_id == uid)
                             .distinct().order_by(refeicoes.c.data.desc()).limit(limite)).all()
    return [l[0] for l in linhas]


def alimentos_recentes(uid, limite: int = 15) -> list[dict]:
    """Alimentos usados recentemente (distintos), com a última porção usada."""
    with _engine().connect() as con:
        linhas = con.execute(select(refeicoes.c.itens).where(
            and_(refeicoes.c.utilizador_id == uid, refeicoes.c.itens.isnot(None)))
            .order_by(refeicoes.c.criado_em.desc()).limit(80)).all()
    vistos: dict[str, dict] = {}
    for (itens_json,) in linhas:
        for item in json.loads(itens_json):
            if item["nome"] not in vistos:
                vistos[item["nome"]] = item
        if len(vistos) >= limite:
            break
    return list(vistos.values())[:limite]


# ---------- Exercício ----------

def registar_exercicio(uid, nome: str, duracao_min: int, kcal: int, dia: str | None = None) -> int:
    dia = dia or date.today().strftime("%Y-%m-%d")
    with _engine().begin() as con:
        res = con.execute(insert(exercicios).values(
            utilizador_id=uid, data=dia, nome=nome, duracao_min=duracao_min, kcal=kcal,
            criado_em=datetime.now().isoformat()))
        return res.inserted_primary_key[0]


def exercicios_do_dia(uid, dia: str) -> list[dict]:
    with _engine().connect() as con:
        linhas = con.execute(select(exercicios).where(
            and_(exercicios.c.utilizador_id == uid, exercicios.c.data == dia))
            .order_by(exercicios.c.criado_em)).mappings().all()
    return [dict(l) for l in linhas]


def exercicio_kcal_do_dia(uid, dia: str) -> int:
    return sum(e["kcal"] for e in exercicios_do_dia(uid, dia))


def apagar_exercicio(ex_id: int) -> None:
    with _engine().begin() as con:
        con.execute(delete(exercicios).where(exercicios.c.id == ex_id))


# ---------- Estado de saúde (modo doente) ----------

def definir_estado(uid, estado: str, tipo: str | None = None, dia: str | None = None) -> None:
    dia = dia or date.today().strftime("%Y-%m-%d")
    with _engine().begin() as con:
        existe = con.execute(select(estado_saude.c.utilizador_id).where(
            and_(estado_saude.c.utilizador_id == uid, estado_saude.c.data == dia))).first()
        if existe:
            con.execute(update(estado_saude).where(
                and_(estado_saude.c.utilizador_id == uid, estado_saude.c.data == dia)).values(
                estado=estado, tipo=tipo))
        else:
            con.execute(insert(estado_saude).values(
                utilizador_id=uid, data=dia, estado=estado, tipo=tipo))


def obter_estado(uid, dia: str) -> dict:
    with _engine().connect() as con:
        linha = con.execute(select(estado_saude).where(
            and_(estado_saude.c.utilizador_id == uid, estado_saude.c.data == dia))).mappings().first()
    return dict(linha) if linha else {"estado": "Saudável", "tipo": None}


# ---------- Água ----------

def adicionar_agua(uid, ml: int, dia: str | None = None) -> None:
    dia = dia or date.today().strftime("%Y-%m-%d")
    with _engine().begin() as con:
        atual = con.execute(select(agua.c.ml).where(
            and_(agua.c.utilizador_id == uid, agua.c.data == dia))).first()
        if atual is None:
            con.execute(insert(agua).values(utilizador_id=uid, data=dia, ml=max(0, ml)))
        else:
            con.execute(update(agua).where(
                and_(agua.c.utilizador_id == uid, agua.c.data == dia)).values(
                ml=max(0, atual[0] + ml)))


def agua_do_dia(uid, dia: str) -> int:
    with _engine().connect() as con:
        linha = con.execute(select(agua.c.ml).where(
            and_(agua.c.utilizador_id == uid, agua.c.data == dia))).first()
    return linha[0] if linha else 0


# ---------- Peso ----------

def registar_peso(uid, kg: float, dia: str | None = None) -> None:
    dia = dia or date.today().strftime("%Y-%m-%d")
    with _engine().begin() as con:
        existe = con.execute(select(peso_registos.c.kg).where(
            and_(peso_registos.c.utilizador_id == uid, peso_registos.c.data == dia))).first()
        if existe is None:
            con.execute(insert(peso_registos).values(utilizador_id=uid, data=dia, kg=kg))
        else:
            con.execute(update(peso_registos).where(
                and_(peso_registos.c.utilizador_id == uid, peso_registos.c.data == dia)).values(kg=kg))


def historico_peso(uid) -> list[dict]:
    with _engine().connect() as con:
        linhas = con.execute(select(peso_registos.c.data, peso_registos.c.kg).where(
            peso_registos.c.utilizador_id == uid).order_by(peso_registos.c.data)).mappings().all()
    return [dict(l) for l in linhas]


# ---------- Alimentos próprios ----------

def criar_alimento(uid, nome: str, por_100g: dict, porcoes: list) -> int:
    with _engine().begin() as con:
        res = con.execute(insert(alimentos_custom).values(
            utilizador_id=uid, nome=nome, por_100g=json.dumps(por_100g, ensure_ascii=False),
            porcoes=json.dumps(porcoes, ensure_ascii=False), criado_em=datetime.now().isoformat()))
        return res.inserted_primary_key[0]


def listar_alimentos_custom(uid) -> list[dict]:
    with _engine().connect() as con:
        linhas = con.execute(select(alimentos_custom).where(
            alimentos_custom.c.utilizador_id == uid).order_by(alimentos_custom.c.nome)).mappings().all()
    return [{"id": l["id"], "nome": l["nome"], "categoria": "⭐ Os meus",
             "por_100g": json.loads(l["por_100g"]), "porcoes": json.loads(l["porcoes"])}
            for l in linhas]


def apagar_alimento(alimento_id: int) -> None:
    with _engine().begin() as con:
        con.execute(delete(alimentos_custom).where(alimentos_custom.c.id == alimento_id))


# ---------- Favoritos ----------

def guardar_favorito(uid, nome: str, itens: list) -> int:
    with _engine().begin() as con:
        res = con.execute(insert(favoritos).values(
            utilizador_id=uid, nome=nome, itens=json.dumps(itens, ensure_ascii=False),
            criado_em=datetime.now().isoformat()))
        return res.inserted_primary_key[0]


def listar_favoritos(uid) -> list[dict]:
    with _engine().connect() as con:
        linhas = con.execute(select(favoritos).where(
            favoritos.c.utilizador_id == uid).order_by(favoritos.c.nome)).mappings().all()
    return [{"id": l["id"], "nome": l["nome"], "itens": json.loads(l["itens"])} for l in linhas]


def apagar_favorito(favorito_id: int) -> None:
    with _engine().begin() as con:
        con.execute(delete(favoritos).where(favoritos.c.id == favorito_id))


# ---------- Definições (globais) ----------

def guardar_definicao(chave: str, valor: str) -> None:
    with _engine().begin() as con:
        existe = con.execute(select(definicoes.c.chave).where(definicoes.c.chave == chave)).first()
        if existe:
            con.execute(update(definicoes).where(definicoes.c.chave == chave).values(valor=valor))
        else:
            con.execute(insert(definicoes).values(chave=chave, valor=valor))


def obter_definicao(chave: str, predefinido: str = "") -> str:
    with _engine().connect() as con:
        linha = con.execute(select(definicoes.c.valor).where(definicoes.c.chave == chave)).first()
    return linha[0] if linha else predefinido
