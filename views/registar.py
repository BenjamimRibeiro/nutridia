"""Registar refeição — alimentos comuns/próprios ou pesquisa OFF, favoritos e
repetição de refeições. Tu só dizes o quê e quanto; a app calcula os nutrientes."""
from datetime import datetime

import streamlit as st

from core import calc, db, momentos, nutrients
from views import builder, components, tema


def _carregar(cesto: list, itens: list) -> None:
    """Substitui o cesto pelos itens de um favorito/refeição (cópia)."""
    cesto.clear()
    cesto.extend(dict(i) for i in itens)


def mostrar():
    tema.cabecalho("🍽️", "Registar refeição",
                   "Escolhe os alimentos e a porção — a app trata das calorias e nutrientes")

    uid = st.session_state.get("uid")
    cesto = st.session_state.setdefault("cesto", [])
    pais = db.obter_definicao("off_pais", "pt")
    perfil = db.obter_perfil(uid)
    alvos = calc.alvos_diarios(perfil) if perfil else None
    sexo = perfil["sexo"] if perfil else None

    # ---- Atalhos: favoritos e repetir ----
    favoritos = db.listar_favoritos(uid)
    dias = db.dias_com_registos(uid, 14)
    if favoritos or dias:
        with st.expander("⚡ Favoritos e repetir refeições", expanded=not cesto):
            if favoritos:
                st.markdown("**Os teus favoritos** (carrega para o cesto):")
                cols = st.columns(3)
                for k, fav in enumerate(favoritos):
                    with cols[k % 3]:
                        if st.button(f"⭐ {fav['nome']}", key=f"fav_{fav['id']}",
                                     use_container_width=True):
                            _carregar(cesto, fav["itens"])
                            st.rerun()
                        if st.button("🗑️", key=f"favdel_{fav['id']}", help="Apagar favorito"):
                            db.apagar_favorito(fav["id"])
                            st.rerun()
            if dias:
                st.markdown("**Copiar uma refeição de outro dia:**")
                dia_sel = st.selectbox("Dia", dias, format_func=lambda d:
                                       datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y"),
                                       key="copiar_dia")
                refs = [r for r in db.refeicoes_do_dia(uid, dia_sel) if r.get("itens")]
                if refs:
                    idx = st.selectbox("Refeição", range(len(refs)),
                                       format_func=lambda i: f"{refs[i]['hora']} — {refs[i]['nome']}",
                                       key="copiar_ref")
                    if st.button("📋 Copiar para o cesto"):
                        _carregar(cesto, refs[idx]["itens"])
                        st.rerun()
                else:
                    st.caption("Esse dia não tem refeições com lista de alimentos para copiar.")

    st.subheader("1️⃣ Adicionar alimentos")
    builder.adicionar_alimento(cesto, "reg", pais, uid)

    st.divider()
    st.subheader("2️⃣ A tua refeição")
    if not cesto:
        st.caption("Ainda não adicionaste nada. Usa os atalhos ou os separadores acima. 👆")
        return

    st.markdown("**Cada alimento dá-te** (clica em 🔍 para o detalhe completo):")
    builder.mostrar_itens(cesto, "reg", sexo, alvos)
    totais = builder.totais(cesto)

    st.markdown(f"### Total da refeição: {totais['kcal']:.0f} kcal")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Proteína", f"{totais['proteina_g']:.0f} g")
    c2.metric("Hidratos", f"{totais['hidratos_g']:.0f} g")
    c3.metric("Gordura", f"{totais['gordura_g']:.0f} g")
    c4.metric("Fibra", f"{totais['fibra_g']:.0f} g")

    st.markdown("**O que esta refeição te dá no geral:**")
    if perfil:
        components.tabela_cobertura(totais, sexo, alvos, apenas_consumidos=True)
    else:
        st.markdown(components.lista_nutrientes(totais))
        st.caption("Preenche o Perfil para veres a % dos teus alvos diários.")

    nome_sugerido = ", ".join(i["nome"].split(" — ")[0] for i in cesto[:3])
    cn, cm = st.columns([2, 1])
    nome = cn.text_input("Nome da refeição", nome_sugerido)
    momento = cm.selectbox("Momento do dia", momentos.MOMENTOS,
                           index=momentos.MOMENTOS.index(momentos.sugerir()))

    foto_bytes = None
    with st.expander("📷 Adicionar foto (opcional)"):
        foto = st.file_uploader("Foto da refeição", type=["jpg", "jpeg", "png", "webp"],
                                key="reg_foto", label_visibility="collapsed")
        if foto:
            foto_bytes = foto.getvalue()
            st.image(foto_bytes, width=220)

    c1, c2 = st.columns(2)
    if c1.button("💾 Guardar refeição", type="primary", use_container_width=True):
        db.guardar_refeicao(uid, nome.strip() or "Refeição", totais, itens=list(cesto),
                            momento=momento, foto_bytes=foto_bytes)
        st.session_state["cesto"] = []
        st.session_state.pop("reg_res", None)
        st.session_state.pop("reg_foto", None)
        st.success(f"✅ «{nome}» guardada! Vê o impacto no Painel.")
        st.balloons()
        st.rerun()
    if c2.button("⭐ Guardar como favorito", use_container_width=True,
                 help="Guarda esta combinação para repetir com 1 clique"):
        db.guardar_favorito(uid, nome.strip() or "Favorito", list(cesto))
        st.success(f"⭐ «{nome}» guardado nos favoritos!")
