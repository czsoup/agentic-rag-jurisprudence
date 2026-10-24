import pytest

from jurirag.application.agent.tools import CaseTools, ToolExecutor
from jurirag.application.evidence import EvidenceRegistry, extract_citations
from jurirag.domain.errors import LLMUnavailableError
from jurirag.domain.llm import ToolCall
from tests.conftest import MemoryCases, WordRetriever

LICENCIEMENT = "aaaaaaaaaaaa000000000001"


@pytest.fixture
def executor(retriever: WordRetriever, cases: MemoryCases) -> ToolExecutor:
    return ToolExecutor(CaseTools(retriever, cases))


async def test_search_returns_cases_with_citable_aliases(executor: ToolExecutor) -> None:
    evidence = EvidenceRegistry()
    result = await executor.execute(
        ToolCall(name="search_cases", arguments={"query": "licenciement faute grave", "k": 3}),
        evidence,
    )

    assert result.ok
    assert result.data["results"][0]["case_id"] == LICENCIEMENT
    assert "[P" not in result.observation and 'id="P1"' in result.observation
    assert evidence.get("P1") is not None and evidence.get("P1").case_id == LICENCIEMENT  # type: ignore[union-attr]


async def test_search_without_results_says_so(executor: ToolExecutor) -> None:
    result = await executor.execute(
        ToolCall(name="search_cases", arguments={"query": "propriété intellectuelle brevet"}),
        EvidenceRegistry(),
    )

    assert result.ok and result.data["results"] == []
    assert "Aucune décision" in result.observation


async def test_read_case_returns_passages_in_document_order(executor: ToolExecutor) -> None:
    evidence = EvidenceRegistry()
    result = await executor.execute(
        ToolCall(name="read_case", arguments={"case_id": LICENCIEMENT}), evidence
    )

    assert result.ok
    zones = [p["zone"] for p in result.data["passages"]]
    assert zones == ["expose", "motivations", "dispositif"]
    assert len(evidence) == 3


async def test_aliases_are_stable_across_tools(executor: ToolExecutor) -> None:
    evidence = EvidenceRegistry()
    await executor.execute(
        ToolCall(name="search_cases", arguments={"query": "abandon de poste faute grave"}), evidence
    )
    first = dict(evidence.aliases)
    await executor.execute(
        ToolCall(name="read_case", arguments={"case_id": LICENCIEMENT}), evidence
    )

    for passage_id, alias in first.items():
        assert evidence.aliases[passage_id] == alias  # un passage garde son alias


@pytest.mark.parametrize(
    ("call", "error"),
    [
        (ToolCall(name="delete_index", arguments={}), "unknown_tool"),
        (ToolCall(name="", arguments={}), "unknown_tool"),
        (ToolCall(name="search_cases", arguments={"query": "ab"}), "invalid_arguments"),
        (ToolCall(name="search_cases", arguments={"query": "bail", "k": 99}), "invalid_arguments"),
        (ToolCall(name="search_cases", arguments={"__raw__": "texte"}), "invalid_arguments"),
        (ToolCall(name="read_case", arguments={"case_id": "../../etc"}), "invalid_arguments"),
        (
            ToolCall(name="read_case", arguments={"case_id": "ffffffffffff000000000099"}),
            "case_not_found",
        ),
    ],
)
async def test_invalid_calls_execute_nothing(
    executor: ToolExecutor, retriever: WordRetriever, call: ToolCall, error: str
) -> None:
    evidence = EvidenceRegistry()
    result = await executor.execute(call, evidence)

    assert not result.ok and result.error == error
    assert result.observation.startswith("Erreur")
    assert len(evidence) == 0 and retriever.queries == []


async def test_unavailable_embedding_service_is_not_recoverable(cases: MemoryCases) -> None:
    executor = ToolExecutor(
        CaseTools(WordRetriever(cases, fail=LLMUnavailableError("down")), cases)
    )
    result = await executor.execute(
        ToolCall(name="search_cases", arguments={"query": "bail commercial"}), EvidenceRegistry()
    )

    assert not result.ok and result.error == "tool_unavailable" and not result.recoverable


def test_extract_citations() -> None:
    assert extract_citations("Faute grave [P1]. Rejet [P2, P1] et [P3; P4].") == [
        "P1",
        "P2",
        "P3",
        "P4",
    ]
    assert extract_citations("Sans citation.") == []
