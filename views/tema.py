"""Tema visual da app — CSS e cabeçalho com estilo de comida saudável."""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

:root{
  --nd-green:#2E7D4F; --nd-green2:#5BA150; --nd-lime:#A8C66C;
  --nd-bg1:#EAF0DF; --nd-bg2:#E0E8D1; --nd-card:#FBFCF6;
  --nd-orange:#E8743B; --nd-text:#233021;
}
html, body, [data-testid="stAppViewContainer"], .stMarkdown,
p, span, div, label, input, button, h1, h2, h3, h4, h5{
  font-family:'Nunito',-apple-system,BlinkMacSystemFont,sans-serif;
}
[data-testid="stAppViewContainer"]{
  background:linear-gradient(180deg, var(--nd-bg1) 0%, var(--nd-bg2) 100%);
  background-attachment:fixed;
}
[data-testid="stHeader"]{ background:transparent; }
.block-container{ padding-top:2.2rem; }

/* Cabeçalho hero */
.nd-hero{
  display:flex; align-items:center; gap:18px;
  background:linear-gradient(120deg,#2E7D4F 0%, #5BA150 58%, #A8C66C 100%);
  color:#fff; padding:20px 26px; border-radius:20px; margin-bottom:20px;
  box-shadow:0 10px 26px rgba(46,125,79,.28);
}
.nd-hero .emoji{ font-size:44px; line-height:1; filter:drop-shadow(0 2px 4px rgba(0,0,0,.25)); }
.nd-hero h1{ margin:0; font-size:29px; font-weight:800; color:#fff; line-height:1.1; }
.nd-hero p{ margin:3px 0 0; font-size:14.5px; opacity:.93; color:#fff; font-weight:600; }

/* Cartões de métrica */
[data-testid="stMetric"]{
  background:var(--nd-card); border-radius:16px; padding:14px 16px;
  box-shadow:0 2px 10px rgba(36,48,36,.07); border-left:5px solid var(--nd-green2);
}
[data-testid="stMetricValue"]{ font-weight:800; color:var(--nd-green); }
[data-testid="stMetricLabel"] p{ font-weight:700; }

/* Botões */
.stButton>button{
  border-radius:12px; font-weight:700; border:1.5px solid var(--nd-green2);
  transition:transform .12s ease, box-shadow .12s ease;
}
.stButton>button:hover{ transform:translateY(-1px); box-shadow:0 4px 12px rgba(46,125,79,.18); }
.stButton>button[kind="primary"]{ background:var(--nd-green); border-color:var(--nd-green); }
.stButton>button[kind="primary"]:hover{ background:#256b43; }

/* Barras de progresso */
[data-testid="stProgress"] > div > div > div > div{
  background:linear-gradient(90deg,var(--nd-green2),var(--nd-lime));
}

/* Expanders */
[data-testid="stExpander"]{
  border:1px solid #DBE4CC; border-radius:14px; overflow:hidden; background:var(--nd-card);
  box-shadow:0 1px 6px rgba(36,48,36,.04);
}
[data-testid="stExpander"] summary{ font-weight:700; }

/* Separadores (tabs) */
.stTabs [data-baseweb="tab-list"]{ gap:6px; }
.stTabs [data-baseweb="tab"]{ border-radius:11px 11px 0 0; font-weight:700; padding:6px 14px; }
.stTabs [aria-selected="true"]{ background:#EAF2E1; color:var(--nd-green); }

/* Barra lateral */
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#FFFFFF 0%, #EEF4E5 100%);
  border-right:1px solid #E3EAD9;
}
.nd-brand{
  font-size:23px; font-weight:800; padding:6px 6px 0; display:flex;
  align-items:center; gap:9px; color:var(--nd-green);
}
.nd-tag{ font-size:12.5px; color:#6b7a5e; padding:2px 8px 12px; font-weight:600; }

/* Tabelas */
[data-testid="stDataFrame"], [data-testid="stTable"]{
  border-radius:14px; overflow:hidden; border:1px solid #E3EAD9;
}

/* Popover / containers brancos */
[data-testid="stPopover"]{ border-radius:12px; }
</style>
"""


def aplicar() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def cabecalho(emoji: str, titulo: str, subtitulo: str = "") -> None:
    sub = f"<p>{subtitulo}</p>" if subtitulo else ""
    st.markdown(
        f'<div class="nd-hero"><div class="emoji">{emoji}</div>'
        f'<div><h1>{titulo}</h1>{sub}</div></div>',
        unsafe_allow_html=True,
    )
