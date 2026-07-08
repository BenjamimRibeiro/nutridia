"""Plano semanal — ementa de 7 dias gerada dos alimentos da tabela local,
à medida do perfil (calorias, alergias, preferências e condições de saúde)."""
import streamlit as st

from core import calc, db, foods, i18n, nutrients
from core import plano as plano_mod
from views import tema

_t = i18n.t


def mostrar():
    tema.cabecalho("📅", _t("Plano semanal", "Weekly plan"),
                   _t("Uma ementa de 7 dias à tua medida — troca-a até gostares",
                      "A 7-day menu made for you — reshuffle until you like it"))

    uid = st.session_state.get("uid")
    perfil = db.obter_perfil(uid)
    if not perfil:
        st.info(_t("Preenche primeiro o teu **Perfil** para gerar um plano à tua medida.",
                   "Fill in your **Profile** first to generate a plan made for you."))
        return

    alvos = calc.alvos_diarios(perfil)
    respeita = []
    if perfil.get("alergias"):
        respeita.append(_t("alergias", "allergies"))
    if perfil.get("restricoes"):
        respeita.append(_t("preferências", "preferences"))
    if perfil.get("condicoes"):
        respeita.append(_t("condições de saúde", "health conditions"))
    extra = (" · " + _t("Respeita as tuas ", "Respects your ") + ", ".join(respeita)
             if respeita else "")
    st.caption(_t(f"Alvo: **{alvos['kcal']} kcal/dia**. Porções da tabela local, ajustadas "
                  "ao teu alvo.", f"Target: **{alvos['kcal']} kcal/day**. Local-table portions, "
                  "adjusted to your target.") + extra)

    semente = st.session_state.setdefault("plano_semente", 0)
    c1, c2 = st.columns([1, 3])
    if c1.button(_t("🎲 Gerar outro plano", "🎲 Reshuffle plan"), type="primary"):
        st.session_state["plano_semente"] = semente + 1
        st.rerun()
    c2.caption(_t("O plano mantém-se igual até carregares no botão — podes voltar "
                  "a esta página sem o perder.",
                  "The plan stays the same until you press the button — you can come "
                  "back to this page without losing it."))

    plano = plano_mod.gerar(perfil, alvos, semente)
    linhas_txt = [_t("Plano semanal NutriDia", "NutriDia weekly plan"), "=" * 30]
    for d in plano:
        desvio = d["kcal"] / alvos["kcal"] if alvos["kcal"] else 0
        with st.expander(f"**{plano_mod.dia_nome(d['dia'])}** — {d['kcal']:.0f} kcal "
                         f"({desvio:.0%} {_t('do alvo', 'of target')})",
                         expanded=(d["dia"] == "Segunda")):
            linhas_txt.append(f"\n{plano_mod.dia_nome(d['dia'])} ({d['kcal']:.0f} kcal):")
            for r in d["refeicoes"]:
                if not r["itens"]:
                    continue
                itens_txt = ", ".join(f"{foods.nome(n)} ({g:.0f} g)"
                                      for n, _rot, g, _k in r["itens"])
                st.markdown(f"{r['emoji']} **{plano_mod.momento_nome(r['momento'])}** "
                            f"({r['kcal']:.0f} kcal): {itens_txt}")
                linhas_txt.append(f"  {r['emoji']} {plano_mod.momento_nome(r['momento'])}: "
                                  f"{itens_txt}")

    st.download_button(_t("⬇️ Descarregar plano (.txt)", "⬇️ Download plan (.txt)"),
                       "\n".join(linhas_txt), file_name="plano_semanal_nutridia.txt",
                       mime="text/plain")
    st.caption(_t("💡 Isto é um ponto de partida gerado da tabela local — troca alimentos a "
                  "gosto no dia a dia. ⚕️ Não substitui um plano de um nutricionista.",
                  "💡 This is a starting point generated from the local table — swap foods as "
                  "you like day to day. ⚕️ Not a substitute for a nutritionist's plan."))
