# 🥗 NutriDia

Diário alimentar inteligente: escolhes o alimento e a porção (1 fatia de pão, 2 ovos,
1 fatia de bolo…) e a app calcula calorias, vitaminas e minerais — não precisas de saber
os valores. Acompanha o teu objetivo (manter/emagrecer/engordar), pontua o teu dia em
**10 áreas de bem-estar**, adapta-se às tuas alergias e condições de saúde, e avisa-te de
carências nutricionais. **Gratuito, sem chaves nem IA.**

## Como usar

- **Uso normal (só tu):** duplo clique em `Iniciar NutriDia.bat` — abre no browser
  automaticamente. Mantém a janela aberta enquanto usas (é a app a correr).
- **Mostrar a um amigo (link temporário):** duplo clique em `Partilhar (tunel).bat`.
  Aparece um link `https://...trycloudflare.com` — envia-o ao teu amigo. Para terminar,
  fecha a janela (o link morre de imediato). O teu PC tem de ficar ligado durante a partilha.
  ⚠️ Enquanto o link está aberto, quem o tiver mexe no teu diário (não tem palavra-passe) —
  partilha só com quem confias e fecha quando acabarem.

1. Na primeira vez, preenche o **Perfil** (sexo, idade, peso, altura, exercício, objetivo)
   e, se quiseres, alergias, preferências, condições de saúde e suplementos.
2. A cada refeição: **Registar refeição** → escolhe alimentos comuns, pesquisa um produto de
   marca **ou lê o código de barras com a câmara** → define a porção → Guardar.
3. Vê o teu **Painel** ao longo do dia e acompanha o **Progresso** e as **Carências**.

## De onde vêm os valores

- **Alimentos comuns** — tabela local com ~140 alimentos portugueses já com porções típicas.
- **Pesquisar produto / código de barras** — base gratuita
  [Open Food Facts](https://pt.openfoodfacts.org) (por nome, código escrito ou **foto do
  código de barras**), com milhares de produtos de marca.

## O que faz

| Página | Função |
|---|---|
| 📊 Painel | Calorias/macros vs alvo, água, exercício, 10 pontuações de bem-estar, avisos das tuas condições de saúde e sugestão do que comer a seguir |
| 🍽️ Registar | Alimentos comuns + Open Food Facts (nome, código ou câmara) → cesto com semáforo 🟢🟡🔴 → guardar (incl. registo retroativo) |
| 🥣 Os meus alimentos | Criar alimentos e receitas próprios |
| 🔍 Explorar | Ver todos os nutrientes de um alimento por porção/peso, com % da tua dose diária |
| 📅 Histórico | Refeições passadas (editáveis), gráficos e evolução do peso |
| 🗓️ Plano semanal | Ementa de 7 dias gerada à tua medida (calorias, alergias, preferências, condições) |
| 🎯 Progresso | Sequências, medalhas, projeção do peso-alvo e relatório de 7/30 dias (exportável) |
| 🔬 Carências | Médias de 7 e 30 dias vs recomendado, sintomas do que falta e lista de compras |
| 👤 Perfil | TMB (Mifflin-St Jeor), manutenção (TDEE), alvos, alergias, condições, suplementos e sol |
| ⚙️ Definições | Região da base de dados de produtos (Portugal/Brasil/Mundo) e idioma |

## Funcionalidades que se adaptam a ti

- **🩺 Condições de saúde** — diabetes, tensão alta e colesterol alto apertam os limites a
  moderar (açúcar/sódio/gordura saturada), avisam-te no Painel e filtram as sugestões.
  *(Não substitui aconselhamento médico.)*
- **🚦 Semáforo por refeição** — ao montar a refeição, vês logo quanto do limite diário de
  açúcar/sal/gordura saturada ela gasta, já ajustado às tuas condições.
- **🥗 Alergias e preferências** — vegetariano, vegano, pescetariano, sem carne vermelha e
  12 alergénios; adaptam as refeições inteligentes e o plano semanal.
- **💊 Suplementos e sol** — com doses/dia ajustáveis; contam automaticamente nos teus totais.
- **🍺 Álcool** — a app sabe que a cerveja/vinho não hidratam e penaliza as pontuações que o
  álcool, em excesso, prejudica (sono, humor, foco…).
- **🤒 Modo doente** — dias doentes não quebram as tuas sequências e dão conforto alimentar.

## Pontuações de bem-estar (10)

🧠 Cérebro & Foco · ⚡ Energia · 😴 Descanso & Sono · 🛡️ Imunidade ·
💪 Músculo & Recuperação · ❤️ Coração · ✨ Pele & Cabelo · 🌿 Digestão · 🙂 Humor ·
💗 Vitalidade & Libido

Cada uma combina os nutrientes que a ciência associa a essa área
(ex.: Descanso = magnésio + cálcio + B6, penalizado por cafeína, açúcar e álcool).

## Estrutura técnica

- **Python 3.12 + Streamlit** (interface), **SQLite** (dados locais em `data/nutridia.db`)
- **Open Food Facts** via `urllib` e leitura de códigos de barras via `zxing-cpp`
- Tudo offline exceto a pesquisa de produtos de marca; dados só no teu computador
- Multi-utilizador com login opcional; na nuvem corre em Postgres (ver `DEPLOY.md`)
- Dependências no venv local `.venv\` (`requirements.txt`)

```
nutri-app/
├── app.py                  # entrada (st.navigation)
├── core/
│   ├── db.py               # SQLite/Postgres: perfil, refeições, água, peso, exercício…
│   ├── calc.py             # TMB, TDEE, alvos de calorias/macros/água
│   ├── nutrients.py        # campos canónicos, escalar(), DDRs, limites, carências
│   ├── foods.py            # tabela local de alimentos comuns + porções
│   ├── openfoodfacts.py    # pesquisa OFF (nome e código de barras)
│   ├── barcode.py          # leitura de código de barras a partir de foto
│   ├── scores.py           # 10 pontuações de bem-estar
│   ├── condicoes.py        # condições de saúde (limites + avisos)
│   ├── sugestoes.py        # refeições inteligentes (respeitam dieta e condições)
│   ├── plano.py            # gerador do plano semanal
│   ├── alcool.py           # penalização por álcool em excesso
│   └── …                   # dieta, suplementos, exercicios, metas, momentos, sol…
└── views/                  # uma página por ficheiro
```

⚕️ **Aviso:** valores estimados, para fins informativos — não substitui aconselhamento
médico ou de um nutricionista.
