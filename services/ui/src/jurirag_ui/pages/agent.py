"""Agentic RAG : question → trace en direct → réponse vérifiée, mémoire, validation humaine."""

import time
from collections.abc import Iterator
from typing import Any

import streamlit as st

from jurirag_ui import api, theme

MODES = {"Agent unique": "single", "Multi-agents (superviseur · chercheur · vérificateur)": "multi"}
KIND_LABELS = {
    "extend_budget": "Prolonger le budget d'itérations",
    "publish_contradictory": "Diffuser une réponse contredite par ses sources",
}


def _consume(stream: Iterator[dict[str, Any]], trace_ph: Any, status_ph: Any) -> None:
    """Affiche chaque événement dès sa réception : la trace se construit pendant le run."""
    state = st.session_state
    try:
        for item in stream:
            if item["type"] == "run":
                if item["status"] == "started":
                    state.agent_events = []
                    state.agent_final = None
                    state.agent_run_id = item["run_id"]
                status_ph.caption(f"Run `{item['run_id']}` — {item['status']}")
            elif item["type"] == "event":
                event = item["event"]
                state.agent_events.append(event)
                trace_ph.markdown(theme.trace_html(state.agent_events), unsafe_allow_html=True)
                status_ph.caption(
                    f"Étape {event['step']} · {event['type']} · {event['summary'][:140]}"
                )
            elif item["type"] == "status":
                state.agent_status = item
                state.agent_metrics = item.get("metrics")
                if item["status"] == "done":
                    state.agent_final = item["final"]
                    state.agent_pending = None
                elif item["status"] == "awaiting_approval":
                    state.agent_pending = {**item["approval"], "timeout_s": item["timeout_s"]}
                elif item["status"] == "error":
                    st.error(item.get("error"))
    except api.ApiError as exc:
        st.error(str(exc))


def _approval_panel(trace_ph: Any, status_ph: Any) -> None:
    pending = st.session_state.get("agent_pending")
    if not pending:
        return
    remaining = int(pending["requested_at"] + pending["timeout_s"] - time.time())
    with st.container(border=True):
        st.markdown(
            "<div class='zone-label'>Validation humaine requise · "
            f"{theme.esc(KIND_LABELS.get(pending['kind'], pending['kind']))}</div>",
            unsafe_allow_html=True,
        )
        st.markdown(f"**{pending['question']}**")
        details = pending.get("details") or {}
        for claim in details.get("unverified_claims") or []:
            st.markdown(f"- {claim}")
        if remaining > 0:
            st.caption(
                "L'agent est à l'arrêt tant que vous n'avez pas répondu. Expiration dans "
                f"{remaining // 60} min {remaining % 60:02d} s — sans réponse, l'action est annulée."
            )
        else:
            st.caption(
                "Délai dépassé : toute réponse sera enregistrée comme une expiration (action annulée)."
            )
        c1, c2 = st.columns(2)
        decision = None
        if c1.button("Confirmer", type="primary", width="stretch"):
            decision = "approve"
        if c2.button("Refuser", width="stretch"):
            decision = "reject"
    if decision:
        st.session_state.agent_pending = None
        _consume(api.resume(st.session_state.session_id, decision), trace_ph, status_ph)
        st.rerun()


def _answer_panel() -> None:
    final = st.session_state.get("agent_final")
    if not final:
        theme.empty("La réponse vérifiée, ses citations et ses limites apparaîtront ici.")
        return
    status = final.get("verifier_status")
    label = {
        "answered": "Réponse",
        "partial": "Réponse partielle",
        "abstained": "Abstention",
        "error": "Erreur",
    }[final["status"]]
    st.markdown(
        f"<div class='zone-label'>{label} · arrêt : {theme.esc(final['stop_reason'])}</div>{theme.stamp(status)}",
        unsafe_allow_html=True,
    )
    known = {s["alias"] for s in final["sources"]}
    st.markdown(theme.answer_html(final["answer"], known), unsafe_allow_html=True)
    if final.get("limits"):
        st.markdown(
            "<div class='limits'>" + "<br>".join(theme.esc(x) for x in final["limits"]) + "</div>",
            unsafe_allow_html=True,
        )
    if final["sources"]:
        st.markdown("<div class='zone-label'>Passages cités</div>", unsafe_allow_html=True)
        for s in final["sources"]:
            st.markdown(
                theme.passage_html(
                    s["alias"], s["title"], s["zone_label"], s["text"], s["passage_id"], s["origin"]
                ),
                unsafe_allow_html=True,
            )
    elif final.get("cases_consulted"):
        st.markdown(
            "<div class='zone-label'>Décisions consultées sans preuve suffisante</div>"
            + "<br>".join(theme.esc(c) for c in final["cases_consulted"]),
            unsafe_allow_html=True,
        )
    if final["status"] in ("answered", "partial"):
        _export()


def _export() -> None:
    run_id = st.session_state.get("agent_run_id")
    pending = st.session_state.get("export_pending")
    if not pending:
        if st.button("Exporter le dossier…"):
            try:
                st.session_state.export_pending = api.request_export(run_id)
                st.rerun()
            except api.ApiError as exc:
                st.error(str(exc))
        return
    with st.container(border=True):
        st.markdown(
            f"<div class='zone-label'>Validation humaine requise · export</div>**{pending['question']}**",
            unsafe_allow_html=True,
        )
        st.caption("Rien n'est écrit tant que vous n'avez pas confirmé.")
        c1, c2 = st.columns(2)
        decision = (
            "approve"
            if c1.button("Confirmer l'export", type="primary")
            else "reject"
            if c2.button("Annuler")
            else None
        )
    if decision:
        try:
            result = api.decide(pending["approval_id"], decision)
            st.session_state.export_result = result
        except api.ApiError as exc:
            st.error(str(exc))
        st.session_state.export_pending = None
        st.rerun()
    result = st.session_state.get("export_result")
    if result and result.get("status") == "exported":
        st.success(f"Dossier exporté : {result['path']}")
        st.download_button(
            "Télécharger le dossier (.md)",
            result["content"],
            file_name=result["path"].split("/")[-1],
        )


def _memory_panel() -> None:
    try:
        session = api.session(st.session_state.session_id)
    except api.ApiError:
        return
    turns = session["memory"]
    body = f"<b>Affaire en mémoire</b> : <span class='mono'>{theme.esc(session['case_id'] or '—')}</span><br>"
    body += (
        f"<b>Échanges retenus</b> : {len(turns)} (durée de vie {int(session['ttl_s'] // 60)} min)"
    )
    for turn in turns:
        body += f"<br>· {theme.esc(turn['question'][:90])}"
    st.markdown(f"<div class='memory'>{body}</div>", unsafe_allow_html=True)
    if st.button("Réinitialiser la session", help="Efface la mémoire et l'affaire retenue"):
        api.reset_session(st.session_state.session_id)
        for key in ("agent_events", "agent_final", "agent_pending", "agent_metrics"):
            st.session_state.pop(key, None)
        st.rerun()


def render() -> None:
    theme.masthead(
        "Agentic RAG",
        "Agent de recherche",
        "L'agent décide quand chercher, quelle décision lire, puis soumet sa réponse au vérificateur. "
        "Seules les étapes réellement exécutées s'affichent.",
    )
    state = st.session_state
    selected = state.get("selected_case")
    left, right = st.columns([1.25, 1], gap="large")
    with right:
        st.markdown("<div class='zone-label'>Registre d'exécution</div>", unsafe_allow_html=True)
        status_ph = st.empty()
        trace_ph = st.empty()
        trace_ph.markdown(theme.trace_html(state.get("agent_events") or []), unsafe_allow_html=True)
        if state.get("agent_metrics"):
            st.markdown(theme.figures_html(state.agent_metrics), unsafe_allow_html=True)
        st.markdown("<div class='zone-label'>Mémoire de session</div>", unsafe_allow_html=True)
        _memory_panel()

    with left:
        with st.form("ask_form", border=False):
            question = st.text_area(
                "Question",
                value=state.pop("agent_prefill", ""),
                placeholder="ex. Un abandon de poste peut-il justifier un licenciement pour faute grave ?",
                height=90,
            )
            c1, c2 = st.columns([1.6, 0.8])
            mode = c1.radio("Mode", list(MODES), horizontal=True, label_visibility="collapsed")
            submitted = c2.form_submit_button("Lancer l'agent", type="primary", width="stretch")
        if selected:
            st.caption(f"Affaire sélectionnée transmise à l'agent : {selected['title']}")
        if submitted and question.strip():
            state.export_pending = state.export_result = None
            _consume(
                api.run_agent(
                    state.session_id,
                    question.strip(),
                    MODES[mode],
                    selected["case_id"] if selected else None,
                ),
                trace_ph,
                status_ph,
            )
            st.rerun()
        _approval_panel(trace_ph, status_ph)
        _answer_panel()
