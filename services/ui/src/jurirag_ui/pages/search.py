"""Parcours RAG : recherche → sélection d'une affaire → lecture → résumé → question-réponse."""

from typing import Any

import streamlit as st

from jurirag_ui import api, theme

METHODS = {
    "Hybride (BM25 + dense, RRF)": "hybrid",
    "Lexical (BM25)": "bm25",
    "Sémantique (dense)": "dense",
}
ZONE_ORDER = ["introduction", "expose", "moyens", "motivations", "dispositif", "texte"]
SUMMARY_LABELS = {"faits": "Faits", "procedure": "Procédure", "decision": "Décision"}


def _select(result: dict[str, Any]) -> None:
    st.session_state.selected_case = {
        "case_id": result["meta"]["case_id"],
        "title": result["title"],
    }
    st.session_state.pop("summary", None)
    st.session_state.pop("static_answer", None)


def _results_column() -> None:
    with st.form("search_form", border=False):
        query = st.text_input(
            "Recherche",
            placeholder="ex. licenciement pour faute grave d'un salarié protégé",
            label_visibility="collapsed",
        )
        c1, c2, c3 = st.columns([1.6, 0.8, 0.7])
        method_label = c1.selectbox("Méthode", list(METHODS), label_visibility="collapsed")
        k = c2.number_input("Résultats", 3, 30, 10, label_visibility="collapsed")
        submitted = c3.form_submit_button("Chercher", width="stretch", type="primary")
    if submitted and query.strip():
        try:
            with st.spinner("Recherche dans l'index…"):
                st.session_state.search_results = api.search(query, int(k), METHODS[method_label])
        except api.ApiError as exc:
            st.error(str(exc))

    data = st.session_state.get("search_results")
    if not data:
        theme.empty(
            "Saisissez des mots-clés ou une question : les décisions les plus pertinentes s'affichent ici."
        )
        return
    results = data["results"]
    st.markdown(
        f'<span class="smallcaps">{len(results)} décision(s) · méthode {theme.esc(data["method"])}</span>',
        unsafe_allow_html=True,
    )
    if not results:
        theme.empty("Aucune décision ne correspond. Essayez d'autres termes juridiques.")
    for result in results:
        excerpt = result["passages"][0]["text"] if result["passages"] else ""
        st.markdown(
            theme.result_row(
                result["rank"],
                result["title"],
                result["meta"],
                " ".join(excerpt.split()),
                result["score"],
            ),
            unsafe_allow_html=True,
        )
        selected = (
            st.session_state.selected_case
            and st.session_state.selected_case["case_id"] == result["meta"]["case_id"]
        )
        st.button(
            "Affaire ouverte" if selected else "Consulter",
            key=f"open-{result['meta']['case_id']}",
            on_click=_select,
            args=(result,),
            disabled=bool(selected),
        )
    st.caption(data["note"])


def _metadata(meta: dict[str, Any]) -> None:
    rows = [
        ("Juridiction", meta.get("jurisdiction")),
        ("Chambre", meta.get("chamber")),
        ("Formation", meta.get("formation")),
        ("Date", meta.get("decision_date")),
        ("Pourvoi", meta.get("number")),
        ("ECLI", meta.get("ecli")),
        ("Solution", meta.get("solution")),
        ("Publication", ", ".join(meta.get("publication") or [])),
        ("Décision attaquée", meta.get("contested")),
    ]
    body = "".join(
        f"<tr><td class='smallcaps'>{theme.esc(k)}</td><td>{theme.esc(v)}</td></tr>"
        for k, v in rows
        if v
    )
    st.markdown(
        f"<table style='font-size:.86rem;border-collapse:collapse'>{body}</table>",
        unsafe_allow_html=True,
    )
    if meta.get("visa"):
        st.markdown(
            "<div class='zone-label'>Textes visés</div>"
            + "<br>".join(theme.esc(v) for v in meta["visa"]),
            unsafe_allow_html=True,
        )
    url = (meta.get("provenance") or {}).get("url")
    prov = meta.get("provenance") or {}
    st.caption(
        f"Provenance : {prov.get('dataset')} · split {prov.get('split')} · révision {str(prov.get('revision'))[:10]}"
        + (f" · [décision sur courdecassation.fr]({url})" if url else "")
    )


def _summary(case_id: str) -> None:
    if st.button("Résumer : faits, procédure, décision", type="primary"):
        try:
            with st.spinner("Résumé par le modèle local…"):
                st.session_state.summary = api.summarize(case_id)
        except api.ApiError as exc:
            st.error(str(exc))
    summary = st.session_state.get("summary")
    if not summary or summary["case_id"] != case_id:
        return
    known = {p["alias"] for p in summary["passages"]}
    for key, label in SUMMARY_LABELS.items():
        st.markdown(f"<div class='zone-label'>{label}</div>", unsafe_allow_html=True)
        st.markdown(
            theme.answer_html(summary["sections"][key], known, "sum"), unsafe_allow_html=True
        )
    if summary["missing_zones"]:
        st.warning("Zones absentes du zonage : " + ", ".join(summary["missing_zones"]))
    with st.expander(f"Passages utilisés ({len(summary['passages'])})"):
        for p in summary["passages"]:
            st.markdown(
                theme.passage_html(
                    p["alias"],
                    p["title"],
                    p["zone_label"],
                    p["text"],
                    p["passage_id"],
                    anchor_prefix="sum",
                ),
                unsafe_allow_html=True,
            )
    st.caption(
        f"{summary['latency_ms'] / 1000:.1f} s · température {summary['params']['temperature']}"
        f" · {summary['params']['model']}"
    )


def _qa(case_id: str) -> None:
    with st.form("qa_form", border=False):
        question = st.text_input(
            "Question sur cette affaire", placeholder="ex. Quel moyen la Cour accueille-t-elle ?"
        )
        c1, c2 = st.columns(2)
        static = c1.form_submit_button("Réponse directe (RAG statique)", width="stretch")
        agentic = c2.form_submit_button("Confier à l'agent", width="stretch", type="primary")
    if agentic and question.strip():
        from jurirag_ui import nav  # import tardif : nav importe cette page

        st.session_state.agent_prefill = question
        st.switch_page(nav.AGENT)
    if static and question.strip():
        try:
            with st.spinner("Recherche dans l'affaire puis réponse…"):
                st.session_state.static_answer = api.ask_static(question, case_id)
        except api.ApiError as exc:
            st.error(str(exc))
    result = st.session_state.get("static_answer")
    if not result:
        return
    known = {p["alias"] for p in result["passages"]}
    status = (result.get("verifier") or {}).get("status")
    st.markdown(theme.stamp(status), unsafe_allow_html=True)
    st.markdown(theme.answer_html(result["answer"], known, "qa"), unsafe_allow_html=True)
    unverified = (result.get("verifier") or {}).get("unverified_claims") or []
    if unverified:
        st.markdown(
            "<div class='limits'><b>Non établi par les passages :</b><br>"
            + "<br>".join(theme.esc(c) for c in unverified)
            + "</div>",
            unsafe_allow_html=True,
        )
    for p in result["passages"]:
        st.markdown(
            theme.passage_html(
                p["alias"],
                p["title"],
                p["zone_label"],
                p["text"],
                p["passage_id"],
                anchor_prefix="qa",
            ),
            unsafe_allow_html=True,
        )
    m = result["metrics"]
    st.caption(
        f"RAG statique : {m['llm_calls']} appel(s) LLM (dont vérification), 1 recherche, "
        f"{m['total_latency_ms'] / 1000:.1f} s — la vérification est mesurée mais ne "
        "déclenche aucune correction."
    )


def _reader() -> None:
    selected = st.session_state.selected_case
    if not selected:
        theme.empty(
            "Sélectionnez une décision dans la liste pour la lire, la résumer et l'interroger."
        )
        return
    try:
        case = api.get_case(selected["case_id"])
    except api.ApiError as exc:
        st.error(str(exc))
        return
    meta = case["meta"]
    st.markdown(
        f"<div class='kicker smallcaps'>{theme.esc(meta.get('decision_type') or 'Décision')}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(f"## {case['title']}")
    if meta.get("summary"):
        st.markdown(
            "<div class='limits' style='border-color:var(--oxblood)'><b>Sommaire officiel</b> — "
            f"{theme.esc(meta['summary'][:900])}</div>",
            unsafe_allow_html=True,
        )

    tab_text, tab_summary, tab_qa, tab_meta = st.tabs(
        ["Texte", "Résumé", "Questions", "Métadonnées"]
    )
    with tab_text:
        zones = sorted(
            case["zones"],
            key=lambda z: ZONE_ORDER.index(z["zone"]) if z["zone"] in ZONE_ORDER else 99,
        )
        labels = list(dict.fromkeys(z["label"] for z in zones))
        if not labels:
            theme.empty("Texte non zoné.")
        for label in labels:
            text = "\n\n".join(z["text"] for z in zones if z["label"] == label)
            with st.expander(label, expanded=label in ("Exposé du litige", "Dispositif")):
                st.markdown(
                    f"<div class='case-text'>{theme.esc(text)}</div>", unsafe_allow_html=True
                )
    with tab_summary:
        _summary(selected["case_id"])
    with tab_qa:
        _qa(selected["case_id"])
    with tab_meta:
        _metadata(meta)


def render() -> None:
    theme.masthead(
        "Recherche · RAG",
        "Recherche & lecture",
        "Retrouver des décisions de la Cour de cassation, les lire par zone, les résumer et les interroger. "
        "Les réponses ne s'appuient que sur les passages affichés.",
    )
    left, right = st.columns([0.95, 1.35], gap="large")
    with left:
        _results_column()
    with right:
        _reader()
