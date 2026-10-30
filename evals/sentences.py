"""Citation coverage (EVALS.md, "Coverage sentences"): a fixed sentence splitter, no judge.

A sentence ends at . ! or ? followed by whitespace and a capital, a quote or a §, except after
an abbreviation (`s.`, `ss.`, `No.`, `p.m.`, …). Decimals and section numbers (`1.5`,
`591-2.1`) never split: no whitespace follows their dot. `[n]` markers right after the stop
belong to the sentence they close.
"""
from __future__ import annotations

import re

MIN_WORDS = 6
MARKER = re.compile(r"\[\d+\]")
# a stop, closing quotes/brackets, trailing markers, then whitespace before a sentence start
_BOUNDARY = re.compile(r"([.!?][\"”’')]*(?:\s*\[\d+\])*)\s+(?=[A-Z\"“‘(§])")
_ABBREVIATIONS = {"s", "ss", "no", "nos", "a.m", "p.m", "e.g", "i.e"}


def _abbreviation_before(text: str, stop: int) -> bool:
    if text[stop] != ".":
        return False
    words = text[:stop].split()
    return bool(words) and words[-1].lstrip("(“\"").lower() in _ABBREVIATIONS


def split_sentences(text: str) -> list[str]:
    sentences, start = [], 0
    for m in _BOUNDARY.finditer(text):
        if _abbreviation_before(text, m.start()):
            continue
        sentences.append(text[start:m.end(1)].strip())
        start = m.end(1)
    tail = text[start:].strip()
    if tail:
        sentences.append(tail)
    return [s for s in sentences if s]


def _words(sentence: str) -> int:
    return len(MARKER.sub(" ", sentence).split())


def coverage(text: str) -> tuple[int, int]:
    """(counted sentences with a marker, counted sentences). Not counted: sentences under 6 words,
    and the gap sentence: a final sentence without a marker after a cited one."""
    sentences = split_sentences(text)
    if len(sentences) > 1 and not MARKER.search(sentences[-1]) and any(MARKER.search(s) for s in sentences[:-1]):
        sentences = sentences[:-1]
    counted = [s for s in sentences if _words(s) >= MIN_WORDS]
    return sum(1 for s in counted if MARKER.search(s)), len(counted)
