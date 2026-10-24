"""Rejoue des questions via l'API réelle et enregistre traces et métriques.

    uv run python scripts/run_scenarios.py                       # 3 scénarios de test
    uv run python scripts/run_scenarios.py --set comparison      # banc statique / agent / multi

Questions : docs/results/questions.json (choisies dans le corpus indexé ; voir `selection`).
Sorties : docs/traces/<id>_<mode>.{json,md} et docs/results/<set>.{csv,md}.
Une validation humaine éventuelle reçoit la décision passée en `--hitl` ; elle est consignée
comme telle dans la trace (ce n'est pas une décision prise par le modèle).
"""

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any

import httpx

API = "http://127.0.0.1:8000"
TIMEOUT = httpx.Timeout(10.0, read=900.0)


def stream(path: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = []
    with httpx.stream("POST", API + path, json=payload, timeout=TIMEOUT) as response:
        response.raise_for_status()
        buffer = b""
        for chunk in response.iter_bytes():
            buffer += chunk
            *lines, buffer = buffer.split(b"\n")  # découpage sur « \n » seulement
            for line in lines:
                if not line.strip():
                    continue
                item = json.loads(line)
                items.append(item)
                if item["type"] == "event":
                    e = item["event"]
                    print(
                        f"   {e['step']:02d} {e['type']:<11} [{e['agent']}] {e['summary'][:150]}",
                        flush=True,
                    )
    return items


def run_agent(question: dict[str, Any], mode: str, hitl: str) -> dict[str, Any]:
    session = f"{question['id']}-{mode}-{int(time.time())}"
    started = time.perf_counter()
    items = stream(
        "/api/v1/runs",
        {
            "session_id": session,
            "question": question["question"],
            "mode": mode,
            "case_id": question.get("case_id"),
        },
    )
    while items[-1].get("status") == "awaiting_approval":
        print(
            f"   → validation humaine demandée ({items[-1]['approval']['kind']}) : réponse du script = {hitl}"
        )
        items += stream(f"/api/v1/sessions/{session}/resume", {"decision": hitl})
    status = items[-1]
    events = [i["event"] for i in items if i["type"] == "event"]
    return {
        "mode": mode,
        "session": session,
        "run_id": next(i["run_id"] for i in items if i["type"] == "run"),
        "events": events,
        "final": status.get("final") or {},
        "metrics": status.get("metrics") or {},
        "wall_s": round(time.perf_counter() - started, 1),
        "hitl_answer": hitl if any(e["type"] == "HUMAN" for e in events) else None,
    }


def run_static(question: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    response = httpx.post(
        API + "/api/v1/rag/ask",
        json={"question": question["question"], "case_id": question.get("case_id"), "k": 5},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    body = response.json()
    verifier = body.get("verifier") or {}
    return {
        "mode": "static",
        "final": {
            "answer": body["answer"],
            "verifier_status": verifier.get("status"),
            "sources": [p for p in body["passages"] if p["alias"] in body["cited"]],
            "unverified": verifier.get("unverified_claims"),
        },
        "metrics": body["metrics"],
        "wall_s": round(time.perf_counter() - started, 1),
        "passages": body["passages"],
    }


def markdown(question: dict[str, Any], result: dict[str, Any]) -> str:
    final, m = result["final"], result["metrics"]
    lines = [
        f"# Trace — {question['title']} ({result['mode']})",
        "",
        f"**Question** : {question['question']}",
        "",
        f"**Pourquoi cette question** : {question['selection']}",
        "",
        f"**Comportement attendu** : {question['expected']}",
        "",
        f"Run `{result.get('run_id', '—')}` · statut `{final.get('status', '—')}` · vérification `{final.get('verifier_status')}` · arrêt `{final.get('stop_reason', '—')}`",
        "",
        f"Appels LLM : {m.get('llm_calls')} · outils : {m.get('tool_calls')} · recherches : {m.get('searches')} · itérations : {m.get('iterations')} · tokens : {(m.get('prompt_tokens') or 0) + (m.get('completion_tokens') or 0)} · latence : {(m.get('total_latency_ms') or 0) / 1000:.1f} s",
    ]
    if result.get("hitl_answer"):
        lines += [
            "",
            f"> Validation humaine : réponse fournie par le script de scénario (`--hitl {result['hitl_answer']}`).",
        ]
    if result.get("events"):
        lines += [
            "",
            "## Trace d'exécution",
            "",
            "| # | type | agent | résumé | latence |",
            "|---|---|---|---|---|",
        ]
        for e in result["events"]:
            summary = e["summary"].replace("|", "\\|").replace("\n", " ")
            if e["type"] == "TOOL":
                summary = f"`{summary}`"
            lat = f"{e['latency_ms'] / 1000:.1f} s" if e.get("latency_ms") else ""
            lines.append(f"| {e['step']} | {e['type']} | {e['agent']} | {summary} | {lat} |")
    lines += ["", "## Réponse finale", "", final.get("answer", "")]
    if final.get("sources"):
        lines += ["", "## Passages cités", ""]
        for s in final["sources"]:
            lines += [
                f"- **[{s['alias']}]** {s['title']} — {s.get('zone_label', s.get('zone'))} (`{s['passage_id']}`)",
                f"  > {' '.join(s['text'].split())[:700]}",
            ]
    if final.get("limits"):
        lines += ["", "## Limites", ""] + [f"- {x}" for x in final["limits"]]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", default="scenarios", choices=["scenarios", "comparison"])
    parser.add_argument("--modes", nargs="+", default=None)
    parser.add_argument("--hitl", default="reject", choices=["approve", "reject"])
    parser.add_argument("--only", nargs="*", help="identifiants de questions à rejouer")
    args = parser.parse_args()

    questions = json.loads(Path("docs/results/questions.json").read_text(encoding="utf-8"))[
        args.set
    ]
    if args.only:
        questions = [q for q in questions if q["id"] in args.only]
    modes = args.modes or (["single"] if args.set == "scenarios" else ["static", "single", "multi"])
    traces = Path("docs/traces")
    traces.mkdir(parents=True, exist_ok=True)
    rows = []
    for question in questions:
        for mode in modes:
            print(f"\n== {question['id']} · {mode} · {question['question']}")
            result = (
                run_static(question) if mode == "static" else run_agent(question, mode, args.hitl)
            )
            stem = f"{question['id']}_{mode}"
            (traces / f"{stem}.json").write_text(
                json.dumps({"question": question, **result}, ensure_ascii=False, indent=1),
                encoding="utf-8",
            )
            (traces / f"{stem}.md").write_text(markdown(question, result), encoding="utf-8")
            m, final = result["metrics"], result["final"]
            rows.append(
                {
                    "question": question["id"],
                    "type": question.get("kind", ""),
                    "mode": mode,
                    "statut": final.get("status", "answered" if mode == "static" else ""),
                    "vérification": final.get("verifier_status"),
                    "arrêt": final.get("stop_reason", "—"),
                    "passages cités": len(final.get("sources") or []),
                    "appels LLM": m.get("llm_calls"),
                    "appels outils": sum((m.get("tool_calls") or {}).values()),
                    "recherches": m.get("searches"),
                    "itérations": m.get("iterations", 1 if mode == "static" else None),
                    "tokens": (m.get("prompt_tokens") or 0) + (m.get("completion_tokens") or 0),
                    "latence (s)": round((m.get("total_latency_ms") or 0) / 1000, 1),
                }
            )
            print(f"   ⇒ {rows[-1]}")
    out = Path("docs/results") / args.set
    with out.with_suffix(".csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    header = "| " + " | ".join(rows[0]) + " |"
    out.with_suffix(".md").write_text(
        "\n".join(
            [header, "|" + "---|" * len(rows[0])]
            + ["| " + " | ".join(str(v) for v in r.values()) + " |" for r in rows]
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
