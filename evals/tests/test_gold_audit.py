"""The gold audit sheet: off-gold citations grouped by (question, chunk), with the sentences citing them."""
from evals.gold_audit import rows

GOLD = {"a": {"question": "A?", "expect": "answer", "required": [["tmc:1-1:*"]], "acceptable": ["tmc:1-2"]},
        "r": {"question": "R?", "expect": "refuse"}}


def answer(text, *cited, passages=()):
    return {"response": {"kind": "answer", "text": text, "citations": [{"n": n, "chunkId": c} for n, c in cited],
                         "passages": list(passages) + [{"n": n, "chunkId": c, "href": f"https://x/{c}"} for n, c in cited]}}


def record(rung, *runs, stale=()):
    return {"header": {"rung": rung}, "scores": {"stale": [{"id": s} for s in stale]},
            "questions": [{"id": "a", "runs": list(runs)}]}


def test_off_gold_citations_are_grouped_across_rungs_with_their_sentences():
    text = "Gold says so [1]. Off gold says more [2]. Both [1][2]."
    sheet = rows([record("shipped", answer(text, (1, "tmc:1-1:a"), (2, "tmc:9-9"))),
                  record("dense", answer("Off gold again [3].", (3, "tmc:9-9"), (4, "tmc:1-2")), {"response": {"kind": "refusal"}})],
                 GOLD)
    assert [(r["question_id"], r["chunk_id"], r["cites"], r["rungs"]) for r in sheet] == [("a", "tmc:9-9", 2, "dense shipped")]
    assert sheet[0]["sentences"].split("\n") == ["Off gold says more [2].", "Both [1][2].", "Off gold again [3]."]
    assert sheet[0]["decision"] == "" and sheet[0]["href"] == "https://x/tmc:9-9"
    assert "chunk" not in sheet[0]  # chunk text stays out of the repo (CORPUS.md)


def test_definition_companions_and_stale_questions_are_left_out():
    companion = {"chunkId": "tmc:9-1", "companion": True, "defines": ["DOG"]}
    assert rows([record("shipped", answer("Dog [1].", (1, "tmc:9-1"), passages=[companion]))], GOLD) == []
    assert rows([record("shipped", answer("Off [1].", (1, "tmc:9-9")), stale=["a"])], GOLD) == []
