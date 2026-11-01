"""The results renderer against a fixture run.json set: RESULTS.md, the README's generated blocks and the
/evals data match their golden files. `UPDATE_GOLDEN=1 pytest` rewrites the goldens after a deliberate change."""
import json
import os
import re
from pathlib import Path

import pytest

from evals import results
from evals.results import ResultsError, load, page_data, readme, results_md, ship_bar

HERE = Path(__file__).parent
RUNS = HERE / "fixtures" / "runs"
GOLDEN = HERE / "golden"
README_IN = """# Title

Hand-written text above.

<!-- headline:start (generated from evals/runs, do not edit) -->
stale headline
<!-- headline:end -->

Hand-written text between.

<!-- ladder:start (generated from evals/runs, do not edit) -->
<!-- ladder:end -->

Hand-written text below.
"""
AGREEMENT = {"agree": 47, "total": 52}


def golden(name: str, actual: str) -> None:
    path = GOLDEN / name
    if os.environ.get("UPDATE_GOLDEN"):
        path.parent.mkdir(exist_ok=True)
        path.write_text(actual, encoding="utf-8")
    assert actual == path.read_text(encoding="utf-8")


@pytest.fixture
def records():
    return load(RUNS)


def test_results_md(records):
    golden("RESULTS.md", results_md(records, page_data(records, AGREEMENT)))


def test_readme_blocks_rewrite_only_between_markers(records):
    out = readme(README_IN, records, page_data(records, AGREEMENT))
    golden("README.md", out)
    outside = lambda md: re.sub(r"<!-- (\w+):start.*?<!-- \1:end -->", "", md, flags=re.S)  # noqa: E731
    assert outside(out) == outside(README_IN)


def test_page_data(records):
    golden("results.json", json.dumps(page_data(records, AGREEMENT), ensure_ascii=False, indent=1) + "\n")


def test_only_the_latest_test_run_of_each_rung_is_published(records):
    data = page_data(records)
    assert [r["run"] for r in data["ladder"]][-1] == "2026-11-02-shipped-120000"  # not the earlier one, not dev
    assert data["headerLink"] == "Evals · 7/7 trick questions refused"


def test_changes_inside_the_spread_are_marked_and_no_gain_rungs_say_so(records):
    rows = {r["rung"]: r for r in page_data(records)["ladder"] + page_data(records)["side"]}
    hybrid = {c["label"]: cell for c, cell in zip(page_data(records)["columns"], rows["hybrid"]["cells"])}
    assert hybrid["hit@ctx"]["mark"] == "gain" and hybrid["trick questions refused"]["mark"] is None  # unchanged
    rerank = {c["label"]: cell for c, cell in zip(page_data(records)["columns"], rows["rerank"]["cells"])}
    assert rerank["cite precision"]["mark"] == "same"  # 0.80 → 0.81, inside its 0.03 spread
    assert rows["side-sonnet"]["why"].endswith("— no measurable gain.")
    assert not rows["shipped"]["why"].endswith("no measurable gain.")


def test_passing_shipped_is_highlighted(records):
    rows = page_data(records)["ladder"]
    assert [r["rung"] for r in rows if r["highlight"]] == ["shipped"]


def test_ship_bar_needs_a_judged_run_with_no_contradicted_fact():
    cols = {"false_refusals": {"value": 0.0}, "refusal_recall": {"value": 6 / 7}, "cite_precision": {"value": 0.9},
            "total_p50": {"value": 4999}, "answer_correct": {"value": 0.9, "contradicted": 0}}
    assert ship_bar(cols) == []
    assert ship_bar({**cols, "answer_correct": {"value": 0.9, "contradicted": 1}}) == ["a contradicted key fact"]
    assert ship_bar({k: v for k, v in cols.items() if k != "answer_correct"}) == ["not judged yet"]
    assert ship_bar({**cols, "refusal_recall": {"value": 5 / 7}, "total_p50": {"value": 5000}}) == [
        "refusal recall under 6 of 7", "total p50 not under 5 s"]


def test_an_audit_of_another_judge_is_not_published(records):
    shipped = results.select(records)["shipped"]
    judge = {"model": "claude-sonnet-5", "prompt_hash": "abc"}
    judged = [{**r, "header": {**r["header"], "judge": judge}} if r is shipped else r for r in records]
    assert page_data(judged, {**AGREEMENT, "judge": judge})["agreement"] == AGREEMENT
    assert page_data(judged, {**AGREEMENT, "judge": {**judge, "prompt_hash": "old"}})["agreement"] is None


def test_no_test_runs_yet_renders_placeholders():
    data = page_data([])
    assert data["headerLink"] == "Evals" and data["ladder"] == [] and data["intro"] is None
    assert "No test-split run is committed yet." in results_md([], data)
    assert "| **shipped** | **–** | **–** | **–** |" in readme(README_IN, [], data)


def test_missing_markers_raise(records):
    with pytest.raises(ResultsError):
        readme("# no markers\n", records, page_data(records))


def test_apply_writes_all_three(tmp_path, records):
    (tmp_path / "README.md").write_text(README_IN, encoding="utf-8")
    results.apply(RUNS, tmp_path / "RESULTS.md", tmp_path / "README.md", tmp_path / "evals" / "results.json", tmp_path / "none.json")
    assert json.loads((tmp_path / "evals" / "results.json").read_text(encoding="utf-8")) == page_data(records)
