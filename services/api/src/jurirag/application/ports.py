"""Ports : contrats dont dépend la couche application.

Les implémentations (Ollama, bm25s, numpy, SQLite) vivent dans `infrastructure/` et sont
câblées dans `bootstrap.py`. Les tests injectent des implémentations factices.
"""

from collections.abc import Sequence
from typing import Any, Protocol

from jurirag.domain.llm import ChatMessage, GenerationParams, LLMResponse, ToolSpec
from jurirag.domain.models import Case, CaseMeta, Passage, PassageHit, RetrievalMethod
from jurirag.domain.trace import RunMetrics, TraceEvent


class LLMPort(Protocol):
    async def chat(
        self,
        messages: Sequence[ChatMessage],
        params: GenerationParams,
        tools: Sequence[ToolSpec] | None = None,
        response_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """Un tour de génération. `tools` expose des outils ; `response_schema` contraint le JSON."""
        ...

    async def list_models(self) -> list[str]: ...


class EmbedderPort(Protocol):
    @property
    def model(self) -> str: ...

    async def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class CaseRepository(Protocol):
    def get_case(self, case_id: str) -> Case | None: ...

    def get_meta(self, case_id: str) -> CaseMeta | None: ...

    def passages_of(self, case_id: str) -> list[Passage]: ...

    def get_passages(self, passage_ids: Sequence[str]) -> list[Passage]: ...

    def count_cases(self) -> int: ...

    def count_passages(self) -> int: ...


class RetrieverPort(Protocol):
    @property
    def available_methods(self) -> list[RetrievalMethod]: ...

    async def search(
        self, query: str, k: int, method: RetrievalMethod | None = None
    ) -> list[PassageHit]:
        """Passages classés. `method=None` : méthode par défaut retenue après évaluation."""
        ...

    async def search_in_case(self, query: str, case_id: str, k: int) -> list[PassageHit]:
        """Passages d'une seule décision, classés par rapport à `query`."""
        ...


class RunStore(Protocol):
    def save_event(self, event: TraceEvent) -> None: ...

    def start_run(
        self, run_id: str, session_id: str, question: str, mode: str, model: str
    ) -> None: ...

    def finish_run(self, run_id: str, metrics: RunMetrics, answer: str | None) -> None: ...

    def list_runs(self, limit: int = 100) -> list[dict[str, Any]]: ...

    def get_run(self, run_id: str) -> dict[str, Any] | None: ...
