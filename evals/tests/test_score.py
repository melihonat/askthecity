"""The scorer, against a hand-computed fixture: 3 answer questions (one with stale gold), 2 refuse
questions, 3 runs. Every expected number below is worked out by hand in the comments."""
import pytest

from evals.score import compare, matches, score

GOLD = [
    {"id": "q1", "expect": "answer", "required": [["tmc:591-2.3:*"], ["bl:470-2026:cl1"]], "acceptable": ["tmc:591-1.1:*"]},
    {"id": "q2", "expect": "answer", "required": [["tmc:608-19:*"]], "acceptable": []},
    {"id": "q3", "expect": "answer", "required": [["tmc:999-1:*"]]},  # matches nothing: stale
    {"id": "r1", "expect": "refuse"},
    {"id": "r2", "expect": "refuse"},
]
SNAPSHOT = {"tmc:591-2.3:A", "bl:470-2026:cl1", "tmc:591-1.1:x", "tmc:608-19:A", "tmc:608-1:A", "tmc:100-1"}

TOTAL_MS = {"q1": 1000, "q2": 2000, "q3": 3000, "r2": 4000}


def call(qid, candidates, context, response, pinned=()):
    total = TOTAL_MS[qid] if response["kind"] == "answer" else 500
    return {
        "passages": [{"chunkId": c} for c in context],
        "debug": {"candidates": [{"chunkId": c} for c in candidates], "pinned": list(pinned),
                  "timings": {"retrieval_ms": 100, "rerank_ms": 50, "generation_ms": None, "total_ms": total}},
        "response": response,
        "wall_ms": 0,
    }


def answer(text, *cited):
    return {"kind": "answer", "text": text, "citations": [{"n": i + 1, "chunkId": c} for i, c in enumerate(cited)]}


def refusal(reason):
    return {"kind": "refusal", "reason": reason}


Q1_TEXT = ("Drilling before 9 a.m. on Saturdays is not allowed [1]. "
           "Some exemptions exist for emergency work by utilities. "
           "A permit is needed for other cases [2].")  # coverage 2/3


def q1(run):
    # recall@20 and full@20 hit; the context lacks the by-law: hit@ctx yes, full@ctx no.
    # Cites one gold chunk and one outside gold: precision 0.5; never the by-law: cite full 0.
    return call("q1", ["tmc:591-2.3:A", "bl:470-2026:cl1"], ["tmc:591-2.3:A"],
                answer(Q1_TEXT, "tmc:591-2.3:A", "tmc:608-1:A"), pinned=["tmc:591-2.3:A"] if run == 0 else ())


def q2(run):
    # not among the 20 but in the context (a companion): recall 0, hit@ctx and full@ctx 1.
    # Declined in runs 1 and 3, answered right in run 2: unstable. Run 3's candidates differ.
    candidates = ["tmc:100-1"] if run < 2 else ["tmc:608-1:A"]
    response = answer("Drones need a permit in every City park [1].", "tmc:608-19:A") if run == 1 else refusal("model_declined")
    return call("q2", candidates, ["tmc:608-19:A"], response)


RUN_DATA = {
    "q1": [q1(r) for r in range(3)],
    "q2": [q2(r) for r in range(3)],
    "q3": [call("q3", ["tmc:100-1"], ["tmc:100-1"], answer("Short [1].", "tmc:100-1")) for _ in range(3)],
    "r1": [call("r1", ["tmc:100-1"], ["tmc:100-1"], refusal("below_threshold")) for _ in range(3)],
    "r2": [call("r2", ["tmc:100-1"], ["tmc:100-1"], answer("The answer is in the passage given here [1].", "tmc:100-1")) for _ in range(3)],
}


@pytest.fixture(scope="module")
def result():
    return score(RUN_DATA, GOLD, SNAPSHOT)


def col(result, name):
    return result["columns"][name]


@pytest.mark.parametrize("pattern, chunk_id, expected", [
    ("tmc:681-5:*", "tmc:681-5:C-D", True),
    ("tmc:681-5:*", "tmc:681-50:A", False),
    ("tmc:608-10:*", "tmc:608-10", True),        # a § kept whole has no part suffix
    ("tmc:608-1:*", "tmc:608-10", False),
    ("bl:470-2026:cl1", "bl:470-2026:cl1", True),
    ("bl:470-2026:cl1", "bl:470-2026:cl10", False),
    ("bl:1482-2025:cl1*", "bl:1482-2025:cl1:O-Y", True),
])
def test_patterns_are_exact_or_star_prefix(pattern, chunk_id, expected):
    assert matches(pattern, chunk_id) is expected


def test_retrieval_columns_come_from_run_1_without_stale_questions(result):
    # scored: q1, q2 (q3 stale; refuse questions never count)
    assert col(result, "recall@20") == {"value": 0.5, "n": 2, "spread": 0.0}   # q1 yes, q2 no
    assert col(result, "full@20") == {"value": 0.5, "n": 2, "spread": 0.0}     # q1 both groups
    assert col(result, "hit@ctx") == {"value": 1.0, "n": 2, "spread": 0.0}     # both in the context
    assert col(result, "full@ctx") == {"value": 0.5, "n": 2, "spread": 0.0}    # q1 lacks the by-law


def test_cite_precision_one_right_one_wrong_is_half(result):
    c = col(result, "cite_precision")
    assert [r["value"] for r in c["per_run"]] == [0.5, 0.75, 0.5]   # run 2 adds q2 at 1.0
    assert [r["n"] for r in c["per_run"]] == [1, 2, 1]
    assert c["value"] == pytest.approx(0.5833, abs=1e-4)
    assert c["spread"] == pytest.approx(0.25)
    assert c["n"] == 1


def test_cite_full_needs_every_required_group_cited(result):
    c = col(result, "cite_full")
    assert [r["value"] for r in c["per_run"]] == [0.0, 0.5, 0.0]   # q1 never cites the by-law; q2 run 2 does
    assert c["value"] == pytest.approx(1 / 6)


def test_coverage_is_per_answer_over_every_answered_question(result):
    c = col(result, "coverage")
    # run 1: q1 2/3, q3 has no counted sentence (skipped), r2 1/1 → (2/3 + 1) / 2; run 2 adds q2 1/1
    assert [r["value"] for r in c["per_run"]] == pytest.approx([5 / 6, 8 / 9, 5 / 6])
    assert [r["n"] for r in c["per_run"]] == [2, 3, 2]
    assert c["value"] == pytest.approx((5 / 6 + 8 / 9 + 5 / 6) / 3)


def test_refusal_columns(result):
    assert col(result, "refusal_recall")["value"] == 0.5          # r1 refused, r2 answered, every run
    assert col(result, "refusal_recall")["n"] == 2
    fr = col(result, "false_refusals")                            # q2 of q1–q3, runs 1 and 3; stale q3 still counts
    assert [r["value"] for r in fr["per_run"]] == pytest.approx([1 / 3, 0, 1 / 3])
    assert fr["n"] == 3
    assert fr["value"] == pytest.approx(2 / 9)
    assert fr["spread"] == pytest.approx(1 / 3)


def test_latency_pools_every_call(result):
    assert col(result, "passages_p50")["value"] == 150 and col(result, "passages_p50")["n"] == 15
    # answered totals: 1000×3, 2000, 3000×3, 4000×3 (refusals excluded) → nearest-rank p50 = 5th, p95 = 10th
    assert col(result, "total_p50")["value"] == 3000 and col(result, "total_p50")["n"] == 10
    assert col(result, "total_p95")["value"] == 4000


def test_stale_gold_is_dropped_and_listed(result):
    assert result["stale"] == [{"id": "q3", "groups": [["tmc:999-1:*"]]}]
    assert all(o["id"] != "q3" for o in result["off_gold"])


def test_flags_retrieval_mismatch_and_unstable_questions(result):
    assert result["retrieval_mismatch"] == ["q2"]
    assert result["unstable"] == [{"id": "q2", "outcomes": ["refusal:model_declined", "answer", "refusal:model_declined"]}]


def test_lists_off_gold_citations_refusal_reasons_and_pins(result):
    assert result["off_gold"] == [{"id": "q1", "run": r, "chunkId": "tmc:608-1:A"} for r in (1, 2, 3)]
    assert result["refusals"] == {"false_refusals": {"model_declined": 2}, "refuse_questions": {"below_threshold": 3, "answer": 3}}
    assert result["pinned"] == ["q1"]


@pytest.mark.parametrize("new, previous, column, expected", [
    ({"value": 0.58, "spread": 0.25}, {"value": 0.40}, "cite_precision", "≈"),       # inside the new rung's spread
    ({"value": 0.58, "spread": 0.25}, {"value": 0.30}, "cite_precision", "better"),
    ({"value": 0.30, "spread": 0.05}, {"value": 0.58}, "cite_precision", "worse"),
    ({"value": 0.50, "spread": 0.0}, {"value": 0.45}, "recall@20", "better"),         # deterministic: any gain counts
    ({"value": 0.0, "spread": 0.0}, {"value": 0.1}, "false_refusals", "better"),      # lower is better
    ({"value": 2900, "spread": 300}, {"value": 3100}, "total_p50", "≈"),
])
def test_approx_decision_uses_the_spread(new, previous, column, expected):
    assert compare(new, previous, column) == expected


def judged(c, *verdicts):
    return {**c, "judge": [{"fact": i, "verdict": v, "span": "", "span_found": True} for i, v in enumerate(verdicts, 1)]}


def test_an_unjudged_run_has_no_answer_correct_column(result):
    assert "answer_correct" not in result["columns"] and result["contradicted"] == []


def test_any_contradicted_fact_zeroes_answer_correct():
    # q1 (2 facts): run 1 both present → 1; run 2 one present, one contradicted → 0, not 0.5; run 3 one absent → 0.5.
    # q2 is answered only in run 2, both present → 1. Stale q3 still counts (no chunk ids involved): absent → 0.
    data = {**RUN_DATA,
            "q1": [judged(RUN_DATA["q1"][0], "present", "present"), judged(RUN_DATA["q1"][1], "present", "contradicted"),
                   judged(RUN_DATA["q1"][2], "present", "absent")],
            "q2": [RUN_DATA["q2"][0], judged(RUN_DATA["q2"][1], "present", "present"), RUN_DATA["q2"][2]],
            "q3": [judged(c, "absent") for c in RUN_DATA["q3"]]}
    result = score(data, GOLD, SNAPSHOT)
    c = col(result, "answer_correct")
    assert [r["value"] for r in c["per_run"]] == pytest.approx([0.5, 1 / 3, 0.25])
    assert [r["n"] for r in c["per_run"]] == [2, 3, 2]
    assert c["value"] == pytest.approx((0.5 + 1 / 3 + 0.25) / 3)
    assert c["spread"] == pytest.approx(0.25)
    assert c["contradicted"] == 1
    assert result["contradicted"] == [{"id": "q1", "run": 2, "fact": 2, "span": ""}]


def test_citing_a_definition_companion_is_acceptable_but_satisfies_nothing():
    # q2 run 2 cites its gold § plus two companions: a definition (acceptable) and an amending by-law
    # that defines nothing (outside gold). Precision 2/3; cite full still needs the gold § itself.
    response = answer("Drones need a permit in every City park [1][6][7].", "tmc:608-19:A", "tmc:608-1:drone", "bl:9-2026:cl1")
    response["passages"] = [{"chunkId": "tmc:608-19:A", "companion": False, "defines": []},
                            {"chunkId": "tmc:608-1:drone", "companion": True, "defines": ["DRONE"]},
                            {"chunkId": "bl:9-2026:cl1", "companion": True, "defines": []}]
    data = {**RUN_DATA, "q2": [RUN_DATA["q2"][0], {**RUN_DATA["q2"][1], "response": response}, RUN_DATA["q2"][2]]}
    result = score(data, GOLD, SNAPSHOT)
    assert col(result, "cite_precision")["per_run"][1]["value"] == pytest.approx((0.5 + 2 / 3) / 2)
    assert col(result, "cite_full")["per_run"][1]["value"] == 0.5
    assert {"id": "q2", "run": 2, "chunkId": "bl:9-2026:cl1"} in result["off_gold"]
    assert all(o["chunkId"] != "tmc:608-1:drone" for o in result["off_gold"])
