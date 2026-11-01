"""The judge/human audit (EVALS.md, "Answer judge"): hand-score one run's key facts blind, then
compare with the judge.

`sheet` writes evals/judge_audit.csv: one row per key fact of every judged answer in the chosen
runs, without the judge's verdict. Fill the `human` column with present / absent / contradicted
(p / a / c also work). `agreement` reads it back, compares with the run's verdicts and writes
evals/judge_agreement.json, which the results renderer shows under the table.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "evals" / "judge_audit.csv"
AGREEMENT = ROOT / "evals" / "judge_agreement.json"
FIELDS = ["run_id", "question_id", "run", "fact", "question", "key_fact", "answer", "human"]
SHORT = {"p": "present", "a": "absent", "c": "contradicted"}


class AuditError(Exception):
    pass


def rows(record: dict, gold: dict[str, dict], runs: list[int]) -> list[dict]:
    out = []
    for q in record["questions"]:
        for run, call in enumerate(q["runs"], 1):
            if run not in runs or "judge" not in call:
                continue
            g = gold[q["id"]]
            out += [{"run_id": record["header"]["run_id"], "question_id": q["id"], "run": run, "fact": i,
                     "question": g["question"], "key_fact": fact, "answer": call["response"]["text"], "human": ""}
                    for i, fact in enumerate(g["key_facts"], 1)]
    return out


def compare(record: dict, sheet: list[dict]) -> dict:
    """Agreement of the hand verdicts with the run's judge verdicts, fact by fact."""
    verdicts = {(q["id"], run, v["fact"]): v["verdict"]
                for q in record["questions"] for run, call in enumerate(q["runs"], 1) for v in call.get("judge") or []}
    agree, disagreements = 0, []
    for r in sheet:
        if r["run_id"] != record["header"]["run_id"]:
            raise AuditError(f"row for run {r['run_id']}, expected {record['header']['run_id']}")
        human = SHORT.get(r["human"].strip().lower(), r["human"].strip().lower())
        if human not in SHORT.values():
            raise AuditError(f"{r['question_id']} run {r['run']} fact {r['fact']}: human verdict {r['human']!r}")
        judge = verdicts[(r["question_id"], int(r["run"]), int(r["fact"]))]
        if human == judge:
            agree += 1
        else:
            disagreements.append({"id": r["question_id"], "run": int(r["run"]), "fact": int(r["fact"]), "human": human, "judge": judge})
    return {"agree": agree, "total": len(sheet), "run": record["header"]["run_id"], "judge": record["header"]["judge"],
            "disagreements": disagreements}


# ── I/O ───────────────────────────────────────────────────────────────────────────────────────

def write_sheet(run_dir: Path, gold: list[dict], runs: list[int], out: Path = SHEET) -> int:
    if out.exists():
        raise AuditError(f"{out.name} exists; hand scores are never overwritten")
    record = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    if not record["header"].get("judge"):
        raise AuditError(f"{run_dir.name} wasn't judged")
    sheet = rows(record, {q["id"]: q for q in gold}, runs)
    with out.open("w", encoding="utf-8-sig", newline="") as f:  # the BOM lets Excel read UTF-8
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(sheet)
    return len(sheet)


def apply(runs_dir: Path, sheet: Path = SHEET, out: Path = AGREEMENT) -> dict:
    with sheet.open(encoding="utf-8-sig", newline="") as f:
        filled = list(csv.DictReader(f))
    if not filled:
        raise AuditError(f"{sheet.name} has no rows")
    run_id = filled[0]["run_id"]
    path = next((p for p in runs_dir.glob("*/run.json") if json.loads(p.read_text(encoding="utf-8"))["header"]["run_id"] == run_id), None)
    if path is None:
        raise AuditError(f"no committed run {run_id}")
    result = compare(json.loads(path.read_text(encoding="utf-8")), filled)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return result
