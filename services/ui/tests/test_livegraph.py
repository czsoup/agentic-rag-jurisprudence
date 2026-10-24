"""Graphe en direct et récapitulatif du parcours, à partir d'événements de trace construits."""

from typing import Any

from jurirag_ui import livegraph


def ev(type_: str, node: str, **data: Any) -> dict[str, Any]:
    return {"type": type_, "node": node, "data": data, "step": 0, "summary": "", "agent": "agent"}


# Scénario 2 typique : chercher, lire, réponse refusée, nouvelle réponse vérifiée.
RUN = [
    ev("DECISION", "decide"),
    ev("TOOL", "act", name="search_cases"),
    ev("OBSERVATION", "act"),
    ev("DECISION", "decide"),
    ev("TOOL", "act", name="read_case"),
    ev("OBSERVATION", "act"),
    ev("DECISION", "decide"),
    ev("CHECK", "verify", status="insufficient"),
    ev("DECISION", "decide"),
    ev("CHECK", "verify", status="sufficient"),
    ev("FINAL", "finalize", status="answered"),
]


def test_visits_follow_the_nodes_without_consecutive_repeats() -> None:
    assert livegraph.visits(RUN) == [
        "start", "decide", "act", "decide", "act", "decide", "verify", "decide", "verify",
        "finalize",
    ]  # fmt: skip


def test_path_recap_reads_like_the_run() -> None:
    labels = [label for label, _ in livegraph.path_steps(RUN)]
    assert labels == ["chercher", "lire", "vérifier ✗", "vérifier ✓", "répondre"]
    css = dict(livegraph.path_steps(RUN))
    assert css["vérifier ✗"] == "bad" and css["vérifier ✓"] == "ok"


def test_identical_consecutive_steps_are_merged() -> None:
    events = [ev("TOOL", "act", name="search_cases") for _ in range(3)]
    events.append(ev("FINAL", "abstain", status="abstained"))
    assert [label for label, _ in livegraph.path_steps(events)] == ["chercher ×3", "s'abstenir"]


def test_human_validation_appears_in_the_recap() -> None:
    events = [
        ev("HUMAN", "budget_gate", kind="extend_budget"),
        ev("HUMAN", "human_gate", decision="reject"),
    ]
    assert [label for label, _ in livegraph.path_steps(events)] == [
        "validation humaine",
        "humain : non",
    ]


def test_running_graph_highlights_the_current_node_and_walked_edges() -> None:
    svg = livegraph.graph_svg("single", RUN[:3], "running")
    assert '<g class="lg-node seen now pulse"><rect' in svg  # act, nœud en cours
    assert svg.count('class="lg-edge on"') == 2  # start → decide → act
    assert ">agir · outil<" in svg


def test_awaiting_approval_marks_the_human_gate() -> None:
    events = [ev("DECISION", "decide"), ev("HUMAN", "budget_gate", kind="extend_budget")]
    svg = livegraph.graph_svg("single", events, "awaiting")
    assert 'class="lg-node wait"' in svg  # human_gate pas encore visité, mais en attente


def test_repeated_visits_are_counted_on_the_node() -> None:
    svg = livegraph.graph_svg("single", RUN, "done")
    assert ">×4<" in svg  # decide visité 4 fois
    assert ">×2<" in svg  # act et verify


def test_multi_agent_layout_uses_its_own_nodes() -> None:
    events = [ev("DECISION", "supervisor"), ev("TOOL", "researcher", name="search_cases")]
    svg = livegraph.graph_svg("multi", events, "running")
    assert ">superviseur<" in svg and ">chercheur<" in svg and ">décider<" not in svg


def test_empty_run_draws_an_idle_graph() -> None:
    svg = livegraph.graph_svg("single", [], "idle")
    assert "now" not in svg and 'class="lg-edge on"' not in svg
    assert "L'agent démarre" in livegraph.path_html([], live=True)
