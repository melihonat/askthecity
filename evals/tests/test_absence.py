"""False absence claims: finding the sentences, checking a `false` verdict's quote, the review sheet."""
import json

import pytest

from evals.absence import AbsenceError, absence_sentences, check_run, is_false, parse, rows

PASSAGES = [{"n": 1, "chunkId": "tmc:1-1", "label": "§ 1-1", "body": "In force on May 21, 2026."},
            {"n": 2, "chunkId": "tmc:1-2", "label": "§ 1-2", "body": "Yards must be cleared in 24 hours."}]


def test_absence_sentences_are_found_in_their_usual_wordings():
    text = ("The limit is 2.0 mg/L [1]. The passages do not state the in-force date. The documents don't cover yards. "
            "This is not addressed in the passages. No passage says who enforces it. The City does not clear lanes [2].")
    assert absence_sentences(text) == ["The passages do not state the in-force date.", "The documents don't cover yards.",
                                       "This is not addressed in the passages.", "No passage says who enforces it."]


def reply(*items):
    return json.dumps({"sentences": [{"sentence": i, "verdict": v, "passage": p, "span": s} for i, (v, p, s) in enumerate(items, 1)]})


def test_a_false_verdict_counts_only_when_its_quote_is_in_that_passage():
    sentences = ["The passages do not state the date.", "They don't cover yards.", "They don't say who enforces it."]
    out = parse(reply(("false", 1, "May 21, 2026"), ("false", 1, "Yards must be cleared"), ("true", 0, "")), PASSAGES, sentences)
    assert [(v["verdict"], v["chunkId"], v["span_found"]) for v in out] == [
        ("false", "tmc:1-1", True), ("false", "tmc:1-1", False), ("true", None, True)]
    assert [is_false(v) for v in out] == [True, False, False]


def test_an_unusable_reply_raises():
    with pytest.raises(AbsenceError):
        parse(reply(("true", 0, "")), PASSAGES, ["a.", "b."])  # one verdict for two sentences
    with pytest.raises(AbsenceError):
        parse("not json", PASSAGES, ["a."])


class FakeChecker:
    def __init__(self):
        self.seen = []

    def check(self, question, passages, answer, sentences):
        self.seen.append((question, [p["body"] for p in passages], sentences))
        return parse(reply(*[("false", 1, "May 21, 2026")] * len(sentences)), passages, sentences)


def call(text, kind="answer"):
    return {"response": {"kind": kind, "text": text, "passages": [{k: v for k, v in p.items() if k != "body"} | {"href": "h"}
                                                                  for p in PASSAGES]}}


RECORD = {"header": {"run_id": "r1"}, "questions": [
    {"id": "a", "runs": [call("Date [1]. The passages do not state the date."), call("No gap here [1]."),
                         call("", "refusal")]}]}


def test_check_run_sends_bodies_only_for_answers_with_an_absence_sentence_and_keeps_them_out_of_the_result():
    checker = FakeChecker()
    result = check_run(RECORD, {"a": "When?"}, {p["chunkId"]: p["body"] for p in PASSAGES}, checker, log=lambda _: None)
    assert checker.seen == [("When?", [p["body"] for p in PASSAGES], ["The passages do not state the date."])]
    assert result["summary"] == {"answers": 2, "absence": 1, "false": 1, "answers_with_false": 1, "unfound_quotes": 0, "unchecked": 0}
    assert "Yards must be cleared" not in json.dumps(result)  # passage bodies never stored (CORPUS.md)


def test_the_sheet_has_every_false_and_a_seeded_sample_of_true():
    v = lambda verdict, i: {"sentence": i, "text": f"s{i}", "verdict": verdict, "passage": 1 if verdict == "false" else 0,  # noqa: E731
                            "chunkId": None, "span": "", "span_found": verdict == "true"}
    result = {"run_id": "r1", "calls": [{"id": "a", "run": 1, "verdicts": [v("false", 1)] + [v("true", i) for i in range(2, 50)]}]}
    sheet = rows([result], {"r1": RECORD})
    assert sheet[0]["verdict"] == "false (quote not found)" and sheet[0]["passage"] == "[1] § 1-1"
    assert len(sheet) == 31 and sheet == rows([result], {"r1": RECORD})
