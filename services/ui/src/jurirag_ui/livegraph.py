"""Graphe de la boucle en direct et récapitulatif du parcours d'un run.

Tout est déduit des événements de trace : chaque événement porte le nœud du graphe qui
l'a émis (`node`). Le schéma est dessiné en SVG, sur une seule ligne (Streamlit interprète
le Markdown autour du HTML), et n'affiche que des chemins réellement parcourus.
"""

from typing import Any

from jurirag_ui.theme import esc

W, H = 124, 30  # taille d'un nœud

# Position (centre) et libellé de chaque nœud, par mode. Reprend docs/diagrams/03 et 05.
LAYOUTS: dict[str, dict[str, tuple[int, int, str]]] = {
    "single": {
        "start": (200, 22, "départ"),
        "decide": (106, 88, "décider"),
        "act": (294, 88, "agir · outil"),
        "verify": (106, 158, "vérifier"),
        "budget_gate": (294, 158, "budget"),
        "human_gate": (200, 226, "validation humaine"),
        "finalize": (106, 294, "répondre"),
        "abstain": (294, 294, "s'abstenir"),
    },
    "multi": {
        "start": (200, 22, "départ"),
        "supervisor": (200, 84, "superviseur"),
        "researcher": (64, 150, "chercheur"),
        "write": (200, 150, "rédiger"),
        "budget_gate": (336, 150, "budget"),
        "verify": (200, 216, "vérifier"),
        "human_gate": (336, 216, "validation humaine"),
        "finalize": (130, 290, "répondre"),
        "abstain": (270, 290, "s'abstenir"),
    },
}

EDGES: dict[str, list[tuple[str, str]]] = {
    "single": [
        ("start", "decide"), ("decide", "act"), ("act", "decide"), ("act", "abstain"),
        ("decide", "verify"), ("decide", "budget_gate"), ("decide", "abstain"),
        ("verify", "finalize"), ("verify", "decide"), ("verify", "abstain"),
        ("verify", "budget_gate"), ("verify", "human_gate"), ("budget_gate", "human_gate"),
        ("budget_gate", "finalize"), ("budget_gate", "abstain"), ("human_gate", "decide"),
        ("human_gate", "finalize"), ("human_gate", "abstain"),
    ],
    "multi": [
        ("start", "supervisor"), ("supervisor", "researcher"), ("researcher", "supervisor"),
        ("researcher", "abstain"), ("supervisor", "write"), ("supervisor", "abstain"),
        ("supervisor", "budget_gate"), ("write", "verify"), ("write", "abstain"),
        ("verify", "finalize"), ("verify", "supervisor"), ("verify", "human_gate"),
        ("verify", "abstain"), ("budget_gate", "human_gate"), ("budget_gate", "finalize"),
        ("budget_gate", "abstain"), ("human_gate", "supervisor"), ("human_gate", "finalize"),
        ("human_gate", "abstain"),
    ],
}  # fmt: skip


def visits(events: list[dict[str, Any]]) -> list[str]:
    """Suite des nœuds traversés, sans répétition consécutive. `start` n'émet rien."""
    path = ["start"]
    for event in events:
        node = event.get("node")
        if node and node != path[-1]:
            path.append(node)
    return path


def _anchor(a: tuple[int, int], b: tuple[int, int], offset: float) -> tuple[float, ...]:
    """Segment entre deux nœuds, coupé au bord des rectangles et décalé si l'arête est double."""
    (x1, y1), (x2, y2) = a, b
    dx, dy = x2 - x1, y2 - y1
    norm = max((dx * dx + dy * dy) ** 0.5, 1e-6)
    ox, oy = -dy / norm * offset, dx / norm * offset
    t = min((W / 2 + 4) / abs(dx) if dx else 1e9, (H / 2 + 4) / abs(dy) if dy else 1e9)
    return (x1 + dx * t + ox, y1 + dy * t + oy, x2 - dx * t + ox, y2 - dy * t + oy)


def graph_svg(mode: str, events: list[dict[str, Any]], phase: str = "idle") -> str:
    """Schéma de la boucle. `phase` : idle, running, awaiting (validation humaine) ou done."""
    layout, edges = LAYOUTS.get(mode, LAYOUTS["single"]), EDGES.get(mode, EDGES["single"])
    path = visits(events) if events else []
    walked = set(zip(path, path[1:], strict=False))
    counts = {n: path.count(n) for n in set(path)}
    current = "human_gate" if phase == "awaiting" else (path[-1] if path else None)
    pairs = set(edges)

    parts = [
        '<svg class="livegraph" viewBox="0 0 400 312" role="img" '
        'aria-label="Graphe de la boucle agentique, nœud en cours surligné">'
        '<defs><marker id="lg-a" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" '
        'markerHeight="6" orient="auto"><path d="M0,0 L8,4 L0,8 z" class="lg-head"/></marker>'
        '<marker id="lg-a-on" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" '
        'markerHeight="6" orient="auto"><path d="M0,0 L8,4 L0,8 z" class="lg-head-on"/></marker>'
        "</defs>"
    ]
    for src, dst in edges:
        if src not in layout or dst not in layout:
            continue
        offset = 4 if (dst, src) in pairs else 0
        x1, y1, x2, y2 = _anchor(layout[src][:2], layout[dst][:2], offset)
        on = (src, dst) in walked
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'class="lg-edge{" on" if on else ""}" marker-end="url(#lg-a{"-on" if on else ""})"/>'
        )
    for node, (x, y, label) in layout.items():
        css = "lg-node"
        if node in counts:
            css += " seen"
        if node == current:
            css += {"running": " now pulse", "awaiting": " wait", "done": " now"}.get(phase, " now")
        parts.append(
            f'<g class="{css}"><rect x="{x - W / 2}" y="{y - H / 2}" width="{W}" height="{H}" rx="3"/>'
            f'<text x="{x}" y="{y + 4}" text-anchor="middle">{esc(label)}</text>'
        )
        if counts.get(node, 0) > 1:
            parts.append(
                f'<text x="{x + W / 2 - 3}" y="{y - H / 2 + 9}" text-anchor="end" '
                f'class="lg-count">×{counts[node]}</text>'
            )
        parts.append("</g>")
    parts.append("</svg>")
    return "".join(parts)


TOOL_LABELS = {"search_cases": "chercher", "read_case": "lire"}
FINAL_LABELS = {
    "answered": ("répondre", "ok"),
    "partial": ("réponse partielle", "warn"),
    "abstained": ("s'abstenir", "warn"),
    "error": ("erreur", "bad"),
}


def path_steps(events: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """Étapes lisibles du parcours : (libellé, classe ok / bad / warn / neutral)."""
    steps: list[tuple[str, str]] = []
    for event in events:
        type_, data = event["type"], event.get("data") or {}
        if type_ == "TOOL":
            name = str(data.get("name"))
            steps.append((TOOL_LABELS.get(name, name), "neutral"))
        elif type_ == "CHECK":
            good = data.get("status") == "sufficient"
            steps.append(("vérifier ✓" if good else "vérifier ✗", "ok" if good else "bad"))
        elif type_ == "HUMAN":
            decision = data.get("decision")
            if decision is None:
                steps.append(("validation humaine", "warn"))
            else:
                steps.append((f"humain : {'oui' if decision == 'approve' else 'non'}", "warn"))
        elif type_ == "ERROR":
            steps.append(("erreur", "bad"))
        elif type_ == "DECISION" and event.get("node") == "write":
            steps.append(("rédiger", "neutral"))
        elif type_ == "FINAL":
            status = data.get("status") or (
                "abstained" if event.get("node") == "abstain" else "answered"
            )
            steps.append(FINAL_LABELS.get(status, (str(status), "neutral")))
    # Deux étapes identiques à la suite deviennent « chercher ×2 ».
    merged: list[tuple[str, str, int]] = []
    for label, css in steps:
        if merged and merged[-1][0] == label:
            merged[-1] = (label, css, merged[-1][2] + 1)
        else:
            merged.append((label, css, 1))
    return [(f"{label} ×{n}" if n > 1 else label, css) for label, css, n in merged]


def path_html(events: list[dict[str, Any]], live: bool = False) -> str:
    steps = path_steps(events)
    if not steps:
        return '<div class="path empty-path">' + ("L'agent démarre…" if live else "—") + "</div>"
    chips = '<span class="arrow">→</span>'.join(
        f'<span class="chip {css}">{esc(label)}</span>' for label, css in steps
    )
    tail = '<span class="arrow">→</span><span class="chip dots">…</span>' if live else ""
    return f'<div class="path"><span class="path-label">Parcours</span>{chips}{tail}</div>'
