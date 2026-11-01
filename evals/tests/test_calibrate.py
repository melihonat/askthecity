"""The calibrate step: threshold = 0.5 × the lowest un-pinned dev answer gate score, and its table."""
import pytest

from evals.calibrate import CalibrationError, calibrate, render, replace_table, replace_threshold

GOLD = [
    {"id": "a1", "expect": "answer"},
    {"id": "a2", "expect": "answer"},
    {"id": "a3", "expect": "answer"},  # pinned: its low score doesn't count
    {"id": "r1", "expect": "refuse"},
]


def run(gate, pinned=False, outcome="answer"):
    response = {"kind": "answer"} if outcome == "answer" else {"kind": "refusal", "reason": outcome}
    return {"debug": {"gateScore": gate, "gateBypassed": pinned}, "response": response}


def record(questions, split="dev", rerank=True):
    return {"header": {"run_id": "2026-10-31-shipped-dev-1", "date": "2026-10-31T02:00:00+00:00", "split": split,
                       "rung": "shipped", "config": {"rerank": rerank}},
            "questions": [{"id": qid, "runs": runs} for qid, runs in questions]}


RECORD = record([
    ("a1", [run(0.78)] * 3),
    ("a2", [run(0.4571), run(0.4567, outcome="model_declined"), run(0.4569)]),  # scores jitter
    ("a3", [run(0.1, pinned=True)] * 3),
    ("r1", [run(0.29, outcome="below_threshold")] * 3),
])


def test_threshold_is_half_the_lowest_unpinned_answer_score_in_any_run_floored():
    result = calibrate(RECORD, GOLD)
    assert result["lowest"] == 0.4567
    assert result["threshold"] == 0.228  # 0.22835 floored, never rounded up


def test_rows_carry_score_pin_and_outcomes_answers_first():
    rows = calibrate(RECORD, GOLD)["rows"]
    assert [r["id"] for r in rows] == ["a1", "a2", "a3", "r1"]
    assert rows[1] == {"id": "a2", "expect": "answer", "gate_score": 0.4567, "spread": pytest.approx(0.0004),
                       "pinned": False, "outcome": "answer ×2, model_declined ×1"}
    assert rows[2]["pinned"] is True


def test_deterministic():
    assert render(calibrate(RECORD, GOLD)) == render(calibrate(RECORD, GOLD))


def test_table_marks_what_the_gate_does():
    table = render(calibrate(RECORD, GOLD))
    assert "threshold 0.228" in table
    assert "| `a3` | answer | 0.100 | 0.0000 | yes | answer ×3 | bypassed |" in table
    assert "| `r1` | refuse | 0.290 | 0.0000 | no | below_threshold ×3 | passes |" in table


@pytest.mark.parametrize("bad, message", [
    (record([("a1", [run(0.7)])], split="test"), "never tuned on test"),
    (record([("a1", [run(None)])], rerank=False), "no reranker"),
    (record([("a3", [run(0.1, pinned=True)])]), "no un-pinned"),
])
def test_rejects_runs_that_cant_calibrate(bad, message):
    with pytest.raises(CalibrationError, match=message):
        calibrate(bad, GOLD)


def test_replaces_table_and_config_in_place():
    md = "intro\n<!-- calibrate:start -->\nold\n<!-- calibrate:end -->\n## Next\n"
    out = replace_table(md, "<!-- calibrate:start -->\nnew\n<!-- calibrate:end -->")
    assert out == "intro\n<!-- calibrate:start -->\nnew\n<!-- calibrate:end -->\n## Next\n"
    ts = "// note\nexport const REFUSAL_THRESHOLD = 0.35;\n"
    assert replace_threshold(ts, 0.228) == "// note\nexport const REFUSAL_THRESHOLD = 0.228;\n"
    with pytest.raises(CalibrationError):
        replace_table("no markers", "x")
