"""The harness's run rules against a fake transport: sequential calls after a discarded warm-up, a 5xx
retried once, and a `limit` or HTTP error invalidating the run with nothing written."""
import json

import pytest

from evals import harness
from evals.harness import RunInvalid, call, run_rung, strip_bodies

QUESTIONS = [{"id": f"q{i}", "question": f"question {i}?", "expect": "answer", "required": [["tmc:1-1:*"]], "split": "dev"}
             for i in range(1, 4)]


def events(kind="answer", limit="global_daily"):
    passage = {"n": 1, "chunkId": "tmc:1-1:A", "label": "Ch 1 § 1-1", "href": "https://x/1.pdf", "body": "City text"}
    final = ({"kind": "answer", "text": "Yes [1].", "citations": [{"n": 1, "chunkId": "tmc:1-1:A"}], "passages": [passage]}
             if kind == "answer" else {"kind": "limit", "limit": limit})
    if kind == "limit":
        return [{"type": "final", "response": final}]
    debug = {"candidates": [{"chunkId": "tmc:1-1:A"}], "pinned": [], "threshold": 0.35, "config": {"model": "llm"},
             "build": {"sha": "abc", "embedder": "e", "reranker": "r", "promptVersion": "1", "promptHash": "h"},
             "timings": {"retrieval_ms": 1, "rerank_ms": 1, "generation_ms": 1, "total_ms": 3}}
    return [{"type": "passages", "passages": [passage]}, {"type": "debug", "debug": debug}, {"type": "final", "response": final}]


class FakeTransport:
    """Replays scripted (status, events) replies in order, then answers."""
    def __init__(self, script=()):
        self.script = list(script)
        self.asked = []

    def post(self, question, rung):
        self.asked.append((question, rung))
        return self.script.pop(0) if self.script else (200, events())


def test_runs_every_question_each_run_after_a_discarded_warm_up():
    t = FakeTransport()
    data = run_rung(QUESTIONS, "dense", t, runs=3, log=lambda *_: None)
    assert len(t.asked) == 1 + 3 * 3
    assert all(rung == "dense" for _, rung in t.asked)
    assert {qid: len(calls) for qid, calls in data.items()} == {"q1": 3, "q2": 3, "q3": 3}


@pytest.mark.parametrize("reply", [(502, []), (200, events("limit", "unavailable"))])
def test_a_server_error_is_retried_once(reply):
    t = FakeTransport([reply])
    assert call(t, "q?", "shipped")["response"]["kind"] == "answer"
    assert len(t.asked) == 2


@pytest.mark.parametrize("script", [
    [(502, []), (503, [])],
    [(500, []), (200, [{"type": "error", "message": "The demo hit an error."}])],
    [(200, events("limit", "unavailable")), (200, events("limit", "unavailable"))],
])
def test_a_second_server_error_aborts(script):
    with pytest.raises(RunInvalid, match="server error twice"):
        call(FakeTransport(script), "q?", "shipped")


def test_an_http_error_invalidates_without_retry():
    t = FakeTransport([(429, [])])
    with pytest.raises(RunInvalid, match="HTTP 429"):
        call(t, "q?", "shipped")
    assert len(t.asked) == 1


def test_a_missing_debug_event_invalidates():
    with pytest.raises(RunInvalid, match="passages → debug → final"):
        call(FakeTransport([(200, [events()[0], events()[2]])]), "q?", "shipped")


def test_a_limit_mid_run_invalidates_the_run_and_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(harness, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(harness, "load_gold", lambda split: QUESTIONS)
    monkeypatch.setattr(harness, "git_state", lambda: {"sha": "abc", "dirty": False})
    monkeypatch.setattr(harness, "read_snapshot", lambda: ({"id": "s1"}, {"tmc:1-1:A"}))
    # warm-up, then run 1 q1, q2, then a limit on q3
    t = FakeTransport([(200, events())] * 3 + [(200, events("limit"))])
    with pytest.raises(RunInvalid, match="global_daily"):
        harness.run("shipped", "dev", "http://test", "secret", "key", skip_preflight=True, transport=t)
    assert len(t.asked) == 4
    assert not (tmp_path / "runs").exists()


class FakeJudge:
    usage = {"input_tokens": 1_000_000, "output_tokens": 100_000, "calls": 9}

    def grade(self, question, key_facts, answer):
        return [{"fact": 1, "verdict": "contradicted" if question == "question 2?" else "present", "span": "Yes", "span_found": True}]


def fake_world(monkeypatch, tmp_path):
    monkeypatch.setattr(harness, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(harness, "load_gold", lambda split: [{**q, "key_facts": ["F"]} for q in QUESTIONS])
    monkeypatch.setattr(harness, "git_state", lambda: {"sha": "abc", "dirty": False})
    monkeypatch.setattr(harness, "read_snapshot", lambda: ({"id": "s1"}, {"tmc:1-1:A"}))
    monkeypatch.setattr(harness, "read_spend", lambda *_: {"usd": 0.01, "requests": 10})


def test_a_judged_run_records_the_judge_and_scores_answer_correct(tmp_path, monkeypatch):
    fake_world(monkeypatch, tmp_path)
    out = harness.run("shipped", "dev", "http://test", "secret", "key", skip_preflight=True, transport=FakeTransport(), judge=FakeJudge())
    record = json.loads((out / "run.json").read_text(encoding="utf-8"))
    j = record["header"]["judge"]
    assert j["model"] == "claude-sonnet-5" and j["prompt_hash"] and j["usd_estimate"] == 3.0   # $2 in + $1 out
    assert record["scores"]["columns"]["answer_correct"]["value"] == pytest.approx(2 / 3)   # q2 contradicted
    assert record["scores"]["columns"]["answer_correct"]["contradicted"] == 3
    assert record["questions"][0]["runs"][0]["judge"][0]["verdict"] == "present"
    report = (out / "report.md").read_text(encoding="utf-8")
    assert "| answer_correct | 0.67 |" in report and "`q2` run 1 fact 1: “Yes”" in report


def test_an_unjudged_run_says_so(tmp_path, monkeypatch):
    fake_world(monkeypatch, tmp_path)
    out = harness.run("shipped", "dev", "http://test", "secret", "key", skip_preflight=True, transport=FakeTransport())
    record = json.loads((out / "run.json").read_text(encoding="utf-8"))
    assert record["header"]["judge"] is None and "answer_correct" not in record["scores"]["columns"]
    assert "Not judged" in (out / "report.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("balance, rung, ok", [
    (3.30, "shipped", True),        # 72 calls × $0.0011 ≈ $0.08 → $3.22 left
    (3.05, "shipped", False),       # $2.97 left
    (3.50, "side-sonnet", False),   # 72 × $0.012 ≈ $0.86 → $2.64 left
])
def test_preflight_blocks_a_run_that_would_leave_under_3_dollars(monkeypatch, balance, rung, ok):
    monkeypatch.setattr(harness, "_gateway_get", lambda path, key, params=None: {"balance": str(balance)})
    if ok:
        assert harness.preflight(72, "key", rung)["balance_usd"] == balance
    else:
        with pytest.raises(SystemExit, match="Top up first"):
            harness.preflight(72, "key", rung)


def test_earlier_rungs_output_doesnt_make_the_tree_dirty(tmp_path, monkeypatch):
    import subprocess
    git = lambda *a: subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)  # noqa: E731
    git("init", "-q")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "x")
    monkeypatch.setattr(harness, "ROOT", tmp_path)
    (tmp_path / "evals" / "runs" / "2026-11-02-dense").mkdir(parents=True)
    (tmp_path / "evals" / "runs" / "2026-11-02-dense" / "run.json").write_text("{}")
    assert harness.git_state()["dirty"] is False
    (tmp_path / "evals" / "harness.py").write_text("")
    assert harness.git_state()["dirty"] is True


def test_strips_passage_bodies_but_keeps_ids_labels_and_hrefs():
    c = call(FakeTransport(), "q?", "shipped")
    stripped = strip_bodies(c)
    for p in [*stripped["passages"], *stripped["response"]["passages"]]:
        assert "body" not in p
        assert p["chunkId"] == "tmc:1-1:A" and p["href"] and p["label"]
    assert stripped["response"]["text"] == "Yes [1]."
    assert c["passages"][0]["body"] == "City text"  # the scorer's copy is untouched


def test_run_dir_names_a_second_run_on_the_same_day_by_suffix():
    assert harness.run_dir("shipped", "test", "2026-11-01").name == "2026-11-01-shipped"
    assert harness.run_dir("shipped", "dev", "2026-11-01").name == "2026-11-01-shipped-dev"
    assert harness.run_dir("shipped", "dev", "2026-11-01", "2").name == "2026-11-01-shipped-dev-2"


def test_run_dir_refuses_a_suffix_that_names_another_rung():
    # `shipped --suffix 2` wrote `2026-11-01-shipped-2`, the `shipped-2` rung's directory
    with pytest.raises(SystemExit, match="shipped-2"):
        harness.run_dir("shipped", "test", "2026-11-01", "2")
    assert harness.run_dir("shipped", "test", "2026-11-01", "b").name == "2026-11-01-shipped-b"
