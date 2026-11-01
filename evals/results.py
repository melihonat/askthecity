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
SIDE = ["side-sonnet", "side-quoted"]
WHY = {
    "dense": "Vector search only: embed the question, take the 5 closest passages.",
    "hybrid": 'Adds keyword search and exact section-number matching, so "591-2.1" finds § 591-2.1.',
    "rerank": "A reranker scores every passage against the question; if none scores high enough, it refuses before the model writes anything.",
    "shipped": "Brings in the by-laws that amended a cited section after the Code was last consolidated.",
    "side-sonnet": "Sonnet 5.5 instead of Haiku 5.5, at ~20× the generation cost.",
    "side-quoted": "Asks the model to quote the supporting sentence for every citation.",
}
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

def select(records: list[dict]) -> dict[str, dict]:
    """The latest test-split run of each rung."""
    latest: dict[str, dict] = {}
    for r in sorted((r for r in records if r["header"]["split"] == "test"), key=lambda r: r["header"]["date"]):
        latest[r["header"]["rung"]] = r
    return latest


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
    cols = lambda rec: rec["scores"]["columns"]  # noqa: E731
    if agreement:
        agreement = {"agree": agreement["agree"], "total": agreement["total"]} if audits(agreement, shipped) else None

    def row(rec: dict, base: dict | None, first: bool) -> dict:
        rung = rec["header"]["rung"]
        cells = [_cell(cols(rec).get(k), base and cols(base).get(k), k, kind) for k, _, kind in PAGE_COLUMNS]
        why = WHY[rung]
        if not first and not any(c["mark"] == "gain" for c in cells):
            why = why.rstrip(".") + NO_GAIN
        return {"rung": rung, "why": why, "highlight": rung == "shipped" and not ship_bar(cols(rec)),
                "run": rec["header"]["run_id"], "cells": cells}

    trick = cols(shipped)["refusal_recall"] if shipped else None
    counts = cols(shipped or (ladder + side)[0]) if (ladder or side) else None
    data = {
        "intro": counts and {"questions": counts["refusal_recall"]["n"] + counts["false_refusals"]["n"],
                             "refuse": counts["refusal_recall"]["n"]},
        "headerLink": f"Evals · {_count(trick)}/{trick['n']} trick questions refused" if trick else "Evals",
        "columns": [{"key": k, "label": label, "n": _n(ladder + side, k)} for k, label, _ in PAGE_COLUMNS],
        "ladder": [row(rec, ladder[i - 1] if i else None, i == 0) for i, rec in enumerate(ladder)],
        "side": [row(rec, shipped, False) for rec in side],
        "shipBar": shipped and {"rung": "shipped", "unmet": ship_bar(cols(shipped))},
        "agreement": agreement,
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
    graded = ("Answers were graded by Sonnet 5 against key facts written with the questions; "
              + (f"on the first full run it agreed with my hand grading on {a['agree']} of {a['total']} facts "
                 f"({a['agree'] / a['total']:.0%})." if a else "the judge/human audit isn't committed yet."))
    return ("Generation columns are the mean of 3 runs. A row only counts as better when the gain is bigger than "
            "its own run-to-run spread; ≈ marks changes inside it. " + graded)


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
    """Vector search only (`dense`) against `shipped`, for the README's first screen."""
    runs = select(records)
    pick = [("vector search only", runs.get("dense"), False), ("shipped", runs.get("shipped"), True)]
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
    lines += _md_table(data, data["ladder"]) + ["", data["underTable"], ""]
    if data["side"]:
        lines += ["Alternatives tried against `shipped`, one change each.", ""] + _md_table(data, data["side"]) + [""]
    lines.append(LADDER_END)
    return "\n".join(lines)


def results_md(records: list[dict], data: dict) -> str:
    runs = select(records)
    recs = [runs[r] for r in LADDER + SIDE if r in runs]
    lines = ["# Eval results", "",
             "Generated by `python -m evals results` from `evals/runs/*/run.json` (latest `split: test` run of each "
             "rung). Never hand-edited. Columns are defined in [`EVALS.md`](../EVALS.md#columns); rungs in "
             "[`LADDER.md`](LADDER.md).", ""]
    if not recs:
        return "\n".join(lines + ["No test-split run is committed yet.", ""])

    shas = sorted({r["header"]["git"]["sha"][:7] for r in recs})
    first = recs[0]["header"]
    lines += [f"Git {', '.join(f'`{s}`' for s in shas)} · snapshot `{first['snapshot']['id']}` · threshold {first['threshold']} · "
              f"{first['runs']} runs per rung", ""]
    if len(shas) > 1:
        lines += ["> **The rungs span more than one git SHA:** the ladder is meant to run in one sitting on one SHA.", ""]

    headings = [k.replace("_", " ") for k, _ in ALL_COLUMNS]
    sep = "|" + " --- |" * (len(ALL_COLUMNS) + 2)
    table = lambda cell: ["| Rung | " + " | ".join(headings) + " | Run |", sep] + [  # noqa: E731
        f"| `{r['header']['rung']}` | " + " | ".join(cell(r["scores"]["columns"].get(k), kind) for k, kind in ALL_COLUMNS)
        + f" | `{r['header']['run_id']}` |" for r in recs]
    lines += table(_fmt) + [""]
    lines += ["## n scored", ""] + table(lambda c, _: "–" if not c else str(c["n"])) + [""]
    lines += ["## Run-to-run spread", "",
              "Max − min over the runs. Retrieval columns come from run 1 only, so they have none.", ""]
    lines += table(lambda c, kind: "–" if not c or c.get("spread") is None else _fmt({"value": c["spread"]}, kind)) + [""]

    lines += ["## Ship bar", ""]
    bar = data["shipBar"]
    if bar is None:
        lines.append("No `shipped` run yet.")
    else:
        lines.append(f"`{bar['rung']}`: " + ("passes." if not bar["unmet"] else "misses: " + "; ".join(bar["unmet"]) + "."))
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
