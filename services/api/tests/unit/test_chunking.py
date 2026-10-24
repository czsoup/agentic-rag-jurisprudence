from jurirag.application.chunking import TOKENS_PER_WORD, chunk_case, chunk_spans
from jurirag.domain.models import Case, CaseMeta, Provenance, Zone, ZoneSpan

PROVENANCE = Provenance(dataset="d", revision="r", split="s")


def _case(text: str, zones: list[ZoneSpan]) -> Case:
    meta = CaseMeta(case_id="c1", jurisdiction="Cour de cassation", provenance=PROVENANCE)
    return Case(meta=meta, text=text, zones=zones)


def test_windows_cover_text_without_cutting_sentences() -> None:
    text = " ".join(f"Phrase numéro {i} sur le litige." for i in range(200))
    windows = chunk_spans(text, 0, len(text), max_tokens=60, overlap=0.0)

    assert len(windows) > 1
    assert windows[0][0] == 0 and windows[-1][1] == len(text)
    for start, end in windows:
        assert text[end - 1] == "."  # chaque fenêtre se termine sur une fin de phrase
        assert len(text[start:end].split()) <= int(60 / TOKENS_PER_WORD)


def test_overlap_repeats_trailing_sentences() -> None:
    text = " ".join(f"Phrase {i} ici." for i in range(100))
    windows = chunk_spans(text, 0, len(text), max_tokens=40, overlap=0.2)

    assert windows[1][0] < windows[0][1]  # la fenêtre 2 commence avant la fin de la 1


def test_long_sentence_without_punctuation_is_split_by_words() -> None:
    text = " ".join(["mot"] * 500)
    windows = chunk_spans(text, 0, len(text), max_tokens=100, overlap=0.0)

    assert len(windows) >= 6


def test_passages_never_mix_zones_and_keep_offsets() -> None:
    expose = "Les faits sont les suivants. Le salarié a été licencié."
    dispositif = "PAR CES MOTIFS, la Cour rejette le pourvoi."
    text = f"{expose}\n{dispositif}"
    zones = [
        ZoneSpan(zone=Zone.EXPOSE, start=0, end=len(expose)),
        ZoneSpan(zone=Zone.DISPOSITIF, start=len(expose) + 1, end=len(text)),
    ]

    passages = chunk_case(_case(text, zones))

    assert [p.zone for p in passages] == [Zone.EXPOSE, Zone.DISPOSITIF]
    assert [p.passage_id for p in passages] == ["c1#expose-0", "c1#dispositif-0"]
    for passage in passages:
        assert text[passage.start : passage.end] == passage.text


def test_case_without_zones_falls_back_to_full_text() -> None:
    passages = chunk_case(_case("Un arrêt sans zonage. Deuxième phrase.", []))

    assert len(passages) == 1
    assert passages[0].zone == Zone.TEXTE
