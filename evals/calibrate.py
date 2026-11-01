"""The calibrate step (EVALS.md, "Refusal threshold"): threshold = 0.5 × the lowest gate score among
un-pinned `split: dev` answer questions, from one committed dev run. Pure: the run record and the
gold in, the threshold and its table out. `apply` writes them into EVALS.md and the app config.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

MARGIN = 0.5
EVALS_MD = Path(__file__).resolve().parent.parent / "EVALS.md"
CONFIG_TS = Path(__file__).resolve().parent.parent / "lib" / "ask" / "config.ts"
TABLE_START = "<!-- calibrate:start -->"
TABLE_END = "<!-- calibrate:end -->"


class CalibrationError(Exception):
    """The run can't calibrate the gate."""


def _outcome(response: dict) -> str:
    return response["kind"] if response["kind"] == "answer" else response["reason"]


def calibrate(record: dict, gold: list[dict]) -> dict:
    """{threshold, lowest, rows}. A row per dev question: its lowest gate score across runs (rerank
    scores jitter in the 4th decimal; the lowest is the cautious one), the spread, whether a pin
    fired, and its outcome per run."""
    head = record["header"]
    if head["split"] != "dev":
        raise CalibrationError(f"split `{head['split']}`: the threshold is never tuned on test")
    if not head["config"]["rerank"]:
        raise CalibrationError(f"rung `{head['rung']}` has no reranker, so no gate scores")

    expect = {q["id"]: q["expect"] for q in gold}
    rows = []
    for q in record["questions"]:
        scores = [r["debug"]["gateScore"] for r in q["runs"]]
        outcomes = Counter(_outcome(r["response"]) for r in q["runs"])
        rows.append({
            "id": q["id"],
            "expect": expect[q["id"]],
            "gate_score": min(scores),
            "spread": max(scores) - min(scores),
            "pinned": any(r["debug"]["gateBypassed"] for r in q["runs"]),
            "outcome": ", ".join(f"{o} ×{n}" for o, n in sorted(outcomes.items())),
        })

    answers = [r["gate_score"] for r in rows if r["expect"] == "answer" and not r["pinned"]]
    if not answers:
        raise CalibrationError("no un-pinned dev answer question")
    lowest = min(answers)
    # floored to 3 places, so rounding never lifts the threshold
    threshold = math.floor(MARGIN * lowest * 1000) / 1000
    rows.sort(key=lambda r: (r["expect"], -r["gate_score"]))
    return {"run_id": head["run_id"], "date": head["date"][:10], "lowest": lowest, "threshold": threshold, "rows": rows}


def render(result: dict) -> str:
    lines = [
        TABLE_START,
        f"Generated {result['date']} by `python -m evals calibrate` from run `{result['run_id']}`: "
        f"lowest un-pinned dev answer gate score {result['lowest']:.3f} → **threshold {result['threshold']}**.",
        "",
        "| Dev question | Expect | Gate score (lowest) | Spread | Pinned | Outcome (3 runs) | Gate at threshold |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in result["rows"]:
        gated = "bypassed" if r["pinned"] else ("refuses" if r["gate_score"] < result["threshold"] else "passes")
        lines.append(f"| `{r['id']}` | {r['expect']} | {r['gate_score']:.3f} | {r['spread']:.4f} | {'yes' if r['pinned'] else 'no'} "
                     f"| {r['outcome']} | {gated} |")
    lines.append(TABLE_END)
    return "\n".join(lines)


def replace_table(md: str, table: str) -> str:
    pattern = re.compile(re.escape(TABLE_START) + ".*?" + re.escape(TABLE_END), re.S)
    if not pattern.search(md):
        raise CalibrationError(f"EVALS.md has no {TABLE_START} … {TABLE_END} block")
    return pattern.sub(lambda _: table, md)


def replace_threshold(ts: str, threshold: float) -> str:
    out, n = re.subn(r"export const REFUSAL_THRESHOLD = [0-9.]+;", f"export const REFUSAL_THRESHOLD = {threshold};", ts)
    if n != 1:
        raise CalibrationError("lib/ask/config.ts: expected one REFUSAL_THRESHOLD")
    return out


def apply(result: dict, evals_md: Path = EVALS_MD, config_ts: Path = CONFIG_TS) -> None:
    evals_md.write_text(replace_table(evals_md.read_text(encoding="utf-8"), render(result)), encoding="utf-8")
    config_ts.write_text(replace_threshold(config_ts.read_text(encoding="utf-8"), result["threshold"]), encoding="utf-8")
