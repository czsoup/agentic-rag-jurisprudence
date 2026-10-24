"""Agentic RAG en conversation : questions successives, graphe de la boucle en direct,
récapitulatif du parcours, réponse vérifiée, mémoire de session et validation humaine.

Un run se déroule en deux passages : la soumission ajoute le tour à la conversation et
relance la page ; le passage suivant affiche la bulle du tour, puis consomme le flux
NDJSON en mettant à jour le graphe, le registre et le parcours à chaque événement.
"""

import time
from collections.abc import Iterator
from typing import Any

import streamlit as st

from jurirag_ui import api, livegraph, theme

MODES = {"Agent unique": "single", "Multi-agents (superviseur · chercheur · vérificateur)": "multi"}
MODE_LABELS = {"single": "agent unique", "multi": "multi-agents"}
KIND_LABELS = {
    "extend_budget": "Prolonger le budget d'itérations",
    "publish_contradictory": "Diffuser une réponse contredite par ses sources",
}
FINAL_LABELS = {
    "answered": "Réponse",
    "partial": "Réponse partielle",
    "abstained": "Abstention",
    "error": "Erreur",
}


class Live:
    """Emplacements mis à jour pendant le run : graphe, statut, registre, parcours."""

    def __init__(self, graph: Any, status: Any, trace: Any, path: Any = None) -> None:
        self.graph, self.status, self.trace, self.path = graph, status, trace, path

    def draw(self, turn: dict[str, Any]) -> None:
        events, phase = turn["events"], turn["phase"]
        self.graph.markdown(
            livegraph.graph_svg(turn["mode"], events, phase), unsafe_allow_html=True
        )
        self.trace.markdown(theme.trace_html(events), unsafe_allow_html=True)
        if self.path is not None:
            self.path.markdown(
                livegraph.path_html(events, live=phase == "running"), unsafe_allow_html=True
            )


def _consume(stream: Iterator[dict[str, Any]], turn: dict[str, Any], live: Live) -> None:
    """Affiche chaque événement dès sa réception : le graphe et la trace avancent avec le run."""
    try:
        for item in stream:
            if item["type"] == "run":
                if item["status"] == "started":
                    turn["run_id"] = item["run_id"]
                turn["phase"] = "running"
                live.status.caption(f"Run `{item['run_id']}` — {item['status']}")
            elif item["type"] == "event":
                event = item["event"]
                turn["events"].append(event)
                live.draw(turn)
                live.status.caption(
                    f"Étape {event['step']} · {event.get('node') or '—'} · {event['type']} · "
                    f"{event['summary'][:120]}"
                )
            elif item["type"] == "status":
                turn["metrics"] = item.get("metrics")
                if item["status"] == "done":
                    turn["final"], turn["phase"] = item["final"], "done"
                    st.session_state.agent_pending = None
                elif item["status"] == "awaiting_approval":
                    turn["phase"] = "awaiting"
                    st.session_state.agent_pending = {
                        **item["approval"],
                        "timeout_s": item["timeout_s"],
                    }
                elif item["status"] == "error":
                    turn["phase"], turn["error"] = "error", item.get("error")
    except api.ApiError as exc:
        turn["phase"], turn["error"] = "error", str(exc)


def _case_title(case_id: str | None) -> str | None:
    """Titre lisible d'une affaire déjà vue dans la conversation ou sélectionnée."""
    if not case_id:
        return None
    selected = st.session_state.get("selected_case")
    if selected and selected["case_id"] == case_id:
        return str(selected["title"])
    for turn in reversed(st.session_state.agent_history):
        for source in (turn.get("final") or {}).get("sources") or []:
            if source.get("case_id") == case_id:
                return str(source["title"])
    return None


def _memory_snapshot() -> dict[str, Any]:
    """Ce que la session retient au moment où la question part (affiché dans la bulle)."""
    try:
        session = api.session(st.session_state.session_id)
    except api.ApiError:
        return {"case_id": None, "case_title": None, "turns": 0}
    return {
        "case_id": session["case_id"],
        "case_title": _case_title(session["case_id"]),
        "turns": len(session["memory"]),
    }


def _question_bubble(turn: dict[str, Any]) -> None:
    with st.chat_message("user", avatar=":material/person:"):
        meta = [MODE_LABELS.get(turn["mode"], turn["mode"])]
        if turn.get("selected_title"):
            meta.append(f"affaire sélectionnée : {theme.esc(turn['selected_title'])}")
        memory = turn.get("memory") or {}
        if memory.get("turns") or memory.get("case_id"):
            case = memory.get("case_title") or memory.get("case_id")
            bits = [f"{memory['turns']} échange(s) retenu(s)"] if memory.get("turns") else []
            if case:
                bits.append(f"affaire en cours : {case}")
            meta.append(f"<span class='mem'>mémoire · {theme.esc(' · '.join(bits))}</span>")
        else:
            meta.append("sans mémoire : première question de la session")
        st.markdown(
            f"<div class='turn-q'>{theme.esc(turn['question'])}</div>"
            f"<div class='turn-meta'>{' · '.join(meta)}</div>",
            unsafe_allow_html=True,
        )


def _answer_block(final: dict[str, Any], prefix: str, compact: bool) -> None:
    st.markdown(
        f"<div class='zone-label'>{FINAL_LABELS[final['status']]} · arrêt : "
        f"{theme.esc(final['stop_reason'])}</div>{theme.stamp(final.get('verifier_status'))}",
        unsafe_allow_html=True,
    )
    known = {s["alias"] for s in final["sources"]}
    st.markdown(theme.answer_html(final["answer"], known, prefix), unsafe_allow_html=True)
    if final.get("limits"):
        st.markdown(
            "<div class='limits'>" + "<br>".join(theme.esc(x) for x in final["limits"]) + "</div>",
            unsafe_allow_html=True,
        )
    if final["sources"]:
        passages = "".join(
            theme.passage_html(
                s["alias"], s["title"], s["zone_label"], s["text"], s["passage_id"], s["origin"],
                prefix,
            )
            for s in final["sources"]
        )  # fmt: skip
        if compact:
            with st.expander(f"Passages cités ({len(final['sources'])})"):
                st.markdown(passages, unsafe_allow_html=True)
        else:
            st.markdown("<div class='zone-label'>Passages cités</div>", unsafe_allow_html=True)
            st.markdown(passages, unsafe_allow_html=True)
    elif final.get("cases_consulted"):
        st.markdown(
            "<div class='zone-label'>Décisions consultées sans preuve suffisante</div>"
            + "<br>".join(theme.esc(c) for c in final["cases_consulted"]),
            unsafe_allow_html=True,
        )


def _answer_bubble(turn: dict[str, Any], index: int, last: bool) -> Any:
    """Bulle de l'agent. Pour le tour en cours, renvoie l'emplacement du parcours en direct."""
    with st.chat_message("assistant", avatar=":material/gavel:"):
        path_ph = st.empty()
        path_ph.markdown(
            livegraph.path_html(turn["events"], live=turn["phase"] == "running"),
            unsafe_allow_html=True,
        )
        if turn["phase"] == "error":
            st.error(turn.get("error") or "Erreur inconnue.")
        elif turn["phase"] == "awaiting" and last:
            _approval_panel()
        elif turn["phase"] == "running" and not last:
            st.caption("Run interrompu avant sa fin.")
        if turn.get("final"):
            _answer_block(turn["final"], f"t{index}", compact=not last)
            if last and turn["final"]["status"] in ("answered", "partial"):
                _export(turn["run_id"])
    return path_ph


def _approval_panel() -> None:
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
        st.session_state.agent_resume = decision
        st.session_state.agent_history[-1]["phase"] = "running"
        st.rerun()


def _export(run_id: str) -> None:
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
            st.session_state.export_result = api.decide(pending["approval_id"], decision)
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
    case = _case_title(session["case_id"]) or session["case_id"] or "—"
    body = f"<b>Affaire en mémoire</b> : {theme.esc(case)}<br>"
    body += (
        f"<b>Échanges retenus</b> : {len(turns)} (durée de vie {int(session['ttl_s'] // 60)} min)"
    )
    for turn in turns:
        body += f"<br>· {theme.esc(turn['question'][:90])}"
    st.markdown(f"<div class='memory'>{body}</div>", unsafe_allow_html=True)
    if st.button(
        "Nouvelle conversation", help="Efface la mémoire, l'affaire retenue et l'historique"
    ):
        api.reset_session(st.session_state.session_id)
        for key in ("agent_history", "agent_pending", "agent_queued", "agent_resume"):
            st.session_state.pop(key, None)
        st.session_state.export_pending = st.session_state.export_result = None
        st.rerun()


def _ask_form() -> None:
    state = st.session_state
    selected = state.get("selected_case")
    busy = bool(state.get("agent_pending"))
    with st.form("ask_form", border=False, clear_on_submit=True):
        question = st.text_area(
            "Question" if not state.agent_history else "Question suivante",
            value=state.pop("agent_prefill", ""),
            placeholder="ex. Un abandon de poste peut-il justifier un licenciement pour faute grave ?"
            if not state.agent_history
            else "ex. Et quelle est la solution de cette affaire ?",
            height=90,
        )
        c1, c2 = st.columns([1.6, 0.8])
        mode = c1.radio("Mode", list(MODES), horizontal=True, label_visibility="collapsed")
        submitted = c2.form_submit_button(
            "Lancer l'agent", type="primary", width="stretch", disabled=busy
        )
    if busy:
        st.caption("Répondez d'abord à la validation humaine en attente.")
    elif selected:
        st.caption(f"Affaire sélectionnée transmise à l'agent : {selected['title']}")
    if submitted and question.strip():
        state.export_pending = state.export_result = None
        state.agent_history.append(
            {
                "question": question.strip(),
                "mode": MODES[mode],
                "selected_title": selected["title"] if selected else None,
                "memory": _memory_snapshot(),
                "events": [],
                "final": None,
                "metrics": None,
                "run_id": None,
                "phase": "running",
                "error": None,
            }
        )
        state.agent_queued = selected["case_id"] if selected else ""
        st.rerun()


def render() -> None:
    theme.masthead(
        "Agentic RAG",
        "Agent de recherche",
        "Posez vos questions à la suite : l'agent garde l'affaire en cours d'une question à "
        "l'autre. Il décide quand chercher, quelle décision lire, puis soumet sa réponse au "
        "vérificateur. Seules les étapes réellement exécutées s'affichent.",
    )
    state = st.session_state
    state.setdefault("agent_history", [])
    history: list[dict[str, Any]] = state.agent_history
    current = history[-1] if history else None
    left, right = st.columns([1.25, 1], gap="large")

    with right:
        st.markdown("<div class='zone-label'>Boucle en direct</div>", unsafe_allow_html=True)
        graph_ph = st.empty()
        mode = current["mode"] if current else "single"
        graph_ph.markdown(
            livegraph.graph_svg(mode, current["events"] if current else [], current["phase"] if current else "idle"),
            unsafe_allow_html=True,
        )  # fmt: skip
        st.markdown(
            "<div class='lg-legend'><b style='background:var(--oxblood);border-color:var(--oxblood)'></b>"
            "nœud en cours<b style='background:var(--paper-2)'></b>déjà parcouru"
            "<b style='background:var(--mark);border:2px dashed var(--ochre)'></b>attente humaine</div>",
            unsafe_allow_html=True,
        )
        status_ph = st.empty()
        st.markdown("<div class='zone-label'>Registre d'exécution</div>", unsafe_allow_html=True)
        with st.container(height=360, border=False):
            trace_ph = st.empty()
            trace_ph.markdown(
                theme.trace_html(current["events"] if current else []), unsafe_allow_html=True
            )
        if current and current.get("metrics"):
            st.markdown(theme.figures_html(current["metrics"]), unsafe_allow_html=True)
        st.markdown("<div class='zone-label'>Mémoire de session</div>", unsafe_allow_html=True)
        _memory_panel()

    with left:
        if not history:
            theme.empty(
                "La conversation commence ici. Chaque réponse affiche son parcours "
                "(chercher → lire → vérifier…), ses citations et ses limites."
            )
        path_ph = None
        for index, turn in enumerate(history):
            _question_bubble(turn)
            path_ph = _answer_bubble(turn, index, last=index == len(history) - 1)
        _ask_form()

    # Run en attente : lancé après la mise en page, pour que la bulle et le graphe s'animent.
    if current is not None and ("agent_queued" in state or "agent_resume" in state):
        live = Live(graph_ph, status_ph, trace_ph, path_ph)
        if "agent_resume" in state:
            stream = api.resume(state.session_id, state.pop("agent_resume"))
        else:
            case_id = state.pop("agent_queued") or None
            stream = api.run_agent(state.session_id, current["question"], current["mode"], case_id)
        _consume(stream, current, live)
        st.rerun()
