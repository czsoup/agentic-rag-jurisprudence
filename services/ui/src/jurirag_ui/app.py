"""Point d'entrée de l'interface : `streamlit run services/ui/src/jurirag_ui/app.py`."""

import uuid

import streamlit as st

from jurirag_ui import api, nav, theme

st.set_page_config(page_title="JuriRAG · Greffe", layout="wide", initial_sidebar_state="expanded")
theme.inject_css()

state = st.session_state
state.setdefault("session_id", uuid.uuid4().hex[:16])  # identifiant aléatoire, rien de personnel
state.setdefault("selected_case", None)

with st.sidebar:
    st.markdown("### JuriRAG")
    st.caption(
        "Recherche agentique en jurisprudence — Cour de cassation, corpus local, modèle local."
    )
    try:
        health = api.health()
        ok = health["status"] == "ok"
        st.markdown(
            theme.stamp("sufficient" if ok else "contradictory").replace(
                theme.STATUS_LABELS["sufficient" if ok else "contradictory"],
                "Système prêt" if ok else "Système dégradé",
            ),
            unsafe_allow_html=True,
        )
        st.caption(
            f"Génération : `{health['generation_model']}`  \nEmbeddings : `{health['embedding_model']}`"
        )
        for problem in health["problems"]:
            st.warning(problem)
    except api.ApiError as exc:
        st.error(str(exc))
    st.divider()
    st.caption(f"Session `{state.session_id}`")
    if state.selected_case:
        st.caption(f"Affaire sélectionnée :  \n**{state.selected_case['title']}**")
        if st.button("Désélectionner", width="stretch"):
            state.selected_case = None
            st.rerun()

st.navigation(nav.PAGES).run()
