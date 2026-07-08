# NutriDia — diário alimentar inteligente

App Streamlit (tudo em **português de Portugal**) para registar refeições escolhendo
alimentos (tabela local de alimentos comuns + pesquisa Open Food Facts) e acompanhar
calorias, micronutrientes, pontuações de bem-estar e peso. **Sem IA, sem chaves pagas.**

## Comandos

- Correr: `.venv\Scripts\streamlit.exe run app.py` (ou duplo clique em `Iniciar NutriDia.bat`)
- Instalar deps: `.venv\Scripts\pip install -r requirements.txt`
- Deps: streamlit, anthropic, pillow, pandas (venv local `.venv\`)

## Arquitetura

- `app.py` — entrada; `st.navigation` com as páginas-função (`views/*.mostrar()`)
- `core/db.py` — **SQLAlchemy Core** (esquema via `Table`/`metadata.create_all`).
  Motor de `NUTRIDIA_DB_URL` (default `sqlite:///data/nutridia.db`; na nuvem = Postgres).
  SQL portável (sem `ON CONFLICT`: upserts manuais select→insert/update). `reset_engine()`
  para testes. Multi-utilizador (tabela `utilizadores` com username/pass_hash/pass_salt);
  quase todas as funções recebem `uid` como 1º arg. `_migrar()` faz ALTER ADD COLUMN das
  colunas de auth em BDs antigas. Refeições guardam `itens` (JSON) além dos totais.
- `core/auth.py` — hash PBKDF2-SHA256 (stdlib, sem dependências). `db.criar_conta`,
  `db.autenticar`, `db.username_existe`.
- **Login (`views/login.py`)**: só na versão online. `app.py` calcula `REQUER_LOGIN`
  = url Postgres OU secret `require_login`. Local (SQLite) → sem login, utilizador default
  "Eu" automático. Online → ecrã de login/registo; `st.session_state["uid"]`/`["nome"]`.
- **Deploy:** ver `DEPLOY.md` (GitHub privado → Supabase Postgres → Streamlit Cloud +
  secret `database_url`). `.gitignore` exclui `data/`, segredos, `.venv`, `cloudflared.exe`.
  `core/ai.py` está dormente e importa anthropic/PIL (já NÃO estão em requirements) —
  não é importado por nada; se reativares, repõe as deps.
- `core/metas.py` — sequências (dia dentro do alvo = 80-110% kcal), medalhas.
- `core/calc.py::projecao_peso` — estima data de chegada ao peso-alvo (tendência real
  do histórico de peso se houver ≥1 semana de registos; senão ritmo planeado).
- `core/calc.py` — TMB Mifflin-St Jeor, TDEE por fator de atividade, alvos de
  kcal/macros/água. Corte nunca desce abaixo da TMB.
- `core/nutrients.py` — fonte canónica: `CAMPOS_NUTRIENTES` (27 chaves) e `escalar()`
  (por-100g → porção). `DDR` (doses recomendadas por sexo), `LIMITES` (sódio, açúcar,
  gordura saturada, cafeína) e `CARENCIAS` (sintomas curto/longo prazo + fontes).
- `core/foods.py` — tabela local de ~110 alimentos comuns PT (valores por 100 g + porções
  típicas). Helper `_f(...)` preenche os 27 campos a 0. Inclui categoria "Sopas e pratos"
  (pratos/sopas/sobremesas típicos PT) e hambúrgueres em "Proteínas".
- `core/momentos.py` — `MOMENTOS` (peq-almoço/almoço/lanche/jantar/ceia/snack), `emoji()`,
  `sugerir(hora)`. Refeições têm coluna `momento` (db); registo/painel/histórico usam-na
  (painel agrupa refeições por momento). Foto opcional via `db.guardar_refeicao(foto_bytes=)`.
- `core/exercicios.py` — catálogo de atividades (MET) + `kcal(met, peso, min)`. Tabela `exercicios`
  no db; o `db.exercicio_kcal_do_dia` soma ao alvo de calorias no painel e nas metas (alvos_aj).
- `core/suplementos.py` — `CATALOGO` (ómega-3, proteína, multivit, etc.) + `nutrientes_de(nomes)`.
  Rotina do utilizador em `perfis.suplementos` (JSON); `db.totais_do_dia` soma-os nos dias
  ativos/hoje. `db.suplementos_nutrientes` escala cada suplemento pelas doses/dia guardadas em
  `perfis.suplementos_doses` (JSON nome→fator, 1 por defeito; editável no Perfil). Suplementos
  sem nutrientes seguidos (ex.: creatina) avisam que não contam nos totais.
  `db.guardar_preferencias(uid, restricoes, alergias, suplementos, sol_habitual, doses, condicoes)`
  — `doses`/`condicoes` a `None` NÃO mexem nessas colunas; `obter_perfil` devolve restricoes/
  alergias/suplementos/condicoes como listas e suplementos_doses como dict. NÃO mexer nelas no
  `guardar_perfil` (senão o registo de peso apaga-as).
- `core/condicoes.py` — condições de saúde (patologias): `Diabetes`→açúcar, `Tensão alta`→sódio,
  `Colesterol alto`→gordura saturada, cada uma com um limite mais apertado que o geral e conselho.
  Guardadas em `perfis.condicoes` (JSON); seletor no Perfil (ao lado das alergias). O Painel mostra
  um aviso diário por condição (dentro/acima do limite) com AVISO de que não é conselho médico.
- `core/dieta.py` — alergias/preferências por palavras-chave do nome; `compativel(food, alergias, prefs)`.
  Pratos compostos com carne (francesinha, lasanha…) estão na lista `_CARNE` por nome.
- `core/sugestoes.py` — `para_carencia` e `para_agora` (filtram por `dieta.compativel`).
  Usado em Carências e Painel.
- `core/doenca.py` + tabela `estado_saude` (PK uid+data): modo doente. `db.definir_estado`/
  `obter_estado`. Dia doente NÃO quebra a streak (em `metas.sequencia_atual`). Painel mostra
  conforto alimentar por tipo, com AVISO de que não é conselho médico.
- `metas`/`carencias` contam "dias com registos" por `db.tem_refeicoes` (não por kcal),
  para os suplementos não criarem dias-fantasma.
- `core/openfoodfacts.py` — pesquisa OFF por nome (`/cgi/search.pl`) e código de barras
  (`/api/v2/product`), via `urllib` (sem dependência extra). `_MAPA` converte unidades
  OFF (g) → nossas (mg ×1000, µg ×1e6). Região (pt/br/world) na definição `off_pais`.
- `core/scores.py` — 10 pontuações de bem-estar (0-100%) = média ponderada de coberturas
  dos nutrientes benéficos + penalizações por excessos. kcal pontua por proximidade ao alvo.
  Inclui "Vitalidade & Libido" (zinco, vit D, ómega-3, magnésio, vit E, folato). Ao adicionar
  uma pontuação, atualizar SEMPRE os 3 dicts EN (`_NOMES_EN`/`_DESC_EN`/`_DICA_EN`) senão
  `descricao()`/`dica()` dão KeyError em inglês.
- `core/ai.py` — **dormente** (análise por IA desligada a pedido do utilizador; ficheiro
  mantido caso se reative). Não é importado por nenhuma view.
- `views/tema.py` — `aplicar()` injeta CSS (tema comida saudável: verdes/creme, fonte
  Nunito, cartões); `cabecalho(emoji, titulo, subtitulo)` é o banner usado em vez de
  `st.title` em todas as páginas. Cores base também em `.streamlit/config.toml`.
- `views/components.py` — `graficos_cobertura` (gráficos Altair separados por grupo:
  macros/minerais/vitaminas/a-moderar, barras coloridas por estado, alfabético) usado no
  Painel; `tabela_cobertura` (dataframe) no cesto e num expander do Painel;
  `lista_nutrientes` (markdown por alimento).
- `views/builder.py` — construtor de refeição REUTILIZÁVEL (Registar, editor do
  Histórico e receitas em Os meus alimentos). Cesto = lista de `{nome, gramas, por_100g}`;
  nutrientes calculados on-the-fly com `nutrients.escalar`.
  `adicionar_alimento(cesto, prefixo, pais, uid)` (uid ativa a categoria "⭐ Os meus"),
  `mostrar_itens(...)`, `totais(cesto)`. Keys de widgets levam `prefixo` para não colidir.
- `views/registar.py` — além do cesto: favoritos (carregar/guardar/apagar) e copiar
  refeição de outro dia (só refeições com `itens`). Expander "🕒 Comeste noutra altura?"
  com date_input + time_input → `db.guardar_refeicao(..., dia=, hora=)` (registo retroativo;
  `guardar_refeicao` aceita `hora` opcional, default = agora).
- `views/explorar.py` — página SÓ de leitura: procurar 1 alimento (tabela local ou OFF) e
  ver TODOS os nutrientes por 100 g / porção / peso à escolha, com %DDR do perfil e manchete
  "🌟 Rico em…" (nutrientes ≥20% do alvo). Reutiliza `components.tabela_cobertura`,
  `foods.porcao/nome`, `openfoodfacts`. Não escreve nada na BD.
- `views/meus_alimentos.py` — criar alimento simples (valores de 1 porção → por_100g)
  e receitas (cesto de ingredientes ÷ doses). Ficam em alimentos_custom.
- `views/metas.py` — página Progresso: streak, medalhas, projeção do peso-alvo.
- Pontuações no Painel: cartões HTML com barra colorida (verde≥80/amarelo≥60/laranja≥40/
  vermelho) + dica de comida (`scores.PONTUACOES[*]["dica"]`) + expander com gráfico
  Altair da progressão de 7 dias por pontuação.

## Convenções e armadilhas

- UI e código (nomes, docstrings, comentários) em PT-PT.
- Fluxo de registo: escolher alimento (comum ou OFF) → porção → cesto em `session_state`
  (itens com `nome`, `gramas`, `por_100g`, `nutrientes`) → `db.guardar_refeicao(nome,
  totais, itens=...)`. O utilizador nunca digita calorias.
- A coluna `refeicoes.itens` (JSON, adicionada por migração em `db.inicializar`) guarda
  os alimentos individuais — é o que permite editar gramas no Histórico
  (`historico._editor_refeicao` + `db.atualizar_refeicao`). Refeições antigas sem itens
  editam-se pelos totais.
- `views/components.py`: `tabela_cobertura` (dataframe com ProgressColumn, alfabético,
  ✅/🟡/🔴 e ⚠️ para limites) usada no Painel e no cesto; `lista_nutrientes` (markdown
  por alimento com % do dia).
- Listas de nutrientes apresentadas ao utilizador devem ser SEMPRE alfabéticas — usar
  `nutrients.ordenar()`/`nutrients.normalizar()` (pedido explícito do Benjamim; cuidado
  com duplicados tipo fibra que está em `DDR` E nos alvos do perfil — usar
  `dict.fromkeys` para deduplicar).
- Carências: `_sugestoes()` pontua alimentos da tabela local por quanto repõem dos gaps
  (porção típica vs falta diária) e monta uma "ideia de refeição" com 3 categorias.
- As chaves de nutrientes têm a unidade no nome (`proteina_g`, `sodio_mg`, `vit_d_ug`) e
  têm de coincidir entre `nutrients.CAMPOS_NUTRIENTES` (canónico), `foods.py`,
  `openfoodfacts._MAPA`, `nutrients.DDR/LIMITES/CARENCIAS` e `scores.PONTUACOES`.
- `agua_ml` nas refeições = água contida na comida; a água bebida regista-se na tabela
  `agua` e soma-se em `db.totais_do_dia`.
- Valores de `foods.py` e OFF são aproximados; micros em falta ficam 0 (= não é fonte).
- Testar páginas: `streamlit.testing.v1.AppTest` não suporta `switch_page` com páginas-função;
  usar um wrapper que chama `views.<página>.mostrar()` diretamente (ver histórico de sessões).
