"""The judge/human audit: a blind sheet out, agreement back."""
import csv
import json

import pytest

from evals import audit
from evals.audit import AuditError, compare, rows

GOLD = {"a": {"question": "A?", "key_facts": ["F1", "F2"]}, "b": {"question": "B?", "key_facts": ["G1"]}}


def call(*verdicts):
    return {"response": {"kind": "answer", "text": "text"}, "judge": [{"fact": i, "verdict": v} for i, v in enumerate(verdicts, 1)]}


RECORD = {"header": {"run_id": "2026-11-02-shipped-120000", "judge": {"model": "claude-sonnet-5", "prompt_hash": "abc"}},
          "questions": [{"id": "a", "runs": [call("present", "absent"), call("present", "present")]},
                        {"id": "b", "runs": [{"response": {"kind": "refusal"}}, call("contradicted")]}]}


def test_the_sheet_is_blind_and_covers_judged_answers_of_the_chosen_runs():
    sheet = rows(RECORD, GOLD, [1])
    assert [(r["question_id"], r["run"], r["fact"]) for r in sheet] == [("a", 1, 1), ("a", 1, 2)]   # b run 1 was refused
    assert all(r["human"] == "" and "judge" not in r for r in sheet)
    assert len(rows(RECORD, GOLD, [1, 2])) == 5


def test_agreement_counts_facts_and_lists_disagreements():
    sheet = rows(RECORD, GOLD, [1, 2])
    for r, human in zip(sheet, ["p", "present", "absent", "present", "c"]):
        r["human"] = human
    result = compare(RECORD, sheet)
    assert (result["agree"], result["total"]) == (3, 5)
    assert result["disagreements"] == [{"id": "a", "run": 1, "fact": 2, "human": "present", "judge": "absent"},
                                       {"id": "a", "run": 2, "fact": 1, "human": "absent", "judge": "present"}]
    assert result["judge"] == RECORD["header"]["judge"]


def test_a_blank_human_verdict_raises():
    with pytest.raises(AuditError, match="human verdict ''"):
        compare(RECORD, rows(RECORD, GOLD, [1]))


def test_sheet_round_trips_and_is_never_overwritten(tmp_path):
    runs = tmp_path / "runs"
    (runs / "r").mkdir(parents=True)
    (runs / "r" / "run.json").write_text(json.dumps(RECORD), encoding="utf-8")
    sheet = tmp_path / "audit.csv"
    gold = [{"id": k, **v} for k, v in GOLD.items()]
    assert audit.write_sheet(runs / "r", gold, [2], sheet) == 3
    with pytest.raises(AuditError, match="never overwritten"):
        audit.write_sheet(runs / "r", gold, [2], sheet)
    with sheet.open(encoding="utf-8-sig", newline="") as f:
        filled = [{**r, "human": "present"} for r in csv.DictReader(f)]
    with sheet.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, audit.FIELDS)
        w.writeheader()
        w.writerows(filled)
    result = audit.apply(runs, sheet, tmp_path / "agreement.json")
    assert (result["agree"], result["total"]) == (2, 3)
    assert json.loads((tmp_path / "agreement.json").read_text(encoding="utf-8"))["agree"] == 2
