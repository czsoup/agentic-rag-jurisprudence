"""Pages de l'application (objets partagés pour la navigation entre pages)."""

import streamlit as st

from jurirag_ui.pages import agent, observability, search, system

SEARCH = st.Page(search.render, title="Recherche & lecture", url_path="recherche", default=True)
AGENT = st.Page(agent.render, title="Agent", url_path="agent")
OBSERVABILITY = st.Page(observability.render, title="Observabilité", url_path="observabilite")
SYSTEM = st.Page(system.render, title="Système", url_path="systeme")
PAGES = [SEARCH, AGENT, OBSERVABILITY, SYSTEM]
