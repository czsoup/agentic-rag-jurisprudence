"""Observabilité : métriques réelles des runs, par mode, et relecture d'une trace."""

import pandas as pd
import streamlit as st

from jurirag_ui import api, theme


def render() -> None:
    theme.masthead(
        "Suivi · Observabilité",
        "Registre des exécutions",
        "Appels LLM, outils, itérations, tokens et latences mesurés sur chaque run. "
        "Le coût monétaire est sans objet : le modèle tourne en local.",
    )
    try:
        metrics = api.metrics()
        runs = api.runs()
    except api.ApiError as exc:
        st.error(str(exc))
        return
    if not runs:
        theme.empty("Aucun run enregistré pour l'instant.")
        return

    st.markdown("<div class='zone-label'>Moyennes par mode</div>", unsafe_allow_html=True)
    rows = []
    for mode, agg in metrics["by_mode"].items():
        rows.append(
            {
                "mode": mode,
                "runs": agg["runs"],
                "appels LLM": agg["avg_llm_calls"],
                "appels d'outils": agg["avg_tool_calls"],
                "itérations": agg["avg_iterations"],
                "tokens": agg["avg_tokens"],
                "latence (s)": round(agg["avg_latency_ms"] / 1000, 1),
                "vérification": ", ".join(f"{k} {v}" for k, v in agg["status"].items()),
                "arrêts": ", ".join(f"{k} {v}" for k, v in agg["stop"].items()),
            }
        )
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    st.markdown("<div class='zone-label'>Runs</div>", unsafe_allow_html=True)
    table = []
    for run in runs:
        m = run.get("metrics") or {}
        table.append(
            {
                "run": run["run_id"],
                "début": run["started_at"][:19].replace("T", " "),
                "mode": run["mode"],
                "question": run["question"][:90],
                "LLM": m.get("llm_calls"),
                "outils": sum((m.get("tool_calls") or {}).values()) if m else None,
                "recherches": m.get("searches"),
                "itérations": m.get("iterations"),
                "latence (s)": round((m.get("total_latency_ms") or 0) / 1000, 1) if m else None,
                "vérification": m.get("verifier_status"),
                "arrêt": m.get("stop_reason")
                or ("en attente" if not run.get("finished_at") else None),
                "erreurs": len(m.get("errors") or []),
            }
        )
    frame = pd.DataFrame(table)
    st.dataframe(frame, hide_index=True, width="stretch")
    run_id = st.selectbox(
        "Relire la trace d'un run",
        frame["run"].tolist(),
        format_func=lambda r: f"{r} — {frame.set_index('run').loc[r, 'question']}",
    )
    if run_id:
        detail = api.run(run_id)
        if detail.get("metrics"):
            st.markdown(theme.figures_html(detail["metrics"]), unsafe_allow_html=True)
            if detail["metrics"].get("errors"):
                st.warning("Erreurs : " + " · ".join(detail["metrics"]["errors"]))
        st.markdown(theme.trace_html(detail["events"]), unsafe_allow_html=True)
