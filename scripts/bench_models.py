"""Banc d'essai des modèles Ollama sur les décisions d'un agent (phase B, DEC-001).

Chaque sonde reproduit une situation réelle de la boucle : même prompt système, mêmes
outils, mêmes paramètres que l'application. On mesure si le modèle prend la bonne décision,
avec des arguments valides, et en combien de temps. Résultats : docs/results/bench_models.{json,md}.

    uv run python scripts/bench_models.py --models qwen3.5:9b qwen3:8b --repeats 3
"""

import argparse
import asyncio
import json
import statistics
from pathlib import Path
from typing import Any

import httpx

from jurirag.application.agent.graph import AGENT_SYSTEM
from jurirag.application.agent.tools import READ_SPEC, SEARCH_SPEC, ReadCaseArgs, SearchCasesArgs
from jurirag.application.agent.verifier import is_abstention
from jurirag.application.evidence import extract_citations
from jurirag.config import get_settings
from jurirag.domain.llm import ChatMessage, ToolCall
from jurirag.infrastructure.ollama import OllamaClient

CASE_ID = "664451ddb94eb60008b3d1fd"
SEARCH_OBS = f"""3 décision(s) pour « abandon de poste faute grave » :

1. case_id={CASE_ID} — Cour de cassation · Chambre sociale · 2024-05-15 · n° 22-17.216 · solution : Cassation
<doc id="P1" zone="Motivations">
La faute grave est celle qui rend impossible le maintien du salarié dans l'entreprise. La mise à pied conservatoire n'est pas un préalable nécessaire à un licenciement pour faute grave.
</doc>

2. case_id=65a1b2c3d4e5f60718293a4b — Cour de cassation · Deuxième chambre civile · 2023-03-02 · solution : Rejet
<doc id="P2" zone="Dispositif">
PAR CES MOTIFS, la Cour REJETTE le pourvoi.
</doc>"""

READ_OBS = """Décision case_id=664451ddb94eb60008b3d1fd — Cour de cassation · Chambre sociale · 2024-05-15
<doc id="P3" zone="Exposé du litige">
M. X a été engagé en qualité de chauffeur. Absent sans justification depuis le 3 mars 2019, il a été licencié pour faute grave le 2 avril 2019.
</doc>
<doc id="P4" zone="Dispositif">
PAR CES MOTIFS, la Cour CASSE ET ANNULE l'arrêt rendu le 12 mai 2022 par la cour d'appel de Lyon.
</doc>"""


def probes() -> list[dict[str, Any]]:
    q1 = "Un abandon de poste peut-il justifier un licenciement pour faute grave ?"
    return [
        {
            "name": "1. chercher d'abord",
            "expect": "search",
            "messages": [ChatMessage(role="user", content=q1)],
        },
        {
            "name": "2. lire l'affaire pertinente",
            "expect": "read",
            "messages": [
                ChatMessage(
                    role="user",
                    content="Quelles étaient les dates d'absence et de licenciement du salarié dans l'arrêt de la chambre sociale du 15 mai 2024 ?",
                ),
                ChatMessage(
                    role="assistant",
                    tool_calls=[
                        ToolCall(
                            name="search_cases", arguments={"query": "abandon de poste faute grave"}
                        )
                    ],
                ),
                ChatMessage(role="tool", content=SEARCH_OBS, tool_name="search_cases"),
            ],
        },
        {
            "name": "3. répondre (preuves suffisantes)",
            "expect": "answer",
            "messages": [
                ChatMessage(
                    role="user",
                    content="Dans l'arrêt du 15 mai 2024, quand le salarié a-t-il été licencié et que décide la Cour ?",
                ),
                ChatMessage(
                    role="assistant",
                    tool_calls=[ToolCall(name="read_case", arguments={"case_id": CASE_ID})],
                ),
                ChatMessage(role="tool", content=READ_OBS, tool_name="read_case"),
            ],
        },
        {
            "name": "4. s'abstenir ou reformuler (rien trouvé)",
            "expect": "abstain_or_reformulate",
            "messages": [
                ChatMessage(
                    role="user",
                    content="Quelle est la jurisprudence sur la brevetabilité des logiciels d'intelligence artificielle ?",
                ),
                ChatMessage(
                    role="assistant",
                    tool_calls=[
                        ToolCall(
                            name="search_cases",
                            arguments={"query": "brevetabilité logiciel intelligence artificielle"},
                        )
                    ],
                ),
                ChatMessage(
                    role="tool",
                    content="Aucune décision trouvée pour « brevetabilité logiciel intelligence artificielle ». Reformuler avec d'autres termes juridiques, ou s'abstenir si la question sort du corpus.",
                    tool_name="search_cases",
                ),
                ChatMessage(
                    role="assistant",
                    tool_calls=[
                        ToolCall(
                            name="search_cases", arguments={"query": "brevet invention logiciel"}
                        )
                    ],
                ),
                ChatMessage(
                    role="tool",
                    content="Aucune décision trouvée pour « brevet invention logiciel ». Reformuler avec d'autres termes juridiques, ou s'abstenir si la question sort du corpus.",
                    tool_name="search_cases",
                ),
            ],
        },
    ]


def judge(expect: str, response: Any) -> tuple[bool, str]:
    calls = response.tool_calls
    if expect == "search":
        if len(calls) >= 1 and calls[0].name == "search_cases":
            try:
                SearchCasesArgs.model_validate(calls[0].arguments)
                return True, f"search_cases({calls[0].arguments.get('query')!r})"
            except Exception as exc:  # noqa: BLE001
                return False, f"arguments invalides : {exc}"
        return False, f"attendu search_cases, obtenu {[c.name for c in calls] or 'texte'}"
    if expect == "read":
        if calls and calls[0].name == "read_case":
            try:
                args = ReadCaseArgs.model_validate(calls[0].arguments)
            except Exception as exc:  # noqa: BLE001
                return False, f"arguments invalides : {exc}"
            return args.case_id == CASE_ID, f"read_case({args.case_id})"
        return False, f"attendu read_case, obtenu {[c.name for c in calls] or 'texte'}"
    if expect == "answer":
        cited = extract_citations(response.content)
        ok = (
            not calls
            and bool(cited)
            and set(cited) <= {"P3", "P4"}
            and "2 avril 2019" in response.content
        )
        return ok, f"citations {cited} ; {'outil' if calls else 'texte'}"
    if expect == "abstain_or_reformulate":
        if calls:
            new = calls[0].arguments.get("query", "")
            ok = calls[0].name == "search_cases" and new not in (
                "brevetabilité logiciel intelligence artificielle",
                "brevet invention logiciel",
            )
            return ok, f"nouvelle recherche {new!r}"
        return is_abstention(response.content), "abstention" if is_abstention(
            response.content
        ) else "réponse non sourcée ou citée"
    raise ValueError(expect)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["qwen3.5:9b", "qwen3:8b"])
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--think", action="store_true", help="active le raisonnement interne")
    args = parser.parse_args()
    settings = get_settings()
    rows: list[dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=settings.request_timeout_s) as http:
        client = OllamaClient(http, settings.ollama_base_url)
        for model in args.models:
            for probe in probes():
                for i in range(args.repeats):
                    params = settings.generation_params(model=model, think=args.think).model_copy(
                        update={"seed": 42 + i}
                    )
                    messages = [
                        ChatMessage(role="system", content=AGENT_SYSTEM),
                        *probe["messages"],
                    ]
                    response = await client.chat(messages, params, tools=[SEARCH_SPEC, READ_SPEC])
                    ok, detail = judge(probe["expect"], response)
                    rows.append(
                        {
                            "model": model,
                            "think": args.think,
                            "probe": probe["name"],
                            "run": i,
                            "ok": ok,
                            "detail": detail,
                            "latency_s": round(response.latency_ms / 1000, 1),
                            "completion_tokens": response.completion_tokens,
                            "content": response.content,
                            "tool_calls": [c.model_dump() for c in response.tool_calls],
                        }
                    )
                    print(
                        f"{model:<14} {probe['name']:<42} #{i} {'OK ' if ok else 'KO '} {response.latency_ms / 1000:5.1f}s  {detail[:90]}"
                    )

    out = Path("docs/results")
    out.mkdir(parents=True, exist_ok=True)
    suffix = "_think" if args.think else ""
    (out / f"bench_models{suffix}.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    lines = ["| modèle | sonde | réussites | latence médiane (s) |", "|---|---|---|---|"]
    for model in args.models:
        for probe in probes():
            sel = [r for r in rows if r["model"] == model and r["probe"] == probe["name"]]
            lines.append(
                f"| {model} | {probe['name']} | {sum(r['ok'] for r in sel)}/{len(sel)} | {statistics.median(r['latency_s'] for r in sel)} |"
            )
        sel = [r for r in rows if r["model"] == model]
        lines.append(
            f"| **{model}** | **total** | **{sum(r['ok'] for r in sel)}/{len(sel)}** | **{statistics.median(r['latency_s'] for r in sel)}** |"
        )
    (out / f"bench_models{suffix}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    asyncio.run(main())
