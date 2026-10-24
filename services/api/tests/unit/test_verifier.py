import json

import pytest

from jurirag.application.agent.verifier import EvidenceVerifier, split_claims, supported_subset
from jurirag.application.evidence import EvidenceRegistry
from jurirag.domain.errors import LLMTimeoutError
from jurirag.domain.llm import GenerationParams
from jurirag.domain.verification import ClaimVerdict, NextAction, VerifierStatus
from tests.conftest import MemoryCases, ScriptedLLM, reply

PARAMS = GenerationParams(model="m", temperature=0, seed=1, top_p=1, num_predict=256, num_ctx=4096)
CASE = "aaaaaaaaaaaa000000000001"
QUESTION = "Le licenciement pour abandon de poste était-il justifié ?"


@pytest.fixture
def evidence(cases: MemoryCases) -> EvidenceRegistry:
    registry = EvidenceRegistry()
    for passage in cases.passages_of(CASE):  # P1 exposé, P2 motivations, P3 dispositif
        registry.add(passage, cases.get_meta(CASE))
    return registry


def judge(*verdicts: str) -> ScriptedLLM:
    payload = {
        "verdicts": [{"claim": i, "verdict": v, "reason": "r"} for i, v in enumerate(verdicts, 1)],
        "addresses_question": True,
        "relevance_reason": "r",
    }
    return ScriptedLLM([reply(json.dumps(payload))])


def test_split_claims_attaches_trailing_citations() -> None:
    claims = split_claims(
        "Le salarié a été licencié pour faute grave. [P1]\nLa Cour rejette le pourvoi [P3]."
    )
    assert claims == [
        ("Le salarié a été licencié pour faute grave. [P1]", ["P1"]),
        ("La Cour rejette le pourvoi [P3].", ["P3"]),
    ]


async def test_supported_answer_is_sufficient(evidence: EvidenceRegistry) -> None:
    verifier = EvidenceVerifier(judge("supports", "supports"), PARAMS)
    answer = (
        "M. X a été licencié pour faute grave le 3 mars 2019 [P1]. La Cour rejette le pourvoi [P3]."
    )

    report = await verifier.verify(QUESTION, answer, evidence)

    assert report.status == VerifierStatus.SUFFICIENT and report.next_action == NextAction.ANSWER
    assert report.llm_judge_used


async def test_no_evidence_is_insufficient_without_calling_the_judge() -> None:
    llm = ScriptedLLM([])
    report = await EvidenceVerifier(llm, PARAMS).verify(
        QUESTION, "Le licenciement est justifié [P1].", EvidenceRegistry()
    )

    assert (
        report.status == VerifierStatus.INSUFFICIENT
        and report.next_action == NextAction.SEARCH_AGAIN
    )
    assert llm.calls == []


async def test_unsourced_claim_fails_even_if_the_judge_agrees_with_the_rest(
    evidence: EvidenceRegistry,
) -> None:
    verifier = EvidenceVerifier(judge("supports"), PARAMS)
    answer = (
        "La Cour rejette le pourvoi [P3]. Le salarié percevra des dommages et intérêts importants."
    )

    report = await verifier.verify(QUESTION, answer, evidence)

    assert report.status == VerifierStatus.INSUFFICIENT
    assert report.unverified_claims == ["Le salarié percevra des dommages et intérêts importants."]
    assert supported_subset(report) == "La Cour rejette le pourvoi [P3]."


async def test_fabricated_citation_is_caught_by_rules(evidence: EvidenceRegistry) -> None:
    llm = ScriptedLLM([])
    report = await EvidenceVerifier(llm, PARAMS).verify(
        QUESTION, "La Cour a cassé l'arrêt d'appel [P9].", evidence
    )

    assert report.status == VerifierStatus.INSUFFICIENT
    assert "citation inexistante : P9" in report.claims[0].rule_failures
    assert llm.calls == []  # rien à juger : la citation n'existe pas


async def test_date_absent_from_cited_passage_is_flagged(evidence: EvidenceRegistry) -> None:
    verifier = EvidenceVerifier(judge("supports"), PARAMS)
    report = await verifier.verify(
        QUESTION, "M. X a été licencié pour faute grave le 4 avril 2020 [P1].", evidence
    )

    assert report.status == VerifierStatus.INSUFFICIENT
    assert any("4 avril 2020" in f for f in report.claims[0].rule_failures)


async def test_date_written_differently_still_matches(evidence: EvidenceRegistry) -> None:
    verifier = EvidenceVerifier(judge("supports"), PARAMS)
    report = await verifier.verify(
        QUESTION, "Le licenciement pour faute grave date du 3 mars 2019 [P1].", evidence
    )

    assert report.claims[0].rule_failures == []


async def test_contradiction_asks_for_a_human(evidence: EvidenceRegistry) -> None:
    verifier = EvidenceVerifier(judge("contradicts"), PARAMS)
    report = await verifier.verify(
        QUESTION, "La Cour a cassé l'arrêt et accueilli le pourvoi [P3].", evidence
    )

    assert (
        report.status == VerifierStatus.CONTRADICTORY and report.next_action == NextAction.ASK_HUMAN
    )


@pytest.mark.parametrize(
    "judge_llm",
    [
        ScriptedLLM([LLMTimeoutError("lent")]),
        ScriptedLLM([reply("ceci n'est pas du JSON")]),
        ScriptedLLM([reply('{"verdicts": []}')]),
        ScriptedLLM([reply('{"verdicts": [{"claim": 1, "verdict": "peut-être", "reason": ""}]}')]),
    ],
)
async def test_judge_failure_never_validates(
    evidence: EvidenceRegistry, judge_llm: ScriptedLLM
) -> None:
    report = await EvidenceVerifier(judge_llm, PARAMS).verify(
        QUESTION, "La Cour rejette le pourvoi formé [P3].", evidence
    )

    assert report.status == VerifierStatus.INSUFFICIENT
    assert report.claims[0].verdict == ClaimVerdict.NOT_ENOUGH_INFO


async def test_limit_statements_need_no_citation(evidence: EvidenceRegistry) -> None:
    verifier = EvidenceVerifier(judge("supports"), PARAMS)
    answer = "La Cour rejette le pourvoi formé [P3]. La décision ne précise pas le montant des indemnités."

    report = await verifier.verify(QUESTION, answer, evidence)

    assert report.status == VerifierStatus.SUFFICIENT and len(report.claims) == 1


async def test_unread_case_suggests_reading_it(evidence: EvidenceRegistry) -> None:
    verifier = EvidenceVerifier(judge("not_enough_info"), PARAMS)
    report = await verifier.verify(
        QUESTION, "La Cour rejette le pourvoi formé [P3].", evidence, read_cases=set()
    )

    assert report.next_action == NextAction.READ_CASE
    report = await EvidenceVerifier(judge("not_enough_info"), PARAMS).verify(
        QUESTION, "La Cour rejette le pourvoi formé [P3].", evidence, read_cases={CASE}
    )
    assert report.next_action == NextAction.SEARCH_AGAIN


async def test_faithful_but_off_topic_answer_is_insufficient(evidence: EvidenceRegistry) -> None:
    payload = {
        "verdicts": [{"claim": 1, "verdict": "supports", "reason": "r"}],
        "addresses_question": False,
        "relevance_reason": "porte sur la procédure, pas sur la question",
    }
    verifier = EvidenceVerifier(ScriptedLLM([reply(json.dumps(payload))]), PARAMS)

    report = await verifier.verify(QUESTION, "La Cour rejette le pourvoi formé [P3].", evidence)

    assert (
        report.status == VerifierStatus.INSUFFICIENT
        and report.next_action == NextAction.SEARCH_AGAIN
    )
    assert "ne traite pas directement" in report.justification


async def test_missing_relevance_field_never_validates(evidence: EvidenceRegistry) -> None:
    payload = {
        "verdicts": [{"claim": 1, "verdict": "supports", "reason": "r"}]
    }  # pertinence absente
    report = await EvidenceVerifier(ScriptedLLM([reply(json.dumps(payload))]), PARAMS).verify(
        QUESTION, "La Cour rejette le pourvoi formé [P3].", evidence
    )

    assert report.status == VerifierStatus.INSUFFICIENT


def test_abstention_detection() -> None:
    from jurirag.application.agent.verifier import is_abstention

    assert is_abstention(
        "Le corpus ne contient aucune décision sur ce sujet. La jurisprudence n'est donc pas disponible."
    )
    assert is_abstention("La question ne semble pas être abordée dans le corpus disponible.")
    assert not is_abstention(
        "La décision ne précise pas la date [P1]."
    )  # cite un passage : ce n'est pas une abstention
    assert not is_abstention("L'abandon de poste justifie un licenciement pour faute grave.")
