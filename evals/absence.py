"""False absence claims (#57): answer sentences saying the documents don't state something that a
passage in the answer's own context does state.

`check` finds each answer's absence sentences and asks a pinned Sonnet 5 (the judge's model and key)
whether a passage states the thing. A `false` verdict must quote that passage; the quote is checked
word for word, and an unfound quote doesn't count as false. Verdicts go to evals/absence/<run>.json:
sentences and short quotes, never passage bodies (CORPUS.md).

`sheet` writes evals/absence_review.csv for the human check: every `false`, plus a seeded sample of
`true`. Fill `human` with true / false (t / f also work).
"""
from __future__ import annotations

import csv
import hashlib
import json
import random
import re
from pathlib import Path
from typing import Protocol

from .judge import MODEL
from .sentences import split_sentences

ROOT = Path(__file__).resolve().parent.parent
PROMPT = ROOT / "evals" / "absence_prompt.md"
OUT_DIR = ROOT / "evals" / "absence"
SHEET = ROOT / "evals" / "absence_review.csv"
PROMPT_VERSION = "1"             # bump with any change to absence_prompt.md; v2 (rejected) is in git history and evals/absence/v2/
MAX_TOKENS = 2000
VERDICTS = ("true", "false")
SAMPLE_TRUE = 30
# The labelled rows of evals/absence_review.csv split by question, balanced on v1 `false` verdicts (32 each),
# fixed before any prompt change: a new checker prompt is tuned on TUNE and measured on the rest.
TUNE = {"amended-summer-cooling", "decisions-electricity-referred", "decisions-laneway-snow", "decisions-tree-size",
        "dev-fireworks-backyard", "dev-leaf-blower", "multi-dead-tree", "multi-reno-hours-idling", "rules-apartment-heat"}
FIELDS = ["run_id", "question_id", "run", "sentence", "verdict", "passage", "href", "span", "human", "note"]

# "the passages do not state", "the documents don't cover", "not addressed in the passages", "no passage …"
ABSENCE = re.compile(
    r"\b(passages?|documents?|sources?|texts?|material|provided)\b[^.]*?\b(do|does|did|is|are)\s*(not|n't)\b"
    r"|\bnot (covered|stated|addressed|mentioned) (in|by)\b|\bno passage\b", re.I)

SCHEMA = {
    "type": "object",
    "properties": {
        "sentences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sentence": {"type": "integer"},
                    "verdict": {"type": "string", "enum": list(VERDICTS)},
                    "passage": {"type": "integer"},
                    "span": {"type": "string"},
                },
                "required": ["sentence", "verdict", "passage", "span"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["sentences"],
    "additionalProperties": False,
}


class AbsenceError(Exception):
    pass


class Checker(Protocol):
    def check(self, question: str, passages: list[dict], answer: str, sentences: list[str]) -> list[dict]: ...


def absence_sentences(text: str) -> list[str]:
    return [s for s in split_sentences(text) if ABSENCE.search(s)]


def prompt_text() -> str:
    return PROMPT.read_text(encoding="utf-8")


def info() -> dict:
    return {"model": MODEL, "prompt_version": PROMPT_VERSION,
            "prompt_hash": hashlib.sha256(prompt_text().encode("utf-8")).hexdigest()[:12]}


def user_message(question: str, passages: list[dict], answer: str, sentences: list[str]) -> str:
    """`passages`: {n, label, body}, as the answer numbered them."""
    ps = "\n\n".join(f"[{p['n']}] {p['label']}\n{p['body']}" for p in passages)
    ss = "\n".join(f"{i}. {s}" for i, s in enumerate(sentences, 1))
    return (f"Question: {question}\n\nPassages:\n<passages>\n{ps}\n</passages>\n\n"
            f"Answer:\n<answer>\n{answer}\n</answer>\n\nAbsence sentences:\n{ss}")


def parse(reply: str, passages: list[dict], sentences: list[str]) -> list[dict]:
    """One verdict per sentence, in order: `{sentence, text, verdict, passage, chunkId, span, span_found}`.
    `span_found` is whether a `false` verdict's quote is in that passage word for word."""
    try:
        items = json.loads(reply)["sentences"]
    except (ValueError, KeyError, TypeError) as e:
        raise AbsenceError(f"unreadable checker reply: {reply[:200]!r}") from e
    if sorted(i.get("sentence") for i in items) != list(range(1, len(sentences) + 1)):
        raise AbsenceError(f"checker returned sentences {[i.get('sentence') for i in items]}, expected 1–{len(sentences)}")
    by_n = {p["n"]: p for p in passages}
    out = []
    for i in sorted(items, key=lambda i: i["sentence"]):
        if i["verdict"] not in VERDICTS:
            raise AbsenceError(f"unknown verdict {i['verdict']!r}")
        p = by_n.get(i["passage"]) if i["verdict"] == "false" else None
        out.append({"sentence": i["sentence"], "text": sentences[i["sentence"] - 1], "verdict": i["verdict"],
                    "passage": i["passage"] if p else 0, "chunkId": p["chunkId"] if p else None,
                    "span": i["span"] if p else "",
                    "span_found": i["verdict"] == "true" or bool(p and i["span"] and i["span"] in p["body"])})
    return out


def is_false(v: dict) -> bool:
    """A false absence claim that counts: the checker said so and its quote was found."""
    return v["verdict"] == "false" and v["span_found"]


class AnthropicChecker:
    """Calls Anthropic directly on JUDGE_ANTHROPIC_API_KEY, never the demo's Gateway credit."""

    def __init__(self, api_key: str):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.system = prompt_text()
        self.usage = {"input_tokens": 0, "output_tokens": 0, "calls": 0}

    def check(self, question: str, passages: list[dict], answer: str, sentences: list[str]) -> list[dict]:
        """One retry on an unusable reply (it has come back with no verdicts once); a second raises."""
        try:
            return self._check(question, passages, answer, sentences)
        except AbsenceError:
            return self._check(question, passages, answer, sentences)

    def _check(self, question: str, passages: list[dict], answer: str, sentences: list[str]) -> list[dict]:
        r = self.client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=self.system,
            thinking={"type": "disabled"},
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": user_message(question, passages, answer, sentences)}],
        )
        self.usage["input_tokens"] += r.usage.input_tokens
        self.usage["output_tokens"] += r.usage.output_tokens
        self.usage["calls"] += 1
        if r.stop_reason != "end_turn":
            raise AbsenceError(f"checker stopped with {r.stop_reason} on {question!r}")
        return parse(next(b.text for b in r.content if b.type == "text"), passages, sentences)


def check_run(record: dict, questions: dict[str, str], bodies: dict[str, str], checker: Checker, log=print,
              only: set[tuple[str, int]] | None = None) -> dict:
    """Every answered call of `record` with an absence sentence, checked. `questions`: id → question text;
    `only`: just these (question id, run) calls."""
    calls = []
    for q in record["questions"]:
        for run, call in enumerate(q["runs"], 1):
            response = call["response"]
            sentences = absence_sentences(response["text"]) if response["kind"] == "answer" else []
            if not sentences or only is not None and (q["id"], run) not in only:
                continue
            passages = [{"n": p["n"], "chunkId": p["chunkId"], "label": p["label"], "body": bodies[p["chunkId"]]}
                        for p in response["passages"]]
            try:
                verdicts = checker.check(questions[q["id"]], passages, response["text"], sentences)
            except AbsenceError as e:  # an unusable reply twice: listed as unchecked, not a verdict
                log(f"  unchecked run {run} {q['id']}: {e}")
                verdicts = [{"sentence": i, "text": s, "verdict": "unchecked", "passage": 0, "chunkId": None, "span": "",
                             "span_found": False} for i, s in enumerate(sentences, 1)]
            calls.append({"id": q["id"], "run": run, "verdicts": verdicts})
            log(f"  checked run {run} {q['id']}: " + ", ".join(v["verdict"] for v in verdicts))
    return {"run_id": record["header"]["run_id"], "checker": info(), "calls": calls, "summary": summary(record, calls)}


def summary(record: dict, calls: list[dict]) -> dict:
    answers = sum(c["response"]["kind"] == "answer" for q in record["questions"] for c in q["runs"])
    verdicts = [v for c in calls for v in c["verdicts"]]
    return {"answers": answers, "absence": len(verdicts), "false": sum(map(is_false, verdicts)),
            "answers_with_false": sum(any(map(is_false, c["verdicts"])) for c in calls),
            "unfound_quotes": sum(v["verdict"] == "false" and not v["span_found"] for v in verdicts),
            "unchecked": sum(v["verdict"] == "unchecked" for v in verdicts)}


def rows(results: list[dict], records: dict[str, dict], seed: int = 57) -> list[dict]:
    """The review sheet: every `false` verdict (found quote or not), plus a seeded sample of `true`."""
    def row(res: dict, call: dict, v: dict) -> dict:
        response = next(q for q in records[res["run_id"]]["questions"] if q["id"] == call["id"])["runs"][call["run"] - 1]["response"]
        p = next((p for p in response["passages"] if p["n"] == v["passage"]), None)
        return {"run_id": res["run_id"], "question_id": call["id"], "run": call["run"], "sentence": v["text"],
                "verdict": v["verdict"] + ("" if v["span_found"] else " (quote not found)"),
                "passage": f"[{p['n']}] {p['label']}" if p else "", "href": p["href"] if p else "",
                "span": v["span"], "human": "", "note": ""}
    every = [(res, call, v) for res in results for call in res["calls"] for v in call["verdicts"]]
    falses = [row(*x) for x in every if x[2]["verdict"] == "false"]
    trues = [x for x in every if x[2]["verdict"] == "true"]
    sample = random.Random(seed).sample(trues, min(SAMPLE_TRUE, len(trues)))
    return falses + [row(*x) for x in sample]


# ── I/O ───────────────────────────────────────────────────────────────────────────────────────

def _bodies(records: list[dict]) -> dict[str, str]:
    from ingest import db
    ids = list({p["chunkId"] for r in records for q in r["questions"] for c in q["runs"]
                for p in c["response"].get("passages") or []})
    with db.connect() as conn:
        return dict(conn.execute("select id, body from chunks where id = any(%s)", (ids,)).fetchall())


def check(run_dirs: list[Path], checker: Checker, out_dir: Path = OUT_DIR, labelled: bool = False) -> list[dict]:
    """`labelled`: only the calls with a row in the review sheet, to measure a new prompt against it."""
    from .harness import load_gold
    records = [json.loads((d / "run.json").read_text(encoding="utf-8")) for d in run_dirs]
    for d in run_dirs:
        if (out_dir / f"{d.name}.json").exists():
            raise AbsenceError(f"{d.name} is already checked; verdicts are never overwritten")
    bodies = _bodies(records)
    out_dir.mkdir(parents=True, exist_ok=True)
    summaries = []
    for d, record in zip(run_dirs, records):
        questions = {q["id"]: q["question"] for q in load_gold(record["header"]["split"])}
        print(f"{d.name}:")
        only = ({(r["question_id"], int(r["run"])) for r in _sheet() if r["run_id"] == record["header"]["run_id"]}
                if labelled else None)
        result = check_run(record, questions, bodies, checker, only=only)
        (out_dir / f"{d.name}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        summaries.append({"run": d.name, **result["summary"]})
    return summaries


def write_sheet(runs_dir: Path, out_dir: Path = OUT_DIR, out: Path = SHEET) -> int:
    if out.exists():
        raise AbsenceError(f"{out.name} exists; review decisions are never overwritten")
    results = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(out_dir.glob("*.json"))]
    records = {}
    for p in runs_dir.glob("*/run.json"):
        r = json.loads(p.read_text(encoding="utf-8"))
        records[r["header"]["run_id"]] = r
    sheet = rows(results, records)
    with out.open("w", encoding="utf-8-sig", newline="") as f:  # the BOM lets Excel read UTF-8
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(sheet)
    return len(sheet)


def _sheet(path: Path = SHEET) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def agreement(sheet: list[dict], results: list[dict]) -> dict:
    """Each labelled row's verdict from `results` against the human label, per half: how often a `false`
    is a false claim (precision), and how many human-false rows it calls true (misses)."""
    verdicts = {(res["run_id"], c["id"], c["run"], v["text"]): v for res in results for c in res["calls"] for v in c["verdicts"]}
    out = {}
    for half in ("tune", "held"):
        rows = [r for r in sheet if (r["question_id"] in TUNE) == (half == "tune")]
        pairs = [(verdicts.get((r["run_id"], r["question_id"], int(r["run"]), r["sentence"])), r["human"].strip().lower()[:1])
                 for r in rows]
        flagged = [h for v, h in pairs if v and is_false(v)]
        out[half] = {"rows": len(rows), "checked": sum(v is not None for v, _ in pairs), "flagged": len(flagged),
                     "right": flagged.count("f"), "human_false": sum(h == "f" for _, h in pairs),
                     "missed": sum(h == "f" and v is not None and not is_false(v) for v, h in pairs)}
    return out
