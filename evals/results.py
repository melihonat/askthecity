"""The results renderer (STORY.md, EVALS.md "Files"): every published number comes from committed run
data, so `evals/RESULTS.md`, the README's generated blocks and the `/evals` page can never disagree.

Pure: run records in, text and page data out. `apply` reads `evals/runs/*/run.json` and writes all
three. Only `split: test` runs are published; dev runs tune the threshold and prompt, nothing else.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .score import compare

ROOT = Path(__file__).resolve().parent.parent
RUNS_DIR = ROOT / "evals" / "runs"
RESULTS_MD = ROOT / "evals" / "RESULTS.md"
README_MD = ROOT / "README.md"
PAGE_JSON = ROOT / "app" / "evals" / "results.json"
# the judge/human audit (EVALS.md, "Answer judge"): {"agree": int, "total": int}, once committed
AGREEMENT_JSON = ROOT / "evals" / "judge_agreement.json"

LADDER = ["dense", "hybrid", "rerank", "shipped"]
# fix rungs (LADDER.md, "Ship bar"): appended under `shipped`, each beside a `shipped` re-run on its SHA
FIX = ["shipped-2", "shipped-3"]
SIDE = ["side-sonnet", "side-quoted"]
WHY = {
    "dense": "Vector search only: embed the question, take the 5 closest passages.",
    "hybrid": 'Adds keyword search and exact section-number matching, so "591-2.1" finds § 591-2.1.',
    "rerank": "A reranker scores every passage against the question; if none scores high enough, it refuses before the model writes anything.",
    "shipped": "Brings in the by-laws that amended a cited section after the Code was last consolidated.",
    "shipped-2": "Fix: the prompt cites only the passage that states each sentence, and leads with the rule in force when a by-law changed a section.",
    "side-sonnet": "Sonnet 5.5 instead of Haiku 5.5, at ~20× the generation cost.",
    "side-quoted": "Asks the model to quote the supporting sentence for every citation.",
}
RERUN_WHY = "The same shipped stack re-run on {sha}, beside the fix below it: the fix is compared against this row."
FIX_NOTE = ("The rows below the first shipped row were added after it missed the ship bar. A fix runs on its own "
            "later commit, with shipped re-run beside it on that commit, and is compared against that re-run. The "
            "rows above are left as they were.")
NO_GAIN = " — no measurable gain."

# (key in run.json, heading, format): "count" shows a share as x / n questions
PAGE_COLUMNS = [
    ("refusal_recall", "trick questions refused", "count"),
    ("false_refusals", "false refusals", "count"),
    ("hit@ctx", "hit@ctx", "share"),
    ("cite_precision", "cite precision", "share"),
    ("answer_correct", "answer correct", "share"),
    ("total_p50", "total p50", "s"),
]
ALL_COLUMNS = [
    ("recall@20", "share"), ("full@20", "share"), ("hit@ctx", "share"), ("full@ctx", "share"),
    ("cite_precision", "share"), ("cite_full", "share"), ("coverage", "share"), ("answer_correct", "share"),
    ("refusal_recall", "share"), ("false_refusals", "share"),
    ("passages_p50", "ms"), ("total_p50", "ms"), ("total_p95", "ms"),
]

HEADLINE_START = "<!-- headline:start (generated from evals/runs, do not edit) -->"
HEADLINE_END = "<!-- headline:end -->"
LADDER_START = "<!-- ladder:start (generated from evals/runs, do not edit) -->"
LADDER_END = "<!-- ladder:end -->"


class ResultsError(Exception):
    """The README is missing a generated block's markers."""


# ── selecting runs ────────────────────────────────────────────────────────────────────────────

def _tests(records: list[dict]) -> list[dict]:
    return sorted((r for r in records if r["header"]["split"] == "test"), key=lambda r: r["header"]["date"])


def _sha(rec: dict) -> str:
    return rec["header"]["git"]["sha"]


def fixes(records: list[dict]) -> list[tuple[dict, dict | None]]:
    """Each fix rung's latest test run, with the `shipped` re-run on its SHA (None if there isn't one)."""
    latest = {r["header"]["rung"]: r for r in _tests(records) if r["header"]["rung"] in FIX}
    shipped = [r for r in _tests(records) if r["header"]["rung"] == "shipped"]
    return [(latest[f], next((s for s in reversed(shipped) if _sha(s) == _sha(latest[f])), None))
            for f in FIX if f in latest]


def select(records: list[dict]) -> dict[str, dict]:
    """The latest test-split run of each ladder and side rung. A `shipped` run on a fix rung's SHA is that
    fix rung's comparison, never the ladder's `shipped` row: rows are appended, not edited."""
    fix_shas = {_sha(f) for f, _ in fixes(records)}
    latest: dict[str, dict] = {}
    for r in _tests(records):
        rung = r["header"]["rung"]
        if rung not in FIX and not (rung == "shipped" and _sha(r) in fix_shas):
            latest[rung] = r
    return latest


def final_shipped(records: list[dict]) -> dict | None:
    """The last `shipped*` rung: the one the ship bar is about (LADDER.md: the table is done when it passes)."""
    pairs = fixes(records)
    return pairs[-1][0] if pairs else select(records).get("shipped")


def public(records: list[dict]) -> dict | None:
    """What the public app serves: the last fix rung that passed the bar (it is switched on only then), else
    the ladder's `shipped`."""
    passed = [fix for fix, _ in fixes(records) if not ship_bar(fix["scores"]["columns"])]
    return passed[-1] if passed else select(records).get("shipped")


def ship_bar(cols: dict) -> list[str]:
    """The checks `shipped` misses (evals/LADDER.md, "Ship bar"); empty means it passes. The
    contradicted check needs the judge's `answer_correct.contradicted` count; unjudged never passes."""
    v = lambda name: cols.get(name, {}).get("value")  # noqa: E731
    contradicted = cols.get("answer_correct", {}).get("contradicted")
    checks = [
        (v("false_refusals") == 0, "false refusals on test"),
        (v("refusal_recall") is not None and v("refusal_recall") >= 6 / 7 - 1e-9, "refusal recall under 6 of 7"),
        (v("cite_precision") is not None and v("cite_precision") >= 0.9, "cite precision under 0.9"),
        (contradicted == 0, "not judged yet" if contradicted is None else "a contradicted key fact"),
        (v("total_p50") is not None and v("total_p50") < 5000, "total p50 not under 5 s"),
    ]
    return [msg for ok, msg in checks if not ok]


# ── formatting ────────────────────────────────────────────────────────────────────────────────

def _count(col: dict) -> str:
    """A share as questions out of n; a mean of 3 runs can land between whole questions."""
    x = col["value"] * col["n"]
    return f"{x:.0f}" if abs(x - round(x)) < 1e-9 else f"{x:.1f}"


def _fmt(col: dict | None, kind: str) -> str:
    if not col or col.get("value") is None:
        return "–"
    v = col["value"]
    if kind == "count":
        return f"{_count(col)} / {col['n']}"
    if kind == "s":
        return f"{v / 1000:.1f} s"
    if kind == "ms":
        return f"{v:,.0f} ms"
    return f"{v:.2f}"


def _cell(col: dict | None, base: dict | None, key: str, kind: str) -> dict:
    """Display text, and against the comparison row: `gain` beyond the spread, `same` for a change
    inside it. An unchanged value, a loss or a missing value gets no mark."""
    mark = None
    if col and base and col.get("value") is not None and base.get("value") is not None and col["value"] != base["value"]:
        mark = {"better": "gain", "≈": "same"}.get(compare(col, base, key))
    return {"text": _fmt(col, kind), "mark": mark}


def _n(rows: list[dict], key: str) -> str:
    """The n under a heading: one number when every row scored the same questions, else the range."""
    ns = sorted({r["scores"]["columns"][key]["n"] for r in rows if key in r["scores"]["columns"]})
    if not ns:
        return "–"
    return str(ns[0]) if len(ns) == 1 else f"{ns[0]}–{ns[-1]}"


# ── the page data, from which the markdown is also drawn ──────────────────────────────────────

def page_data(records: list[dict], agreement: dict | None = None) -> dict:
    runs = select(records)
    ladder = [runs[r] for r in LADDER if r in runs]
    side = [runs[r] for r in SIDE if r in runs]
    shipped = runs.get("shipped")
    final = final_shipped(records)
    cols = lambda rec: rec["scores"]["columns"]  # noqa: E731
    if agreement:
        missed = sum(d["human"] == "contradicted" != d["judge"] for d in agreement.get("disagreements", []))
        agreement = ({"agree": agreement["agree"], "total": agreement["total"], "contradictionsMissed": missed}
                     if audits(agreement, shipped) else None)

    def row(rec: dict, base: dict | None, first: bool, why: str | None = None) -> dict:
        rung = rec["header"]["rung"]
        cells = [_cell(cols(rec).get(k), base and cols(base).get(k), k, kind) for k, _, kind in PAGE_COLUMNS]
        why = why or WHY[rung]
        if not first and not any(c["mark"] == "gain" for c in cells):
            why = why.rstrip(".") + NO_GAIN
        return {"rung": rung, "why": why, "highlight": rec is final and not ship_bar(cols(rec)),
                "run": rec["header"]["run_id"], "cells": cells}

    fix_recs, fix_rows = [], []
    for fix, rerun in fixes(records):
        if rerun:
            fix_recs.append(rerun)
            fix_rows.append(row(rerun, None, True, RERUN_WHY.format(sha=_sha(rerun)[:7])))
        fix_recs.append(fix)
        fix_rows.append(row(fix, rerun, rerun is None))

    live = public(records)
    trick = cols(live)["refusal_recall"] if live else None
    counts = cols(shipped or (ladder + side)[0]) if (ladder or side) else None
    data = {
        "intro": counts and {"questions": counts["refusal_recall"]["n"] + counts["false_refusals"]["n"],
                             "refuse": counts["refusal_recall"]["n"]},
        "headerLink": f"Evals · {_count(trick)}/{trick['n']} trick questions refused" if trick else "Evals",
        "columns": [{"key": k, "label": label, "n": _n(ladder + fix_recs + side, k)} for k, label, _ in PAGE_COLUMNS],
        "ladder": [row(rec, ladder[i - 1] if i else None, i == 0) for i, rec in enumerate(ladder)] + fix_rows,
        "side": [row(rec, shipped, False) for rec in side],
        "shipBar": final and {"rung": final["header"]["rung"], "unmet": ship_bar(cols(final))},
        "agreement": agreement,
        "fixNote": FIX_NOTE if fix_rows else None,
    }
    return {**data, "underTable": under_table(agreement)}


def audits(agreement: dict, shipped: dict | None) -> bool:
    """An audit only vouches for the judge it audited: a changed judge model or prompt needs a fresh one."""
    judge = shipped and shipped["header"].get("judge")
    if not judge or "judge" not in agreement:
        return True
    return all(agreement["judge"].get(k) == judge.get(k) for k in ("model", "prompt_hash"))


def under_table(a: dict | None) -> str:
    """The spread rule and the judge/human agreement line, shown under the main ladder."""
    missed = (a or {}).get("contradictionsMissed", 0)
    graded = ("Answers were graded by Sonnet 5 against key facts written with the questions; "
              + (f"on the first full run a human grader, blind to its verdicts, agreed with it on {a['agree']} of "
                 f"{a['total']} facts ({a['agree'] / a['total']:.0%})" if a else "the judge/human audit isn't committed yet")
              + (f", and marked {missed} {'fact' if missed == 1 else 'facts'} contradicted that the judge passed, "
                 "which the ship bar's contradicted check doesn't see." if missed else "."))
    return ("Generation columns are the mean of 3 runs. A row only counts as better when the gain is bigger than "
            "its own run-to-run spread; ≈ marks changes inside it. " + graded
            + " Cite precision counts a cited definition the app attached as correct; that rule was added after "
              "the first full run, when the citations outside gold turned out to be mostly definitions written "
              "after the gold was (0.69 → 0.78 for shipped), and applies to every row.")


# ── markdown ──────────────────────────────────────────────────────────────────────────────────

def _md_cell(c: dict) -> str:
    return f"**{c['text']}**" if c["mark"] == "gain" else (f"≈ {c['text']}" if c["mark"] == "same" else c["text"])


def _md_table(data: dict, rows: list[dict]) -> list[str]:
    head = "| Rung | " + " | ".join(f"{c['label']}<br><sub>n {c['n']}</sub>" for c in data["columns"]) + " |"
    lines = [head, "|" + " --- |" * (len(data["columns"]) + 1)]
    for r in rows:
        name = f"**`{r['rung']}`** ✓ ship bar" if r["highlight"] else f"`{r['rung']}`"
        lines.append(f"| {name}<br><sub>{r['why']}</sub> | " + " | ".join(_md_cell(c) for c in r["cells"]) + " |")
    return lines


def headline_block(records: list[dict], data: dict) -> str:
    """Vector search only (`dense`) against what the public app serves, for the README's first screen."""
    runs, final = select(records), public(records)
    pick = [("vector search only", runs.get("dense"), False), (final["header"]["rung"] if final else "shipped", final, True)]
    lines = [HEADLINE_START, "| | refuses trick questions | cite precision | answer correct |", "| --- | --- | --- | --- |"]
    for label, rec, bold in pick:
        c = rec["scores"]["columns"] if rec else {}
        cells = [_fmt(c.get("refusal_recall"), "count"), _fmt(c.get("cite_precision"), "share"), _fmt(c.get("answer_correct"), "share")]
        b = (lambda s: f"**{s}**") if bold else (lambda s: s)
        lines.append(f"| {b(label)} | " + " | ".join(b(x) for x in cells) + " |")
    if data["intro"]:
        lines += ["", f"{data['intro']['questions']} questions written before the first build; full ladder below."]
    lines.append(HEADLINE_END)
    return "\n".join(lines)


def ladder_block(data: dict) -> str:
    lines = [LADDER_START]
    if not data["ladder"] and not data["side"]:
        lines += ["No test-split run is committed yet.", LADDER_END]
        return "\n".join(lines)
    lines += [f"{data['intro']['questions']} questions written before the first build, {data['intro']['refuse']} of them "
              "meant to be refused. Each row adds one thing to the row above, all run on the same final code.", ""]
    lines += _md_table(data, data["ladder"]) + [""]
    if data["fixNote"]:
        lines += [data["fixNote"], ""]
    lines += [data["underTable"], ""]
    if data["side"]:
        lines += ["Alternatives tried against `shipped`, one change each.", ""] + _md_table(data, data["side"]) + [""]
    lines.append(LADDER_END)
    return "\n".join(lines)


def results_md(records: list[dict], data: dict) -> str:
    runs, pairs = select(records), fixes(records)
    ladder = [runs[r] for r in LADDER if r in runs]
    fix_recs = [rec for fix, rerun in pairs for rec in (rerun, fix) if rec]
    side = [runs[r] for r in SIDE if r in runs]
    recs = ladder + fix_recs + side
    lines = ["# Eval results", "",
             "Generated by `python -m evals results` from `evals/runs/*/run.json` (latest `split: test` run of each "
             "rung). Never hand-edited. Columns are defined in [`EVALS.md`](../EVALS.md#columns); rungs in "
             "[`LADDER.md`](LADDER.md).", ""]
    if not recs:
        return "\n".join(lines + ["No test-split run is committed yet.", ""])

    # the ladder and side table share one SHA; each fix pair shares its own (LADDER.md, "How it runs")
    shas = sorted({_sha(r)[:7] for r in ladder + side})
    fix_shas = sorted({_sha(r)[:7] for r in fix_recs} - set(shas))
    first = recs[0]["header"]
    lines += [f"Git {', '.join(f'`{s}`' for s in shas)}"
              + (f" · fix rungs on {', '.join(f'`{s}`' for s in fix_shas)}" if fix_shas else "")
              + f" · snapshot `{first['snapshot']['id']}` · threshold {first['threshold']} · {first['runs']} runs per rung", ""]
    if len(shas) > 1:
        lines += ["> **The rungs span more than one git SHA:** the ladder is meant to run in one sitting on one SHA.", ""]
    for fix, rerun in pairs:
        if rerun is None:
            lines += [f"> **`{fix['header']['rung']}` has no `shipped` re-run on its SHA** to be compared against.", ""]

    reruns = {id(rerun) for _, rerun in pairs if rerun}
    name = lambda r: f"`{r['header']['rung']}`" + (" re-run" if id(r) in reruns else "")  # noqa: E731
    headings = [k.replace("_", " ") for k, _ in ALL_COLUMNS]
    sep = "|" + " --- |" * (len(ALL_COLUMNS) + 2)
    table = lambda cell: ["| Rung | " + " | ".join(headings) + " | Run |", sep] + [  # noqa: E731
        f"| {name(r)} | " + " | ".join(cell(r["scores"]["columns"].get(k), kind) for k, kind in ALL_COLUMNS)
        + f" | `{r['header']['run_id']}` |" for r in recs]
    lines += table(_fmt) + [""]
    lines += ["## n scored", ""] + table(lambda c, _: "–" if not c else str(c["n"])) + [""]
    lines += ["## Run-to-run spread", "",
              "Max − min over the runs. Retrieval columns come from run 1 only, so they have none.", ""]
    lines += table(lambda c, kind: "–" if not c or c.get("spread") is None else _fmt({"value": c["spread"]}, kind)) + [""]

    lines += ["## Ship bar", ""]
    bars = [r for r in [runs.get("shipped")] + [fix for fix, _ in pairs] if r]
    if not bars:
        lines.append("No `shipped` run yet.")
    for r in bars:
        unmet = ship_bar(r["scores"]["columns"])
        lines += [f"`{r['header']['rung']}`: " + ("passes." if not unmet else "misses: " + "; ".join(unmet) + "."), ""]
    if bars:
        lines.pop()
    lines += ["", "## Judge", "", data["underTable"], ""]
    return "\n".join(lines)


def replace_block(md: str, start: str, end: str, block: str) -> str:
    pattern = re.compile(re.escape(start) + ".*?" + re.escape(end), re.S)
    if not pattern.search(md):
        raise ResultsError(f"README.md has no {start} … {end} block")
    return pattern.sub(lambda _: block, md)


def readme(md: str, records: list[dict], data: dict) -> str:
    md = replace_block(md, HEADLINE_START, HEADLINE_END, headline_block(records, data))
    return replace_block(md, LADDER_START, LADDER_END, ladder_block(data))


# ── I/O ───────────────────────────────────────────────────────────────────────────────────────

def load(runs_dir: Path = RUNS_DIR) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(runs_dir.glob("*/run.json"))]


def apply(runs_dir: Path = RUNS_DIR, results: Path = RESULTS_MD, readme_md: Path = README_MD,
          page: Path = PAGE_JSON, agreement: Path = AGREEMENT_JSON) -> dict:
    records = load(runs_dir)
    data = page_data(records, json.loads(agreement.read_text(encoding="utf-8")) if agreement.exists() else None)
    results.write_text(results_md(records, data), encoding="utf-8")
    readme_md.write_text(readme(readme_md.read_text(encoding="utf-8"), records, data), encoding="utf-8")
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return data
