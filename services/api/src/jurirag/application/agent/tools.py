"""Outils de l'agent : `search_cases(query, k)` et `read_case(case_id)`.

Le modèle *propose* un appel ; ce module décide s'il est autorisé (liste blanche), valide
les arguments (pydantic) puis l'exécute : le LLM n'exécute rien.
Les erreurs sont renvoyées au modèle sous forme d'observation explicite.
Ces outils ne dépendent d'aucun LLM : ils sont testés seuls.
"""

import re
import time
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator

from jurirag.application.evidence import EvidenceRegistry
from jurirag.application.ports import CaseRepository, RetrieverPort
from jurirag.domain.errors import JuriragError, LLMError
from jurirag.domain.llm import ToolCall, ToolSpec
from jurirag.domain.models import ZONE_LABELS, CaseMeta, Passage, Zone

CASE_ID = re.compile(r"^[A-Za-z0-9_-]{6,64}$")
# Ordre de lecture par défaut d'une décision : faits et procédure, raisonnement, décision.
READ_ORDER = (Zone.EXPOSE, Zone.MOTIVATIONS, Zone.DISPOSITIF, Zone.MOYENS, Zone.TEXTE)


class SearchCasesArgs(BaseModel):
    query: str = Field(min_length=3, max_length=300)
    k: int = Field(5, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def _strip(cls, value: str) -> str:
        value = " ".join(value.split())
        if len(value) < 3:
            raise ValueError("requête trop courte")
        return value


class ReadCaseArgs(BaseModel):
    case_id: str
    focus: str | None = Field(None, max_length=300)

    @field_validator("case_id")
    @classmethod
    def _valid_id(cls, value: str) -> str:
        value = value.strip()
        if not CASE_ID.match(value):
            raise ValueError("identifiant de décision mal formé")
        return value


SEARCH_SPEC = ToolSpec(
    name="search_cases",
    description=(
        "Recherche des décisions de la Cour de cassation dans le corpus local (index hybride "
        "BM25 + embeddings). À utiliser quand aucune preuve n'a encore été trouvée, ou avec une "
        "requête reformulée si les résultats précédents ne suffisent pas. Renvoie, pour chaque "
        "décision, ses métadonnées et le passage le plus pertinent, avec un alias citable [Pn]."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Mots-clés juridiques ou question en langage naturel, en français.",
            },
            "k": {
                "type": "integer",
                "minimum": 1,
                "maximum": 10,
                "description": "Nombre de décisions à renvoyer (5 par défaut).",
            },
        },
        "required": ["query"],
    },
)

READ_SPEC = ToolSpec(
    name="read_case",
    description=(
        "Lit une décision précise, repérée par son case_id dans un résultat de search_cases. "
        "Renvoie ses passages (faits et procédure, motivations, dispositif) avec des alias "
        "citables [Pn]. Indiquer `focus` pour obtenir les passages qui traitent d'un point précis."
    ),
    parameters={
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "Identifiant exact de la décision."},
            "focus": {
                "type": "string",
                "description": "Point recherché dans la décision (facultatif).",
            },
        },
        "required": ["case_id"],
    },
)


class ToolResult(BaseModel):
    """Résultat d'exécution : `observation` est le texte renvoyé au modèle."""

    name: str
    arguments: dict[str, Any]
    ok: bool
    observation: str
    summary: str  # une ligne pour la trace
    error: str | None = None
    recoverable: bool = True
    latency_ms: float = 0.0
    data: dict[str, Any] = Field(default_factory=dict)  # résultat structuré pour l'interface


def _excerpt(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + " …"


def _meta_line(meta: CaseMeta) -> str:
    bits = [meta.title()]
    if meta.solution:
        bits.append(f"solution : {meta.solution}")
    if meta.publication and "Publié au Bulletin" in meta.publication:
        bits.append("publié au Bulletin")
    return " · ".join(bits)


class CaseTools:
    """Les outils réels, branchés sur l'index et le stockage des décisions."""

    def __init__(
        self,
        retriever: RetrieverPort,
        cases: CaseRepository,
        max_passages_per_read: int = 8,
        passage_chars: int = 1600,
    ) -> None:
        self._retriever = retriever
        self._cases = cases
        self._max_read = max_passages_per_read
        self._passage_chars = passage_chars

    @property
    def specs(self) -> list[ToolSpec]:
        return [SEARCH_SPEC, READ_SPEC]

    def _passage_block(self, alias: str, passage: Passage) -> str:
        zone = ZONE_LABELS[passage.zone]
        return f'<doc id="{alias}" zone="{zone}">\n{_excerpt(passage.text, self._passage_chars)}\n</doc>'

    async def search_cases(self, args: SearchCasesArgs, evidence: EvidenceRegistry) -> ToolResult:
        # On interroge plus de passages que de décisions demandées, puis on regroupe par décision.
        hits = await self._retriever.search(args.query, k=args.k * 4)
        best: dict[str, Any] = {}
        for hit in hits:
            if hit.passage.case_id not in best:
                best[hit.passage.case_id] = hit
            if len(best) == args.k:
                break
        if not best:
            return ToolResult(
                name="search_cases",
                arguments=args.model_dump(),
                ok=True,
                observation=(
                    f"Aucune décision trouvée pour « {args.query} ». Reformuler avec d'autres "
                    "termes juridiques, ou s'abstenir si la question sort du corpus."
                ),
                summary="0 résultat",
                data={"query": args.query, "results": []},
            )

        lines, results = [], []
        for rank, (case_id, hit) in enumerate(best.items(), start=1):
            meta = self._cases.get_meta(case_id)
            if meta is None:
                continue
            alias = evidence.add(hit.passage, meta)
            themes = ", ".join(meta.themes[:4])
            lines.append(
                f"{rank}. case_id={case_id} — {_meta_line(meta)}"
                + (f"\n   thèmes : {themes}" if themes else "")
                + f"\n{self._passage_block(alias, hit.passage)}"
            )
            results.append(
                {
                    "rank": rank,
                    "case_id": case_id,
                    "title": meta.title(),
                    "solution": meta.solution,
                    "score": hit.score,
                    "alias": alias,
                    "passage_id": hit.passage.passage_id,
                    "zone": hit.passage.zone.value,
                    "excerpt": _excerpt(hit.passage.text, 320),
                }
            )
        observation = (
            f"{len(results)} décision(s) pour « {args.query} » (classement par pertinence ; "
            "un score élevé n'est pas une preuve) :\n\n" + "\n\n".join(lines)
        )
        return ToolResult(
            name="search_cases",
            arguments=args.model_dump(),
            ok=True,
            observation=observation,
            summary=f"{len(results)} décision(s) ; meilleure : {results[0]['title']}",
            data={"query": args.query, "results": results},
        )

    async def read_case(self, args: ReadCaseArgs, evidence: EvidenceRegistry) -> ToolResult:
        meta = self._cases.get_meta(args.case_id)
        if meta is None:
            return ToolResult(
                name="read_case",
                arguments=args.model_dump(),
                ok=False,
                observation=(
                    f"Erreur : aucune décision avec case_id={args.case_id} dans le corpus. "
                    "Utiliser un case_id renvoyé par search_cases."
                ),
                summary="identifiant inconnu",
                error="case_not_found",
            )
        all_passages = self._cases.passages_of(args.case_id)
        if args.focus:
            hits = await self._retriever.search_in_case(args.focus, args.case_id, self._max_read)
            chosen = [h.passage for h in hits]
        else:
            order = {zone: i for i, zone in enumerate(READ_ORDER)}
            ranked = sorted(
                (p for p in all_passages if p.zone in order),
                key=lambda p: (order[p.zone], p.ordinal),
            )
            # Au moins le début de chaque zone clé, puis la suite dans l'ordre de lecture.
            firsts = [p for p in ranked if p.ordinal == 0]
            rest = [p for p in ranked if p.ordinal > 0]
            chosen = (firsts + rest)[: self._max_read]
        chosen.sort(key=lambda p: p.start)  # ordre du document

        blocks, passages = [], []
        for passage in chosen:
            alias = evidence.add(passage, meta)
            blocks.append(self._passage_block(alias, passage))
            passages.append(
                {
                    "alias": alias,
                    "passage_id": passage.passage_id,
                    "zone": passage.zone.value,
                    "text": passage.text,
                }
            )
        header = [f"Décision case_id={args.case_id} — {_meta_line(meta)}"]
        if meta.contested:
            header.append(f"Décision attaquée : {meta.contested}")
        if meta.visa:
            header.append("Textes visés : " + "; ".join(meta.visa[:5]))
        omitted = len(all_passages) - len(chosen)
        header.append(
            f"{len(chosen)} passage(s) sur {len(all_passages)}"
            + (f" ({omitted} non affichés ; préciser `focus` pour d'autres)" if omitted else "")
        )
        return ToolResult(
            name="read_case",
            arguments=args.model_dump(),
            ok=True,
            observation="\n".join(header) + "\n\n" + "\n\n".join(blocks),
            summary=f"{len(chosen)} passage(s) lus dans {meta.title()}",
            data={"case_id": args.case_id, "title": meta.title(), "passages": passages},
        )


class ToolExecutor:
    """Liste blanche + validation + exécution + mesure. Ne lève jamais : renvoie un ToolResult."""

    def __init__(self, tools: CaseTools) -> None:
        self._tools = tools
        self._registry: dict[
            str, tuple[type[BaseModel], Callable[[Any, EvidenceRegistry], Awaitable[ToolResult]]]
        ] = {
            "search_cases": (SearchCasesArgs, tools.search_cases),
            "read_case": (ReadCaseArgs, tools.read_case),
        }

    @property
    def specs(self) -> list[ToolSpec]:
        return self._tools.specs

    @property
    def names(self) -> list[str]:
        return list(self._registry)

    async def execute(self, call: ToolCall, evidence: EvidenceRegistry) -> ToolResult:
        start = time.perf_counter()
        result = await self._execute(call, evidence)
        result.latency_ms = round((time.perf_counter() - start) * 1000, 1)
        return result

    async def _execute(self, call: ToolCall, evidence: EvidenceRegistry) -> ToolResult:
        if call.name not in self._registry:
            return ToolResult(
                name=call.name or "?",
                arguments=call.arguments,
                ok=False,
                observation=(
                    f"Erreur : l'outil « {call.name} » n'existe pas. Outils autorisés : "
                    + ", ".join(self._registry)
                ),
                summary="outil non autorisé — rien n'a été exécuté",
                error="unknown_tool",
            )
        schema, function = self._registry[call.name]
        try:
            args = schema.model_validate(call.arguments)
        except ValidationError as exc:
            problems = "; ".join(
                f"{'.'.join(str(p) for p in e['loc']) or 'arguments'} : {e['msg']}"
                for e in exc.errors()
            )
            return ToolResult(
                name=call.name,
                arguments=call.arguments,
                ok=False,
                observation=f"Erreur : arguments invalides pour {call.name} ({problems}).",
                summary="arguments invalides — rien n'a été exécuté",
                error="invalid_arguments",
            )
        try:
            return await function(args, evidence)
        except LLMError as exc:  # l'embedding de la requête passe par Ollama
            return ToolResult(
                name=call.name,
                arguments=call.arguments,
                ok=False,
                observation=f"Erreur : service d'embedding indisponible ({exc}).",
                summary="outil indisponible",
                error="tool_unavailable",
                recoverable=False,
            )
        except JuriragError as exc:
            return ToolResult(
                name=call.name,
                arguments=call.arguments,
                ok=False,
                observation=f"Erreur de l'outil : {exc}",
                summary="erreur de l'outil",
                error="tool_error",
                recoverable=False,
            )
