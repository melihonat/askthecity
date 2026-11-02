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
AGREEMENT = {"agree": 47, "total": 52, "disagreements": [
    {"id": "q1", "run": 1, "fact": 1, "human": "contradicted", "judge": "present"},
    {"id": "q2", "run": 1, "fact": 2, "human": "absent", "judge": "present"}]}
PUBLISHED = {"agree": 47, "total": 52, "contradictionsMissed": 1}


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
    assert page_data(judged, {**AGREEMENT, "judge": judge})["agreement"] == PUBLISHED
    assert page_data(judged, {**AGREEMENT, "judge": {**judge, "prompt_hash": "old"}})["agreement"] is None


def test_no_test_runs_yet_renders_placeholders():
    data = page_data([])
    assert data["headerLink"] == "Evals" and data["ladder"] == [] and data["intro"] is None
    assert "No test-split run is committed yet." in results_md([], data)
    assert "| **shipped** | **–** | **–** | **–** |" in readme(README_IN, [], data)


def _run(base: dict, rung: str | None = None, sha: str | None = None, date: str | None = None, **cols) -> dict:
    """`base` with new column values; a new rung, SHA or date also makes it a new run."""
    columns = {k: {**v, **({"value": cols[k]} if k in cols else {})} for k, v in base["scores"]["columns"].items()}
    header = base["header"]
    if rung or sha or date:
        rung, date = rung or header["rung"], date or header["date"]
        header = {**header, "rung": rung, "git": {"sha": sha or header["git"]["sha"], "dirty": False}, "date": date,
                  "run_id": f"{date[:10]}-{rung}-130000"}
    return {"header": header, "scores": {"columns": columns}}


@pytest.fixture
def fixed(records):
    """The ladder's `shipped` misses the bar on cite precision; `shipped-2` and a `shipped` re-run beside it
    on a later commit, where `shipped-2` passes."""
    ladder_shipped = results.select(records)["shipped"]
    missed = [_run(r, cite_precision=0.80) if r is ladder_shipped else r
              for r in records]
    rerun = _run(ladder_shipped, "shipped", "2222222bbbb", "2026-11-03T10:00:00+00:00", cite_precision=0.79)
    fix = _run(ladder_shipped, "shipped-2", "2222222bbbb", "2026-11-03T10:30:00+00:00", cite_precision=0.92)
    return missed + [rerun, fix]


def test_a_fix_rung_is_appended_under_shipped_beside_its_rerun(fixed):
    data = page_data(fixed)
    rows = data["ladder"]
    assert [r["rung"] for r in rows] == ["dense", "hybrid", "rerank", "shipped", "shipped", "shipped-2"]
    assert rows[3]["run"] == "2026-11-02-shipped-120000"  # the ladder row is never replaced by the re-run
    assert rows[4]["run"] == "2026-11-03-shipped-130000" and "2222222" in rows[4]["why"]
    assert rows[5]["why"].startswith(results.WHY["shipped-2"].rstrip("."))
    cite = [c["key"] for c in data["columns"]].index("cite_precision")
    assert rows[5]["cells"][cite]["mark"] == "gain"  # 0.79 → 0.92, against the re-run, not the ladder row
    assert rows[4]["cells"][cite]["mark"] is None  # the re-run is a baseline, not a step up the ladder


def test_the_ship_bar_and_highlight_move_to_the_last_fix_rung(fixed):
    data = page_data(fixed)
    assert data["shipBar"] == {"rung": "shipped-2", "unmet": []}
    assert [(r["rung"], r["run"]) for r in data["ladder"] if r["highlight"]] == [("shipped-2", "2026-11-03-shipped-2-130000")]
    md = results_md(fixed, data)
    assert "`shipped`: misses: cite precision under 0.9." in md and "`shipped-2`: passes." in md


def test_the_headline_shows_a_fix_rung_only_once_it_passes(fixed):
    """The public app switches to a fix only when it passes, so the README's first screen does too."""
    assert "| **shipped-2** |" in readme(README_IN, fixed, page_data(fixed))
    missed = [_run(r, cite_precision=0.85) if r["header"]["rung"] == "shipped-2" else r for r in fixed]
    out = readme(README_IN, missed, page_data(missed))
    assert "| **shipped** | **7 / 7** | **0.80** |" in out and "**shipped-2**" not in out.split("headline:end")[0]


def test_a_fix_pair_on_its_own_sha_is_not_a_sha_warning(fixed, records):
    md = results_md(fixed, page_data(fixed))
    assert "more than one git SHA" not in md
    assert "fix rungs on `2222222`" in md
    stray = [_run(r, sha="3333333cccc") if r["header"]["rung"] == "dense" else r
             for r in fixed]
    assert "more than one git SHA" in results_md(stray, page_data(stray))


def test_a_fix_rung_without_a_rerun_on_its_sha_says_so(fixed):
    alone = [r for r in fixed if r["header"]["run_id"] != "2026-11-03-shipped-130000"]
    data = page_data(alone)
    assert [r["rung"] for r in data["ladder"]][-2:] == ["shipped", "shipped-2"]
    assert "no `shipped` re-run on its SHA" in results_md(alone, data)


def test_a_run_after_the_gold_audit_gets_its_own_rows_and_the_ship_bar(fixed):
    after = _run(results.select(fixed)["shipped"], "shipped", "4444444dddd", "2026-11-04T10:00:00+00:00", cite_precision=0.99)
    after["header"] = {**after["header"], "gold": 2}
    recs = fixed + [after]
    data = page_data(recs)
    assert [r["run"] for r in data["ladder"]] == [r["run"] for r in page_data(fixed)["ladder"]]  # ladder as it ran
    assert [(r["rung"], r["run"]) for r in data["audited"]] == [("shipped", "2026-11-04-shipped-130000")]
    assert all(c["mark"] is None for c in data["audited"][0]["cells"])  # compared with nothing
    assert data["auditNote"] and data["shipBar"]["rung"] == "shipped" and data["audited"][0]["highlight"]
    md = results_md(recs, data)
    assert "`shipped` after gold audit: passes." in md and "after the gold audit on `4444444`" in md
    assert "After the gold audit" not in readme(README_IN, fixed, page_data(fixed))
    assert page_data(fixed)["audited"] == [] and page_data(fixed)["auditNote"] is None


def test_fix_rung_goldens(fixed):
    data = page_data(fixed, AGREEMENT)
    golden("fix/RESULTS.md", results_md(fixed, data))
    golden("fix/README.md", readme(README_IN, fixed, data))
    golden("fix/results.json", json.dumps(data, ensure_ascii=False, indent=1) + "\n")


def test_missing_markers_raise(records):
    with pytest.raises(ResultsError):
        readme("# no markers\n", records, page_data(records))


def test_apply_writes_all_three(tmp_path, records):
    (tmp_path / "README.md").write_text(README_IN, encoding="utf-8")
    results.apply(RUNS, tmp_path / "RESULTS.md", tmp_path / "README.md", tmp_path / "evals" / "results.json", tmp_path / "none.json")
    assert json.loads((tmp_path / "evals" / "results.json").read_text(encoding="utf-8")) == page_data(records)
