"""report.md for one rung run (EVALS.md, "Files"): the columns, then what needs a human look."""
from __future__ import annotations

import statistics

COLUMNS = [
    ("recall@20", "share"), ("full@20", "share"), ("hit@ctx", "share"), ("full@ctx", "share"),
    ("cite_precision", "ratio"), ("cite_full", "share"), ("coverage", "ratio"),
    ("refusal_recall", "share"), ("false_refusals", "share"),
    ("passages_p50", "ms"), ("total_p50", "ms"), ("total_p95", "ms"),
]


def _fmt(value, kind: str) -> str:
    if value is None:
        return "–"
    return f"{value:,.0f} ms" if kind == "ms" else f"{value:.2f}"


def render(head: dict, scores: dict, data: dict[str, list[dict]]) -> str:
    cols = scores["columns"]
    lines = [
        f"# {head['run_id']}",
        "",
        f"Rung `{head['rung']}` · split `{head['split']}` · {head['runs']} runs · {head['base_url']}  ",
        f"Git `{head['git']['sha'][:7]}`{' (dirty)' if head['git']['dirty'] else ''} · deployed `{(head['deployed_sha'] or 'unknown')[:7]}` · "
        f"snapshot `{head['snapshot']['id']}` · prompt `{head['prompt']['version']}` ({head['prompt']['hash']}) · threshold {head['threshold']}",
        "",
    ]
    if head["deployed_sha"] and head["deployed_sha"] != head["git"]["sha"]:
        lines += ["> **The deployed SHA differs from the local one:** this run measures the deployed code.", ""]

    lines += ["| Column | Value | n | Spread |", "| --- | --- | --- | --- |"]
    for name, kind in COLUMNS:
        c = cols[name]
        spread = "–" if c.get("spread") is None else _fmt(c["spread"], kind)
        lines.append(f"| {name} | {_fmt(c['value'], kind)} | {c['n']} | {spread} |")
    lines += ["", "Answer correctness (judge) is not scored yet.", ""]

    spend = head["spend"]
    lines.append(f"Gateway spend (tag `eval:{head['run_id']}`): "
                 + (f"${spend['usd']:.4f} over {spend.get('requests')} requests" if spend.get("usd") is not None else f"not read back ({spend.get('error')})"))
    walls = [c["wall_ms"] for calls in data.values() for c in calls]
    lines += [f"Harness wall-clock p50: {statistics.median(walls):,.0f} ms, from the machine that ran the harness (not the function region).", ""]

    lines += _section("Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)",
                      [f"`{qid}`" for qid in scores["retrieval_mismatch"]])
    lines += _section("Stale gold (dropped from retrieval and citation columns)",
                      [f"`{s['id']}`: " + ", ".join(" | ".join(g) for g in s["groups"]) for s in scores["stale"]])
    lines += _section("Unstable questions (outcome differed across runs)",
                      [f"`{u['id']}`: " + " → ".join(u["outcomes"]) for u in scores["unstable"]])
    lines += _section("Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)",
                      [f"`{o['id']}` run {o['run']}: `{o['chunkId']}`" for o in scores["off_gold"]])
    r = scores["refusals"]
    lines += _section("Refusal reasons", [
        "Answer questions refused: " + (", ".join(f"{k} × {v}" for k, v in r["false_refusals"].items()) or "none"),
        "Refuse questions: " + (", ".join(f"{k} × {v}" for k, v in r["refuse_questions"].items()) or "none"),
    ])
    lines += _section("Pinned questions (a § number matched)", [f"`{qid}`" for qid in scores["pinned"]])
    return "\n".join(lines).rstrip() + "\n"


def _section(title: str, items: list[str]) -> list[str]:
    return [f"## {title}", "", *([f"- {i}" for i in items] or ["None."]), ""]
