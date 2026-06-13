"""Análise de refeições com a API Claude — foto e/ou descrição → nutrientes."""
import base64
import io
import json

import anthropic
from PIL import Image

MODELOS = {
    "claude-opus-4-8": "Opus 4.8 — o mais inteligente (recomendado, ~$0.02-0.05/análise)",
    "claude-sonnet-4-6": "Sonnet 4.6 — rápido e bom (~$0.01-0.03/análise)",
    "claude-haiku-4-5": "Haiku 4.5 — o mais barato (~$0.005-0.01/análise)",
}
MODELO_PREDEFINIDO = "claude-opus-4-8"

# Campos numéricos que a análise devolve (totais da refeição inteira)
CAMPOS_NUTRIENTES = [
    "kcal", "proteina_g", "hidratos_g", "gordura_g", "gordura_saturada_g",
    "fibra_g", "acucar_g", "sodio_mg", "potassio_mg", "calcio_mg", "ferro_mg",
    "magnesio_mg", "zinco_mg", "vit_a_ug", "vit_c_mg", "vit_d_ug", "vit_e_mg",
    "vit_k_ug", "vit_b1_mg", "vit_b2_mg", "vit_b3_mg", "vit_b6_mg", "folato_ug",
    "vit_b12_ug", "omega3_g", "agua_ml", "cafeina_mg",
]

_SCHEMA = {
    "type": "object",
    "properties": {
        "nome_refeicao": {"type": "string",
                          "description": "Nome curto e natural da refeição em português, ex: 'Bacalhau com batatas e brócolos'"},
        "alimentos": {
            "type": "array",
            "description": "Cada alimento identificado e a porção estimada",
            "items": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string"},
                    "porcao_estimada": {"type": "string", "description": "ex: '150 g', '1 chávena'"},
                },
                "required": ["nome", "porcao_estimada"],
                "additionalProperties": False,
            },
        },
        "confianca": {"type": "string", "enum": ["alta", "media", "baixa"],
                      "description": "Confiança na estimativa das porções e valores"},
        "notas": {"type": "string",
                  "description": "Observações úteis em português: incertezas, sugestões, avisos"},
        "nutrientes": {
            "type": "object",
            "description": "Totais estimados para a refeição INTEIRA",
            "properties": {campo: {"type": "number"} for campo in CAMPOS_NUTRIENTES},
            "required": CAMPOS_NUTRIENTES,
            "additionalProperties": False,
        },
    },
    "required": ["nome_refeicao", "alimentos", "confianca", "notas", "nutrientes"],
    "additionalProperties": False,
}

_SYSTEM = """És um nutricionista especializado em análise de refeições, com bom conhecimento
da cozinha portuguesa e dos tamanhos de porção habituais em Portugal.

Recebes uma fotografia de uma refeição e/ou uma descrição em texto. A tua tarefa:
1. Identificar cada alimento e bebida presentes.
2. Estimar a porção de cada um (usa referências visuais: tamanho do prato, talheres, etc.).
3. Calcular os totais nutricionais da refeição INTEIRA: calorias, macronutrientes,
   vitaminas e minerais. Usa valores realistas de tabelas de composição de alimentos.
4. Se algum valor for desconhecido ou irrelevante para os alimentos presentes, usa 0.
5. agua_ml refere-se à água contida nos alimentos e bebidas da refeição.
6. Sê honesto na confiança: 'baixa' se a foto for ambígua ou a descrição vaga.

Responde sempre em português de Portugal."""


def _preparar_imagem(dados: bytes, lado_max: int = 1100) -> str:
    """Redimensiona e converte para JPEG base64 — reduz custo sem perder detalhe útil."""
    img = Image.open(io.BytesIO(dados))
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((lado_max, lado_max))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return base64.standard_b64encode(buffer.getvalue()).decode("utf-8")


def analisar_refeicao(api_key: str, modelo: str, descricao: str = "",
                      imagem_bytes: bytes | None = None) -> dict:
    """Analisa a refeição e devolve o dicionário estruturado (nome, alimentos, nutrientes...).

    Levanta ValueError com mensagem amigável em caso de erro."""
    if not imagem_bytes and not descricao.strip():
        raise ValueError("Tira uma foto ou descreve a refeição primeiro.")

    conteudo = []
    if imagem_bytes:
        conteudo.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg",
                       "data": _preparar_imagem(imagem_bytes)},
        })
    pedido = "Analisa esta refeição e calcula os valores nutricionais."
    if descricao.strip():
        pedido += f"\n\nDescrição/contexto do utilizador: {descricao.strip()}"
    conteudo.append({"type": "text", "text": pedido})

    client = anthropic.Anthropic(api_key=api_key)
    kwargs = dict(
        model=modelo,
        max_tokens=8000,
        system=_SYSTEM,
        messages=[{"role": "user", "content": conteudo}],
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
    )
    # pensamento adaptativo melhora a estimativa de porções (não suportado no Haiku)
    if "haiku" not in modelo:
        kwargs["thinking"] = {"type": "adaptive"}

    try:
        resposta = client.messages.create(**kwargs)
    except anthropic.AuthenticationError:
        raise ValueError("Chave de API inválida. Verifica-a nas Definições.")
    except anthropic.RateLimitError:
        raise ValueError("Demasiados pedidos seguidos. Espera um minuto e tenta outra vez.")
    except anthropic.APIConnectionError:
        raise ValueError("Sem ligação à internet (ou a API está inacessível).")
    except anthropic.APIStatusError as e:
        raise ValueError(f"Erro da API ({e.status_code}): {e.message}")

    texto = next((b.text for b in resposta.content if b.type == "text"), "")
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        raise ValueError("A resposta da IA veio num formato inesperado. Tenta novamente.")


def testar_ligacao(api_key: str, modelo: str) -> str:
    """Valida a chave de API sem gastar tokens. Devolve o nome do modelo."""
    client = anthropic.Anthropic(api_key=api_key)
    try:
        info = client.models.retrieve(modelo)
        return info.display_name
    except anthropic.AuthenticationError:
        raise ValueError("Chave de API inválida.")
    except anthropic.NotFoundError:
        raise ValueError(f"Modelo '{modelo}' não encontrado.")
    except anthropic.APIConnectionError:
        raise ValueError("Sem ligação à internet.")
