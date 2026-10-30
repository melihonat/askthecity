"""The harness's run rules against a fake transport: sequential calls after a discarded warm-up, a 5xx
retried once, and a `limit` or HTTP error invalidating the run with nothing written."""
import pytest

from evals import harness
from evals.harness import RunInvalid, call, run_rung, strip_bodies

QUESTIONS = [{"id": f"q{i}", "question": f"question {i}?", "expect": "answer", "required": [["tmc:1-1:*"]], "split": "dev"}
             for i in range(1, 4)]


def events(kind="answer"):
    passage = {"n": 1, "chunkId": "tmc:1-1:A", "label": "Ch 1 § 1-1", "href": "https://x/1.pdf", "body": "City text"}
    final = ({"kind": "answer", "text": "Yes [1].", "citations": [{"n": 1, "chunkId": "tmc:1-1:A"}], "passages": [passage]}
             if kind == "answer" else {"kind": "limit", "limit": "global_daily"})
    if kind == "limit":
        return [{"type": "final", "response": final}]
    debug = {"candidates": [{"chunkId": "tmc:1-1:A"}], "pinned": [], "threshold": 0.35,
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


def test_a_5xx_is_retried_once():
    t = FakeTransport([(502, [])])
    assert call(t, "q?", "shipped")["response"]["kind"] == "answer"
    assert len(t.asked) == 2


@pytest.mark.parametrize("script", [
    [(502, []), (503, [])],
    [(500, []), (200, [{"type": "error", "message": "The demo hit an error."}])],
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


def test_strips_passage_bodies_but_keeps_ids_labels_and_hrefs():
    c = call(FakeTransport(), "q?", "shipped")
    stripped = strip_bodies(c)
    for p in [*stripped["passages"], *stripped["response"]["passages"]]:
        assert "body" not in p
        assert p["chunkId"] == "tmc:1-1:A" and p["href"] and p["label"]
    assert stripped["response"]["text"] == "Yes [1]."
    assert c["passages"][0]["body"] == "City text"  # the scorer's copy is untouched
