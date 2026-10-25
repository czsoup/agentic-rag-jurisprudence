"""Produit le résumé faits / procédure / décision d'une affaire via l'API réelle et l'enregistre.

    uv run python scripts/record_summary.py 65f1500528057200093c3e89

Contrôle automatique : chaque citation [Pn] du résumé doit désigner un passage réellement
fourni au modèle (même règle que R2 du vérificateur). La justesse juridique du résumé n'est
pas jugée ici : elle relève d'une relecture humaine.
Sorties : docs/traces/R1_resume.{json,md}. La relecture humaine est ajoutée à la main ensuite :
relancer le script l'écrase.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any

import httpx

API = "http://127.0.0.1:8000"
OUT = Path("docs/traces")
CITE = re.compile(r"\[(P\d+(?:\s*[,;]\s*P\d+)*)\]")
SECTIONS = {"faits": "Faits", "procedure": "Procédure", "decision": "Décision"}


def citations(text: str) -> list[str]:
    return [a for group in CITE.findall(text) for a in re.split(r"\s*[,;]\s*", group)]


def check(summary: dict[str, Any]) -> dict[str, Any]:
    shown = {p["alias"] for p in summary["passages"]}
    per_section = {k: citations(v) for k, v in summary["sections"].items()}
    cited = {a for aliases in per_section.values() for a in aliases}
    return {
        "passages_fournis": sorted(shown, key=lambda a: int(a[1:])),
        "citations_par_section": per_section,
        "citations_inconnues": sorted(cited - shown),
        "sections_sans_citation": [k for k, v in per_section.items() if not v],
    }


def markdown(summary: dict[str, Any], control: dict[str, Any]) -> str:
    ok = not control["citations_inconnues"]
    lines = [
        f"# Trace — Résumé faits / procédure / décision : {summary['title']}",
        "",
        f"Produit par `POST /api/v1/cases/{summary['case_id']}/summary` (modèle "
        f"`{summary['params']['model']}`, température {summary['params']['temperature']}, "
        f"graine {summary['params']['seed']}) en {summary['latency_ms'] / 1000:.1f} s. "
        "Commande : `uv run python scripts/record_summary.py " + summary["case_id"] + "`.",
        "",
        "**Contrôle automatique des citations** : "
        + (
            "toutes les citations désignent un passage fourni au modèle."
            if ok
            else f"citations sans passage : {', '.join(control['citations_inconnues'])}."
        )
        + (
            f" Sections sans citation : {', '.join(control['sections_sans_citation'])}."
            if control["sections_sans_citation"]
            else ""
        ),
        "",
    ]
    if summary["missing_zones"]:
        lines += [f"Zones absentes du zonage : {', '.join(summary['missing_zones'])}.", ""]
    for key, label in SECTIONS.items():
        lines += [f"## {label}", "", summary["sections"][key], ""]
    lines += ["## Passages fournis au modèle", ""]
    for p in summary["passages"]:
        text = " ".join(p["text"].split())
        lines += [
            f"- **[{p['alias']}]** {p['zone_label']} (`{p['passage_id']}`)",
            f"  > {text[:400]}{'…' if len(text) > 400 else ''}",
        ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("case_id")
    args = parser.parse_args()
    response = httpx.post(
        f"{API}/api/v1/cases/{args.case_id}/summary", timeout=httpx.Timeout(10.0, read=600.0)
    )
    response.raise_for_status()
    summary = response.json()
    control = check(summary)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "R1_resume.json").write_text(
        json.dumps({**summary, "controle": control}, ensure_ascii=False, indent=1)
    )
    (OUT / "R1_resume.md").write_text(markdown(summary, control))
    print(json.dumps(control, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
