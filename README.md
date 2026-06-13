# 🥗 NutriDia

Diário alimentar: escolhes o alimento e a porção (1 fatia de pão, 2 ovos, 1 fatia de
bolo…) e a app calcula calorias, vitaminas e minerais — não precisas de saber os valores.
Acompanha o teu objetivo (manter/emagrecer/engordar), pontua o teu dia em 9 áreas de
bem-estar e avisa-te de carências nutricionais. **Gratuito, sem chaves nem IA.**

## Como usar

- **Uso normal (só tu):** duplo clique em `Iniciar NutriDia.bat`.
- **Mostrar a um amigo (link temporário):** duplo clique em `Partilhar (tunel).bat`.
  Aparece um link `https://...trycloudflare.com` — envia-o ao teu amigo. Para terminar,
  fecha a janela (o link morre de imediato). O teu PC tem de ficar ligado durante a partilha.
  ⚠️ Enquanto o link está aberto, quem o tiver mexe no teu diário (não tem palavra-passe) —
  partilha só com quem confias e fecha quando acabarem.

1. **Duplo clique em `Iniciar NutriDia.bat`** — abre no browser automaticamente.
2. Na primeira vez, preenche o **Perfil** (sexo, idade, peso, altura, exercício, objetivo).
3. A cada refeição: **Registar refeição** → escolhe alimentos comuns (ou pesquisa um
   produto de marca) → define a porção → Guardar. Não há nada a configurar.

## De onde vêm os valores

- **Alimentos comuns** — tabela local com ~60 alimentos portugueses já com porções típicas.
- **Pesquisar produto** — base gratuita [Open Food Facts](https://pt.openfoodfacts.org)
  (por nome ou código de barras), com milhares de produtos de marca.

## O que faz

| Página | Função |
|---|---|
| 📊 Painel | Calorias/macros vs alvo, água, 9 pontuações de bem-estar do dia |
| 🍽️ Registar | Alimentos comuns + pesquisa Open Food Facts → cesto → guardar |
| 📅 Histórico | Refeições passadas, gráficos de 14 dias, registo e evolução do peso |
| 🔬 Carências | Média de 7 dias vs doses recomendadas + sintomas do que falta |
| 👤 Perfil | TMB (Mifflin-St Jeor), manutenção (TDEE) e alvos personalizados |
| ⚙️ Definições | Região da base de dados de produtos (Portugal/Brasil/Mundo) |

## Pontuações de bem-estar

🧠 Cérebro & Foco · ⚡ Energia · 😴 Descanso & Sono · 🛡️ Imunidade ·
💪 Músculo & Recuperação · ❤️ Coração · ✨ Pele & Cabelo · 🌿 Digestão · 🙂 Humor

Cada uma combina os nutrientes que a ciência associa a essa área
(ex.: Descanso = magnésio + cálcio + B6, penalizado por cafeína e açúcar).

## Estrutura técnica

- **Python 3.12 + Streamlit** (interface), **SQLite** (dados locais em `data/nutridia.db`)
- **Open Food Facts** via `urllib` (sem chave, sem dependências extra)
- Tudo offline exceto a pesquisa de produtos de marca; dados só no teu computador
- Dependências no venv local `.venv\`

```
nutri-app/
├── app.py                  # entrada (st.navigation)
├── core/
│   ├── db.py               # SQLite: perfil, refeições, água, peso, definições
│   ├── calc.py             # TMB, TDEE, alvos de calorias/macros/água
│   ├── nutrients.py        # campos canónicos, escalar(), DDRs, limites, carências
│   ├── foods.py            # tabela local de alimentos comuns + porções
│   ├── openfoodfacts.py    # pesquisa OFF (nome e código de barras)
│   └── scores.py           # 9 pontuações de bem-estar
└── views/                  # uma página por ficheiro
```

⚕️ **Aviso:** valores estimados, para fins informativos — não substitui aconselhamento
médico ou de um nutricionista.
