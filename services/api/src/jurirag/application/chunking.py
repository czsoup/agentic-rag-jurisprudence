"""Découpage structurel puis récursif d'une décision en passages.

1. Structurel : une décision est d'abord découpée selon ses zones (exposé, moyens,
   motivations, dispositif…) — un passage ne mélange jamais deux zones.
2. Récursif : chaque zone est découpée en fenêtres de phrases d'environ `max_tokens`,
   avec un chevauchement de `overlap` (valeurs usuelles : 300–800 tokens, 10–20 %).

Les offsets de caractères sont conservés : chaque passage renvoie exactement à `Case.text`.
Le nombre de tokens est estimé (1 mot ≈ 1,3 token en français) : on évite de dépendre du
tokenizer du modèle d'embedding, l'ordre de grandeur suffit pour dimensionner les passages.
"""

import re
from dataclasses import dataclass

from jurirag.domain.models import Case, Passage, Zone, ZoneSpan

TOKENS_PER_WORD = 1.3
# Fin de phrase, ou saut de ligne (les arrêts sont fortement structurés en alinéas).
_SENTENCE_END = re.compile(r"(?<=[.;:!?])\s+|\n+")
_WORD = re.compile(r"\S+")

# Zones indexées. Les annexes sont exclues : elles reproduisent in extenso le moyen des
# parties (doublon des « moyens », et un argument de partie n'est pas ce que juge la Cour).
# L'introduction est gardée : elle porte la formation, les parties et la décision attaquée.
INDEXED_ZONES = (
    Zone.INTRODUCTION,
    Zone.EXPOSE,
    Zone.MOYENS,
    Zone.MOTIVATIONS,
    Zone.DISPOSITIF,
    Zone.TEXTE,
)


@dataclass(frozen=True)
class _Span:
    start: int
    end: int
    words: int


def _sentences(text: str, start: int, end: int) -> list[_Span]:
    spans: list[_Span] = []
    cursor = start
    for match in _SENTENCE_END.finditer(text, start, end):
        if match.start() > cursor:
            spans.append(_make_span(text, cursor, match.start()))
        cursor = match.end()
    if cursor < end:
        spans.append(_make_span(text, cursor, end))
    return [s for s in spans if s.words > 0]


def _make_span(text: str, start: int, end: int) -> _Span:
    return _Span(start, end, len(_WORD.findall(text, start, end)))


def _split_long(text: str, span: _Span, max_words: int) -> list[_Span]:
    """Une « phrase » trop longue (énumération sans ponctuation) est coupée par mots."""
    words = list(_WORD.finditer(text, span.start, span.end))
    pieces = []
    for i in range(0, len(words), max_words):
        group = words[i : i + max_words]
        pieces.append(_Span(group[0].start(), group[-1].end(), len(group)))
    return pieces


def chunk_spans(
    text: str, start: int, end: int, max_tokens: int, overlap: float
) -> list[tuple[int, int]]:
    """Fenêtres (start, end) couvrant text[start:end], alignées sur les phrases."""
    max_words = max(20, int(max_tokens / TOKENS_PER_WORD))
    overlap_words = int(max_words * overlap)

    units: list[_Span] = []
    for sentence in _sentences(text, start, end):
        if sentence.words > max_words:
            units.extend(_split_long(text, sentence, max_words))
        else:
            units.append(sentence)

    windows: list[tuple[int, int]] = []
    i = 0
    while i < len(units):
        j, words = i, 0
        while j < len(units) and (words + units[j].words <= max_words or j == i):
            words += units[j].words
            j += 1
        windows.append((units[i].start, units[j - 1].end))
        if j >= len(units):
            break
        # Chevauchement : la fenêtre suivante reprend les dernières phrases de celle-ci.
        back, carried = j, 0
        while back - 1 > i and carried + units[back - 1].words <= overlap_words:
            back -= 1
            carried += units[back].words
        i = back
    return windows


def chunk_case(case: Case, max_tokens: int = 450, overlap: float = 0.15) -> list[Passage]:
    spans = [s for s in case.zones if s.zone in INDEXED_ZONES and s.end > s.start]
    if not spans:  # pas de zonage exploitable : tout le texte, découpage récursif seul
        spans = [ZoneSpan(zone=Zone.TEXTE, start=0, end=len(case.text))]

    passages: list[Passage] = []
    ordinals: dict[Zone, int] = {}
    for span in sorted(spans, key=lambda s: s.start):
        for start, end in chunk_spans(case.text, span.start, span.end, max_tokens, overlap):
            ordinal = ordinals.get(span.zone, 0)
            ordinals[span.zone] = ordinal + 1
            passages.append(
                Passage(
                    passage_id=f"{case.meta.case_id}#{span.zone.value}-{ordinal}",
                    case_id=case.meta.case_id,
                    zone=span.zone,
                    ordinal=ordinal,
                    start=start,
                    end=end,
                    text=case.text[start:end],
                )
            )
    return passages
