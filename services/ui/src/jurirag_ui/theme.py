"""Direction artistique « Greffe » : composants de rendu partagés par les pages.

Registre éditorial plutôt que tableau de bord : listes denses façon index de recueil,
passages en marge numérotée, trace tenue comme un registre de greffe, tampon de contrôle.
Tout texte venant de l'API est échappé avant d'être inséré dans du HTML.
"""

import html
import re
from typing import Any

import streamlit as st

CSS = """
<style>
:root {
  --paper: #F4F0E6; --paper-2: #EAE3D3; --ink: #1C1B19; --ink-2: #5B564C;
  --rule: #D6CDB8; --oxblood: #7A2020; --verdigris: #4F6B5A; --ochre: #A0642A;
  --mark: #EFD9B4;
}
.block-container { padding-top: 2.2rem; max-width: 1380px; }
[data-testid="stHeader"] { background: transparent; }
h1, h2, h3 { letter-spacing: -0.01em; }
.masthead { border-bottom: 3px double var(--ink); padding-bottom: .55rem; margin-bottom: 1.2rem; }
.masthead .kicker { font: 500 .72rem/1 "IBM Plex Mono", monospace; letter-spacing: .14em;
  text-transform: uppercase; color: var(--oxblood); }
.masthead h1 { font-family: "Newsreader", serif; font-weight: 600; font-size: 2.3rem; margin: .25rem 0 0; }
.masthead p { color: var(--ink-2); margin: .3rem 0 0; font-size: .95rem; max-width: 70ch; }

.smallcaps { font-variant: small-caps; letter-spacing: .04em; color: var(--ink-2); }
.mono { font-family: "IBM Plex Mono", monospace; font-size: .8rem; }

/* Index des résultats */
.index-row { display: grid; grid-template-columns: 2.4rem 1fr; gap: .2rem .8rem;
  border-top: 1px solid var(--rule); padding: .75rem 0 .6rem; }
.index-row .num { font: italic 600 1.35rem/1.2 "Newsreader", serif; color: var(--oxblood); }
.index-row .title { font: 600 1.02rem/1.3 "Newsreader", serif; }
.index-row .meta { font-size: .8rem; color: var(--ink-2); margin-top: .1rem; }
.index-row .excerpt { font: 400 .9rem/1.5 "Newsreader", serif; color: var(--ink); margin-top: .35rem; }
.index-row .themes { font-size: .76rem; color: var(--ink-2); margin-top: .3rem; }

/* Passages : marginalia */
.passage { display: grid; grid-template-columns: 3.2rem 1fr; gap: .9rem; padding: .65rem .6rem;
  border-left: 2px solid var(--rule); margin: .35rem 0; scroll-margin-top: 5rem; }
.passage:target, .passage.hl { background: var(--mark); border-left-color: var(--oxblood); }
.passage .alias { font: 600 .82rem/1.3 "IBM Plex Mono", monospace; color: var(--oxblood); }
.passage .where { font-size: .74rem; color: var(--ink-2); margin-bottom: .2rem; }
.passage .text { font: 400 .95rem/1.6 "Newsreader", serif; white-space: pre-wrap; }
.origin { display: inline-block; font: 500 .66rem/1 "IBM Plex Mono", monospace; letter-spacing: .08em;
  text-transform: uppercase; border: 1px solid currentColor; padding: .15rem .3rem; margin-left: .35rem; }
.origin.corpus { color: var(--verdigris); }
.origin.externe { color: var(--ochre); }

/* Réponse */
.answer { font: 400 1.08rem/1.7 "Newsreader", serif; border-top: 1px solid var(--ink);
  padding-top: .8rem; margin-top: .4rem; }
a.cite { font: 600 .74rem/1 "IBM Plex Mono", monospace; color: var(--paper) !important;
  background: var(--oxblood); padding: .12rem .28rem; border-radius: 1px; text-decoration: none;
  vertical-align: .12em; margin-left: .12rem; }
a.cite:hover { background: var(--ink); }
a.cite.ghost { background: transparent; color: var(--oxblood) !important; border: 1px dashed var(--oxblood); }
.limits { font-size: .85rem; color: var(--ink-2); border-left: 2px solid var(--ochre); padding-left: .7rem; margin-top: .8rem; }

/* Tampon du vérificateur */
.stamp { display: inline-block; font: 600 .74rem/1 "IBM Plex Mono", monospace; letter-spacing: .16em;
  text-transform: uppercase; border: 2px solid currentColor; padding: .38rem .55rem; transform: rotate(-1.5deg); }
.stamp.sufficient { color: var(--verdigris); }
.stamp.insufficient { color: var(--oxblood); }
.stamp.contradictory { color: var(--ochre); }
.stamp.pending { color: var(--ink-2); border-style: dashed; }

/* Registre de trace */
.registry { list-style: none; padding: 0; margin: 0; counter-reset: none; }
.registry li { display: grid; grid-template-columns: 2rem 7.2rem 1fr; gap: .5rem; padding: .42rem 0;
  border-bottom: 1px dotted var(--rule); font-size: .86rem; line-height: 1.45; }
.registry .step { font: 500 .78rem/1.5 "IBM Plex Mono", monospace; color: var(--ink-2); text-align: right; }
.registry .type { font: 600 .7rem/1.6 "IBM Plex Mono", monospace; letter-spacing: .08em; }
.registry .agent { display: block; font: italic 400 .72rem/1.2 "Newsreader", serif; color: var(--ink-2); letter-spacing: 0; }
.registry .lat { font: 400 .72rem "IBM Plex Mono", monospace; color: var(--ink-2); margin-left: .4rem; }
.t-DECISION { color: var(--ink); } .t-TOOL { color: #6B4F2A; } .t-OBSERVATION { color: var(--ink-2); }
.t-CHECK { color: var(--verdigris); } .t-CHECK.bad { color: var(--oxblood); } .t-FINAL { color: var(--oxblood); }
.t-ERROR { color: #B3261E; } .t-HUMAN { color: var(--ochre); }
.registry .args { font: 400 .76rem/1.4 "IBM Plex Mono", monospace; color: #6B4F2A; word-break: break-word; }

/* Chiffres d'un run */
.figures { display: flex; flex-wrap: wrap; gap: 0; border-top: 1px solid var(--ink); border-bottom: 1px solid var(--rule); margin: .6rem 0; }
.figures div { padding: .45rem .9rem .45rem 0; margin-right: .9rem; }
.figures b { display: block; font: 600 1.15rem/1.2 "Newsreader", serif; }
.figures span { font-size: .7rem; color: var(--ink-2); text-transform: uppercase; letter-spacing: .08em; }

.memory { font-size: .84rem; border: 1px solid var(--rule); padding: .6rem .7rem; background: var(--paper-2); }
.empty { color: var(--ink-2); font-style: italic; font-family: "Newsreader", serif; padding: .8rem 0; }
.zone-label { font: 500 .72rem/1 "IBM Plex Mono", monospace; letter-spacing: .12em; text-transform: uppercase; color: var(--oxblood); margin: 1.1rem 0 .3rem; }
.case-text { font: 400 1rem/1.65 "Newsreader", serif; white-space: pre-wrap; max-width: 80ch; }
</style>
"""

STATUS_LABELS = {
    "sufficient": "Preuves suffisantes",
    "insufficient": "Preuves insuffisantes",
    "contradictory": "Sources contradictoires",
    None: "Non vérifié",
}


def esc(value: Any) -> str:
    return html.escape(str(value if value is not None else ""))


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def masthead(kicker: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="masthead"><div class="kicker">{esc(kicker)}</div><h1>{esc(title)}</h1>'
        + (f"<p>{esc(subtitle)}</p>" if subtitle else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def stamp(status: str | None) -> str:
    css = status if status in ("sufficient", "insufficient", "contradictory") else "pending"
    return f'<span class="stamp {css}">{esc(STATUS_LABELS.get(status, status))}</span>'


_CITE = re.compile(r"\[(P\d+(?:\s*[,;]\s*P\d+)*)\]")


def answer_html(answer: str, known: set[str], anchor_prefix: str = "src") -> str:
    """Remplace [P3] par un lien vers le passage ; une citation inconnue reste visible, en pointillés."""

    def repl(match: re.Match[str]) -> str:
        links = []
        for alias in re.split(r"\s*[,;]\s*", match.group(1)):
            cls = "cite" if alias in known else "cite ghost"
            title = "ouvrir le passage" if alias in known else "citation sans passage correspondant"
            links.append(
                f'<a class="{cls}" href="#{anchor_prefix}-{alias}" title="{title}">{esc(alias)}</a>'
            )
        return "".join(links)

    escaped = esc(answer)
    return f'<div class="answer">{_CITE.sub(repl, escaped)}</div>'


def passage_html(
    alias: str,
    title: str,
    zone_label: str,
    text: str,
    passage_id: str = "",
    origin: str = "corpus",
    anchor_prefix: str = "src",
) -> str:
    origin_cls = "corpus" if origin == "corpus" else "externe"
    return (
        f'<div class="passage" id="{anchor_prefix}-{esc(alias)}"><div class="alias">{esc(alias)}</div><div>'
        f'<div class="where">{esc(title)} — {esc(zone_label)}<span class="origin {origin_cls}">{esc(origin)}</span>'
        + (f' <span class="mono">{esc(passage_id)}</span>' if passage_id else "")
        + f'</div><div class="text">{esc(" ".join(text.split()))}</div></div></div>'
    )


def _args(data: dict[str, Any]) -> str:
    arguments = data.get("arguments") or {}
    shown = {k: v for k, v in arguments.items() if k != "__raw__"}
    return ", ".join(f"{k}={v!r}" for k, v in shown.items()) or "—"


def trace_html(events: list[dict[str, Any]]) -> str:
    if not events:
        return '<div class="empty">Aucune étape pour l\'instant.</div>'
    rows = []
    for event in events:
        type_ = event["type"]
        css = f"t-{type_}"
        if type_ == "CHECK" and event["data"].get("status") != "sufficient":
            css += " bad"
        body = esc(event["summary"])
        if type_ == "TOOL":
            body = f'<span class="args">{esc(event["data"].get("name"))}({esc(_args(event["data"]))})</span>'
        lat = (
            f'<span class="lat">{event["latency_ms"] / 1000:.1f} s</span>'
            if event.get("latency_ms")
            else ""
        )
        rows.append(
            f'<li><span class="step">{event["step"]:02d}</span>'
            f'<span class="type {css}">{esc(type_)}<span class="agent">{esc(event["agent"])}</span></span>'
            f"<span>{body}{lat}</span></li>"
        )
    return '<ol class="registry">' + "".join(rows) + "</ol>"


def figures_html(metrics: dict[str, Any]) -> str:
    tools = metrics.get("tool_calls") or {}
    cells = [
        ("Appels LLM", metrics.get("llm_calls", 0)),
        ("Appels d'outils", sum(tools.values())),
        ("Recherches", metrics.get("searches", 0)),
        ("Itérations", metrics.get("iterations", 0)),
        ("Tokens", (metrics.get("prompt_tokens") or 0) + (metrics.get("completion_tokens") or 0)),
        ("Latence", f"{(metrics.get('total_latency_ms') or 0) / 1000:.1f} s"),
        ("Coût", "n/a (local)"),
    ]
    return (
        '<div class="figures">'
        + "".join(f"<div><b>{esc(v)}</b><span>{esc(k)}</span></div>" for k, v in cells)
        + "</div>"
    )


def result_row(rank: int, title: str, meta: dict[str, Any], excerpt: str, score: float) -> str:
    bits = [
        b
        for b in (
            meta.get("solution"),
            "publié au Bulletin"
            if "Publié au Bulletin" in (meta.get("publication") or [])
            else None,
            meta.get("ecli"),
        )
        if b
    ]
    themes = " · ".join((meta.get("themes") or [])[:5])
    return (
        f'<div class="index-row"><div class="num">{rank}</div><div>'
        f'<div class="title">{esc(title)}</div>'
        f'<div class="meta">{esc(" · ".join(bits))} <span class="mono">score {score:.4f}</span></div>'
        f'<div class="excerpt">{esc(excerpt[:420])}{"…" if len(excerpt) > 420 else ""}</div>'
        + (f'<div class="themes smallcaps">{esc(themes)}</div>' if themes else "")
        + "</div></div>"
    )


def empty(message: str) -> None:
    st.markdown(f'<div class="empty">{esc(message)}</div>', unsafe_allow_html=True)
