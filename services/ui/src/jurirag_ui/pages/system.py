"""État du système : Ollama, modèles, index, paramètres effectivement utilisés."""

import json

import streamlit as st

from jurirag_ui import api, theme


def render() -> None:
    theme.masthead(
        "Système",
        "Configuration & provenance",
        "Ce que l'API utilise réellement : serveur Ollama, modèles, index, paramètres de génération.",
    )
    try:
        health = api.health()
    except api.ApiError as exc:
        st.error(str(exc))
        return
    checks = health["checks"]
    labels = {
        "ollama": "Ollama joignable",
        "generation_model": f"Modèle {health['generation_model']}",
        "embedding_model": f"Embeddings {health['embedding_model']}",
        "index": "Index construit",
    }
    st.markdown(
        " ".join(
            theme.stamp("sufficient" if ok else "insufficient").replace(
                theme.STATUS_LABELS["sufficient" if ok else "insufficient"], labels[k]
            )
            for k, ok in checks.items()
        ),
        unsafe_allow_html=True,
    )
    for problem in health["problems"]:
        st.warning(problem)

    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("<div class='zone-label'>Agent et génération</div>", unsafe_allow_html=True)
        st.code(json.dumps(health["agent"], ensure_ascii=False, indent=2), language="json")
        st.markdown(
            "<div class='zone-label'>Modèles installés sur Ollama</div>", unsafe_allow_html=True
        )
        st.write(", ".join(health["ollama"]["models"]) or "—")
    with right:
        st.markdown(
            "<div class='zone-label'>Manifeste de l'index (provenance)</div>",
            unsafe_allow_html=True,
        )
        if health["index"]:
            st.code(json.dumps(health["index"], ensure_ascii=False, indent=2), language="json")
        else:
            theme.empty("Index absent : lancer `make index`.")
