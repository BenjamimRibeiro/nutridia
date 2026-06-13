"""Pesquisa de produtos na base gratuita Open Food Facts (sem chave de API).

Mapeia os nutrientes da OFF (valores por 100 g) para o nosso conjunto de campos.
"""
import json
import urllib.parse
import urllib.request

from core import nutrients

_DOMINIOS = {"pt": "pt.openfoodfacts.org", "br": "br.openfoodfacts.org",
             "world": "world.openfoodfacts.org"}
_UA = "NutriDia/1.0 (diario alimentar pessoal)"
_CAMPOS_OFF = "product_name,product_name_pt,generic_name,brands,nutriments,code,quantity"

# chave OFF (por 100 g) -> (nosso campo, fator de conversão para a nossa unidade)
# OFF guarda quase tudo em gramas: minerais/vitaminas em mg -> x1000; em µg -> x1e6.
_MAPA = {
    "energy-kcal_100g": ("kcal", 1),
    "proteins_100g": ("proteina_g", 1),
    "carbohydrates_100g": ("hidratos_g", 1),
    "fat_100g": ("gordura_g", 1),
    "saturated-fat_100g": ("gordura_saturada_g", 1),
    "fiber_100g": ("fibra_g", 1),
    "sugars_100g": ("acucar_g", 1),
    "sodium_100g": ("sodio_mg", 1000),
    "potassium_100g": ("potassio_mg", 1000),
    "calcium_100g": ("calcio_mg", 1000),
    "iron_100g": ("ferro_mg", 1000),
    "magnesium_100g": ("magnesio_mg", 1000),
    "zinc_100g": ("zinco_mg", 1000),
    "vitamin-a_100g": ("vit_a_ug", 1_000_000),
    "vitamin-c_100g": ("vit_c_mg", 1000),
    "vitamin-d_100g": ("vit_d_ug", 1_000_000),
    "vitamin-e_100g": ("vit_e_mg", 1000),
    "vitamin-k_100g": ("vit_k_ug", 1_000_000),
    "vitamin-b1_100g": ("vit_b1_mg", 1000),
    "vitamin-b2_100g": ("vit_b2_mg", 1000),
    "vitamin-pp_100g": ("vit_b3_mg", 1000),
    "vitamin-b6_100g": ("vit_b6_mg", 1000),
    "vitamin-b9_100g": ("folato_ug", 1_000_000),
    "vitamin-b12_100g": ("vit_b12_ug", 1_000_000),
    "omega-3-fat_100g": ("omega3_g", 1),
    "caffeine_100g": ("cafeina_mg", 1000),
}


def _dominio(pais: str) -> str:
    return _DOMINIOS.get(pais, _DOMINIOS["pt"])


def _por_100g(nutriments: dict) -> dict:
    base = {k: 0.0 for k in nutrients.CAMPOS_NUTRIENTES}
    for off_key, (campo, fator) in _MAPA.items():
        valor = nutriments.get(off_key)
        if isinstance(valor, (int, float)):
            base[campo] = round(valor * fator, 3)
    if not base["kcal"]:  # fallback: energia em kJ
        kj = nutriments.get("energy_100g") or nutriments.get("energy-kj_100g")
        if isinstance(kj, (int, float)) and kj:
            base["kcal"] = round(kj / 4.184)
    return base


def _nome(prod: dict) -> str:
    nome = (prod.get("product_name_pt") or prod.get("product_name")
            or prod.get("generic_name") or "Produto sem nome").strip()
    marca = (prod.get("brands") or "").split(",")[0].strip()
    return f"{nome} — {marca}" if marca else nome


def _obter(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=12) as resp:
        return json.loads(resp.read().decode("utf-8"))


def pesquisar(termo: str, pais: str = "pt", limite: int = 25) -> list[dict]:
    """Pesquisa produtos por texto. Devolve lista de {nome, por_100g, code, quantidade}."""
    if not termo.strip():
        return []
    url = (f"https://{_dominio(pais)}/cgi/search.pl"
           f"?search_terms={urllib.parse.quote(termo)}&search_simple=1&action=process"
           f"&json=1&page_size={limite}&fields={_CAMPOS_OFF}")
    try:
        dados = _obter(url)
    except Exception as e:
        raise ValueError(f"Não foi possível pesquisar (verifica a internet). [{e}]")

    resultados = []
    for prod in dados.get("products", []):
        por100 = _por_100g(prod.get("nutriments", {}))
        if not por100["kcal"]:  # sem energia conhecida = inútil para nós
            continue
        resultados.append({"nome": _nome(prod), "por_100g": por100,
                           "code": prod.get("code", ""), "quantidade": prod.get("quantity", "")})
    return resultados


def enriquecer(prod: dict) -> tuple[dict, str | None]:
    """Estima vitaminas/minerais em falta a partir do alimento mais parecido da
    tabela local. Só preenche campos a 0; devolve (produto, nome_do_alimento_usado)."""
    from core import foods

    tokens = set(nutrients.normalizar(prod["nome"]).split())
    melhor, melhor_score = None, 0
    for alimento in foods.ALIMENTOS:
        score = len(tokens & set(nutrients.normalizar(alimento["nome"]).split()))
        if score > melhor_score:
            melhor, melhor_score = alimento, score
    if not melhor or melhor_score < 1:
        return prod, None

    por_100g = dict(prod["por_100g"])
    micros = list(nutrients.DDR) + ["fibra_g"]
    preenchidos = 0
    for chave in micros:
        if por_100g.get(chave, 0) == 0 and melhor["por_100g"].get(chave, 0) > 0:
            por_100g[chave] = melhor["por_100g"][chave]
            preenchidos += 1
    if preenchidos == 0:
        return prod, None
    novo = dict(prod)
    novo["por_100g"] = por_100g
    return novo, melhor["nome"]


def por_codigo(codigo: str, pais: str = "pt") -> dict:
    """Procura um produto pelo código de barras."""
    url = (f"https://{_dominio(pais)}/api/v2/product/{urllib.parse.quote(codigo)}"
           f"?fields={_CAMPOS_OFF}")
    try:
        dados = _obter(url)
    except Exception as e:
        raise ValueError(f"Não foi possível obter o produto (verifica a internet). [{e}]")
    if dados.get("status") != 1 or "product" not in dados:
        raise ValueError("Código de barras não encontrado no Open Food Facts.")
    prod = dados["product"]
    por100 = _por_100g(prod.get("nutriments", {}))
    if not por100["kcal"]:
        raise ValueError("Este produto não tem valores nutricionais na base de dados.")
    return {"nome": _nome(prod), "por_100g": por100, "code": codigo,
            "quantidade": prod.get("quantity", "")}
