"""The judge's reply handling and which calls it grades, against a fake judge: no API calls."""
import json

import pytest

from evals.judge import JudgeError, info, judge_run, parse, user_message

FACTS = ["Drones need a permit in City parks.", "The fine is up to $5,000."]
ANSWER = "You need a permit to fly a drone in a City park [1]. Fines can reach $10,000 [2]."


def reply(*facts):
    return json.dumps({"facts": [{"fact": i, "verdict": v, "span": s} for i, v, s in facts]})


def test_parse_returns_one_verdict_per_fact_in_order():
    out = parse(reply((2, "contradicted", "Fines can reach $10,000"), (1, "present", "You need a permit")), FACTS, ANSWER)
    assert [(v["fact"], v["verdict"], v["span_found"]) for v in out] == [(1, "present", True), (2, "contradicted", True)]


def test_a_span_not_in_the_answer_is_flagged_not_fatal():
    out = parse(reply((1, "present", "permits are required"), (2, "absent", "")), FACTS, ANSWER)
    assert [v["span_found"] for v in out] == [False, True]


@pytest.mark.parametrize("bad", ["not json", reply((1, "present", "x")), reply((1, "present", "x"), (3, "absent", "")),
                                 reply((1, "present", "x"), (2, "wrong", ""))])
def test_a_reply_that_doesnt_grade_every_fact_raises(bad):
    with pytest.raises(JudgeError):
        parse(bad, FACTS, ANSWER)


def test_the_judge_sees_only_question_facts_and_answer():
    assert user_message("Can I fly a drone?", FACTS, ANSWER) == (
        "Question: Can I fly a drone?\n\nKey facts:\n1. Drones need a permit in City parks.\n"
        "2. The fine is up to $5,000.\n\nAnswer:\n<answer>\n" + ANSWER + "\n</answer>")


def test_info_pins_model_and_prompt():
    i = info()
    assert i["model"] == "claude-sonnet-5" and len(i["prompt_hash"]) == 12 and i["prompt_version"]


class FakeJudge:
    def __init__(self):
        self.graded = []

    def grade(self, question, key_facts, answer):
        self.graded.append(question)
        return [{"fact": i, "verdict": "present", "span": "", "span_found": True} for i in range(1, len(key_facts) + 1)]


def test_judges_only_answered_calls_of_answer_questions():
    gold = [{"id": "a", "question": "A?", "expect": "answer", "key_facts": FACTS},
            {"id": "r", "question": "R?", "expect": "refuse"}]
    answered = lambda: {"response": {"kind": "answer", "text": ANSWER}}  # noqa: E731
    refused = lambda: {"response": {"kind": "refusal", "reason": "model_declined"}}  # noqa: E731
    data = {"a": [answered(), refused(), answered()], "r": [answered(), refused(), refused()]}
    judge = FakeJudge()
    judge_run(data, gold, judge, log=lambda *_: None)
    assert judge.graded == ["A?", "A?"]
    assert ["judge" in c for c in data["a"]] == [True, False, True]
    assert not any("judge" in c for c in data["r"])
