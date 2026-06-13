# 🚀 Pôr o NutriDia online (para o teu amigo usar com conta própria)

Guia simples, do início ao fim. Resultado final: um link `https://...streamlit.app`
onde cada pessoa cria a sua conta e vê só o seu diário, com os dados a persistir.

São 3 etapas: **GitHub** → **Base de dados (Postgres grátis)** → **Streamlit Cloud**.

---

## Etapa 1 — Pôr o código no GitHub

1. Cria conta em [github.com](https://github.com) (se ainda não tens).
2. Cria um repositório novo: botão **New** → nome `nutridia` → escolhe **Private**
   (privado; ninguém vê o código a não ser que convides) → **Create repository**.
3. No teu PC, na pasta `nutri-app`, o repositório local já está pronto (já fiz `git init`
   e o primeiro commit). Só precisas de o ligar ao GitHub e enviar — copia os comandos
   que o GitHub te mostra na secção *"…or push an existing repository"*, algo como:

   ```
   git remote add origin https://github.com/O-TEU-NOME/nutridia.git
   git branch -M main
   git push -u origin main
   ```

   > Os teus **dados pessoais e segredos não vão** para o GitHub (estão no `.gitignore`).

---

## Etapa 2 — Base de dados gratuita (para os dados não se apagarem)

Sem isto, o site funciona na mesma, mas os dados desaparecem quando ele reinicia.
Com isto, ficam permanentes. Usamos o **Supabase** (grátis):

1. Cria conta em [supabase.com](https://supabase.com) → **New project**.
2. Dá um nome, define uma **Database Password** (guarda-a) e cria.
3. Quando o projeto abrir: **Project Settings** (engrenagem) → **Database** →
   secção **Connection string** → separador **URI**. Copia o texto, parecido com:

   ```
   postgresql://postgres:[A-TUA-PASSWORD]@db.xxxx.supabase.co:5432/postgres
   ```

   Substitui `[A-TUA-PASSWORD]` pela password que definiste. Guarda esta linha
   para a Etapa 3.

---

## Etapa 3 — Publicar no Streamlit Cloud

1. Vai a [share.streamlit.io](https://share.streamlit.io) → entra com o GitHub.
2. **New app** → escolhe o repositório `nutridia`, branch `main`, ficheiro `app.py` → **Deploy**.
3. Espera 1-2 minutos. O site abre — mas falta ligar a base de dados.
4. Canto inferior direito → **Manage app** → **⋮** → **Settings** → **Secrets**.
   Cola lá esta linha (com a tua connection string da Etapa 2):

   ```
   database_url = "postgresql://postgres:A-TUA-PASSWORD@db.xxxx.supabase.co:5432/postgres"
   ```

   Guarda. O site reinicia sozinho.
5. Pronto! Agora o site **pede início de sessão**. Abre o link, cria a tua conta,
   e envia o link ao teu amigo para ele criar a dele. 🎉

---

## Atualizar o site mais tarde

Sempre que mudarmos algo, é só enviar para o GitHub e o Streamlit atualiza sozinho:

```
git add -A
git commit -m "descrição da mudança"
git push
```

---

## Notas de segurança

- ✅ Cada utilizador só vê o seu diário; palavras-passe guardadas encriptadas (hash PBKDF2).
- ✅ O Streamlit Cloud serve em HTTPS (ligação encriptada).
- ✅ Código no GitHub **privado**; dados e segredos fora do repositório.
- ℹ️ A tua app **local** (no PC) continua separada e sem login — são dois diários
  distintos (o local e o online).
