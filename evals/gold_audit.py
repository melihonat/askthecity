"""The gold audit (#56): review citations outside gold, widen `acceptable` from the accepted ones.

`sheet` writes evals/gold_audit.csv: one row per distinct (question, chunk) cited outside
`required`/`acceptable` in any committed test-split run, with the sentences that cite it and a
link to the chunk's page on toronto.ca (chunk text stays out of the repo, CORPUS.md). Fill `decision` with accept / reject (a / r also work): accept only when the passage
itself states the sentence. Accepted chunks go into that question's `acceptable` by hand.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from .score import _acceptable
from .sentences import split_sentences

ROOT = Path(__file__).resolve().parent.parent
SHEET = ROOT / "evals" / "gold_audit.csv"
FIELDS = ["question_id", "chunk_id", "cites", "rungs", "question", "sentences", "href", "decision", "note"]


class GoldAuditError(Exception):
    pass


def _citing_sentences(text: str, n: int) -> list[str]:
    marker = re.compile(rf"\[{n}\]")
    return [s for s in split_sentences(text) if marker.search(s)]


def rows(records: list[dict], gold: dict[str, dict]) -> list[dict]:
    """Off-gold citations across `records`, grouped by (question, chunk), most cited first."""
    seen: dict[tuple[str, str], dict] = {}
    for record in records:
        rung = record["header"]["rung"]
        stale = {s["id"] if isinstance(s, dict) else s for s in record["scores"].get("stale") or []}
        for q in record["questions"]:
            if q["id"] in stale or q["id"] not in gold or gold[q["id"]]["expect"] != "answer":
                continue
            for call in q["runs"]:
                response = call["response"]
                if response["kind"] != "answer":
                    continue
                for c in response["citations"]:
                    if _acceptable(c["chunkId"], gold[q["id"]], response):
                        continue
                    row = seen.setdefault((q["id"], c["chunkId"]), {"cites": 0, "rungs": set(), "sentences": [], "href": ""})
                    row["cites"] += 1
                    row["href"] = next(p["href"] for p in response["passages"] if p["chunkId"] == c["chunkId"])
                    row["rungs"].add(rung)
                    row["sentences"] += [s for s in _citing_sentences(response["text"], c["n"]) if s not in row["sentences"]]
    out = [{"question_id": qid, "chunk_id": cid, "cites": r["cites"], "rungs": " ".join(sorted(r["rungs"])),
            "question": gold[qid]["question"], "sentences": "\n".join(r["sentences"]),
            "href": r["href"], "decision": "", "note": ""}
           for (qid, cid), r in seen.items()]
    return sorted(out, key=lambda r: (r["question_id"], -r["cites"], r["chunk_id"]))


# ── I/O ───────────────────────────────────────────────────────────────────────────────────────

def write_sheet(runs_dir: Path, gold: list[dict], out: Path = SHEET) -> int:
    if out.exists():
        raise GoldAuditError(f"{out.name} exists; review decisions are never overwritten")
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(runs_dir.glob("*/run.json"))]
    records = [r for r in records if r["header"]["split"] == "test"]
    sheet = rows(records, {q["id"]: q for q in gold})
    with out.open("w", encoding="utf-8-sig", newline="") as f:  # the BOM lets Excel read UTF-8
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(sheet)
    return len(sheet)
