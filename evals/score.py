"""The scorer (EVALS.md, "Columns" and "Noise"). Pure: run data, gold and the snapshot's chunk ids in,
columns and findings out. No I/O; answer correct reads the judge's verdicts already stored on each
call (evals/judge.py) and is absent from an unjudged run.

`run_data` maps a question id to its calls, one per run, each the events the app sent:
`{"passages": [PassageView], "debug": DebugEvent, "response": AskResponse}`.
"""
from __future__ import annotations

import math
import statistics
from collections import Counter

from .sentences import coverage

LATENCY = {"passages_p50", "total_p50", "total_p95"}
# columns where a lower value is better, for the ≈ decision
LOWER_IS_BETTER = {"false_refusals"} | LATENCY


def matches(pattern: str, chunk_id: str) -> bool:
    """Exact chunk id, or a prefix ending in `*`. `tmc:608-10:*` is any chunk of § 608-10, so it also
    matches `tmc:608-10`, the id of a § kept whole."""
    if not pattern.endswith("*"):
        return chunk_id == pattern
    prefix = pattern[:-1]
    return chunk_id.startswith(prefix) or (prefix.endswith(":") and chunk_id == prefix[:-1])


def satisfies(group: list[str], chunk_ids) -> bool:
    return any(matches(p, c) for p in group for c in chunk_ids)


def stale_groups(question: dict, snapshot_ids) -> list[list[str]]:
    """Required groups that match no chunk in the snapshot: stale gold, never a miss."""
    return [g for g in question.get("required") or [] if not satisfies(g, snapshot_ids)]


def _column(values: list[float]) -> dict:
    return {"value": statistics.fmean(values) if values else None, "n": len(values)}


def _percentile(values: list[float], q: float) -> float | None:
    """Nearest-rank percentile: always a latency some call actually had."""
    if not values:
        return None
    return sorted(values)[max(0, math.ceil(len(values) * q / 100) - 1)]


def _outcome(response: dict) -> str:
    return response["kind"] if response["kind"] == "answer" else f"{response['kind']}:{response.get('reason') or response.get('limit')}"


def _cited(response: dict) -> list[str]:
    return [c["chunkId"] for c in response["citations"]]


def _in_gold(chunk_id: str, q: dict) -> bool:
    return any(matches(p, chunk_id) for g in q["required"] for p in g) or any(matches(p, chunk_id) for p in q.get("acceptable") or [])


def _generation_columns(gold: list[dict], calls: dict[str, dict], scored: set[str]) -> dict[str, dict]:
    """The columns that vary with generation, for one run. `calls` maps question id → that run's call."""
    answer_qs = [q for q in gold if q["expect"] == "answer"]
    refuse_qs = [q for q in gold if q["expect"] == "refuse"]
    answered = [q for q in answer_qs if q["id"] in scored and calls[q["id"]]["response"]["kind"] == "answer"]

    precision, full = [], []
    for q in answered:
        cited = _cited(calls[q["id"]]["response"])
        precision.append(sum(_in_gold(c, q) for c in cited) / len(cited))
        full.append(float(all(satisfies(g, cited) for g in q["required"])))

    cover = []
    for q in gold:
        response = calls[q["id"]]["response"]
        if response["kind"] == "answer":
            covered, counted = coverage(response["text"])
            if counted:
                cover.append(covered / counted)

    refused = lambda q: calls[q["id"]]["response"]["kind"] == "refusal"  # noqa: E731
    passages_ms, answered_ms = _latencies(calls.values())
    return {
        "cite_precision": _column(precision),
        "cite_full": _column(full),
        "coverage": _column(cover),
        "refusal_recall": _column([float(refused(q)) for q in refuse_qs]),
        "false_refusals": _column([float(refused(q)) for q in answer_qs]),
        **_latency_columns(passages_ms, answered_ms),
    }


def _correct(verdicts: list[dict]) -> float:
    """Key facts judged present ÷ key facts, 0 if any is contradicted."""
    if any(v["verdict"] == "contradicted" for v in verdicts):
        return 0.0
    return sum(v["verdict"] == "present" for v in verdicts) / len(verdicts)


def judged(run_data: dict[str, list[dict]], gold: list[dict]) -> dict:
    """The answer correct column from the judge's verdicts on each call, and the contradicted facts by
    name. Empty when the run wasn't judged. Over every answered `answer` question: correctness needs
    no chunk ids, so stale gold doesn't drop a question here."""
    if not any("judge" in c for calls in run_data.values() for c in calls):
        return {"columns": {}, "contradicted": []}
    answer_qs = [q for q in gold if q["expect"] == "answer" and q["id"] in run_data]
    runs = min(len(calls) for calls in run_data.values())
    per_run = []
    for i in range(runs):
        values = [_correct(c["judge"]) for q in answer_qs if (c := run_data[q["id"]][i])["response"]["kind"] == "answer"]
        per_run.append(_column(values))
    values = [r["value"] for r in per_run if r["value"] is not None]
    contradicted = [{"id": q["id"], "run": run, "fact": v["fact"], "span": v["span"]}
                    for q in answer_qs for run, c in enumerate(run_data[q["id"]][:runs], 1)
                    for v in c.get("judge") or [] if v["verdict"] == "contradicted"]
    column = {"value": statistics.fmean(values) if values else None, "n": min(r["n"] for r in per_run),
              "spread": (max(values) - min(values)) if values else None, "per_run": per_run,
              "contradicted": len(contradicted)}
    return {"columns": {"answer_correct": column}, "contradicted": contradicted}


def _latencies(calls) -> tuple[list[int], list[int]]:
    """Server passages time (retrieval + rerank) of every call; server total of answered calls only
    (a gate refusal skips generation and would flatter a rung that refuses more)."""
    calls = list(calls)
    passages = [c["debug"]["timings"]["retrieval_ms"] + c["debug"]["timings"]["rerank_ms"] for c in calls]
    answered = [c["debug"]["timings"]["total_ms"] for c in calls if c["response"]["kind"] == "answer"]
    return passages, answered


def _latency_columns(passages_ms: list[int], answered_ms: list[int]) -> dict[str, dict]:
    return {
        "passages_p50": {"value": _percentile(passages_ms, 50), "n": len(passages_ms)},
        "total_p50": {"value": _percentile(answered_ms, 50), "n": len(answered_ms)},
        "total_p95": {"value": _percentile(answered_ms, 95), "n": len(answered_ms)},
    }


def score(run_data: dict[str, list[dict]], gold: list[dict], snapshot_chunk_ids) -> dict:
    snapshot_ids = set(snapshot_chunk_ids)
    gold = [q for q in gold if q["id"] in run_data]
    runs = min(len(calls) for calls in run_data.values())

    stale = {q["id"]: groups for q in gold if q["expect"] == "answer" and (groups := stale_groups(q, snapshot_ids))}
    scored = {q["id"] for q in gold if q["expect"] == "answer" and q["id"] not in stale}

    # Retrieval: run 1 only; runs 2.. must have returned the same candidates.
    first = {qid: calls[0] for qid, calls in run_data.items()}
    recall, full20, hit, fullctx = [], [], [], []
    for q in gold:
        if q["id"] not in scored:
            continue
        candidates = [c["chunkId"] for c in first[q["id"]]["debug"]["candidates"]]
        context = [p["chunkId"] for p in first[q["id"]]["passages"]]
        hits20 = [satisfies(g, candidates) for g in q["required"]]
        hitsctx = [satisfies(g, context) for g in q["required"]]
        recall.append(float(any(hits20)))
        full20.append(float(all(hits20)))
        hit.append(float(any(hitsctx)))
        fullctx.append(float(all(hitsctx)))
    columns = {
        "recall@20": {**_column(recall), "spread": 0.0},
        "full@20": {**_column(full20), "spread": 0.0},
        "hit@ctx": {**_column(hit), "spread": 0.0},
        "full@ctx": {**_column(fullctx), "spread": 0.0},
    }
    retrieval_mismatch = sorted(
        qid for qid, calls in run_data.items()
        if any([c["chunkId"] for c in call["debug"]["candidates"]] != [c["chunkId"] for c in calls[0]["debug"]["candidates"]]
               for call in calls[1:])
    )

    # Generation: per run, then the mean of the runs, with the run-to-run spread.
    # Latency pools every call of every run (a percentile, not a mean of percentiles).
    per_run = [_generation_columns(gold, {qid: calls[i] for qid, calls in run_data.items()}, scored) for i in range(runs)]
    pooled = _latency_columns(*_latencies(call for calls in run_data.values() for call in calls[:runs]))
    for name in per_run[0]:
        values = [r[name]["value"] for r in per_run if r[name]["value"] is not None]
        columns[name] = {
            **(pooled[name] if name in LATENCY else {
                "value": statistics.fmean(values) if values else None,
                "n": min(r[name]["n"] for r in per_run),  # answered counts can differ between runs
            }),
            "spread": (max(values) - min(values)) if values else None,
            "per_run": [r[name] for r in per_run],
        }

    outcomes = {qid: [_outcome(c["response"]) for c in calls] for qid, calls in run_data.items()}
    unstable = sorted(qid for qid, seen in outcomes.items() if len(set(seen)) > 1)
    judge = judged(run_data, gold)

    return {
        "columns": {**columns, **judge["columns"]},
        "contradicted": judge["contradicted"],
        "stale": [{"id": qid, "groups": groups} for qid, groups in stale.items()],
        "retrieval_mismatch": retrieval_mismatch,
        "unstable": [{"id": qid, "outcomes": outcomes[qid]} for qid in unstable],
        "off_gold": _off_gold(gold, run_data, scored),
        "refusals": _refusal_breakdown(gold, run_data),
        "pinned": sorted(qid for qid, call in first.items() if call["debug"]["pinned"]),
    }


def _off_gold(gold: list[dict], run_data: dict, scored: set[str]) -> list[dict]:
    """Citations outside required/acceptable: widen `acceptable` in a commit, or accept the miss."""
    out = []
    for q in gold:
        if q["id"] not in scored:
            continue
        for run, call in enumerate(run_data[q["id"]], 1):
            if call["response"]["kind"] == "answer":
                out += [{"id": q["id"], "run": run, "chunkId": c} for c in _cited(call["response"]) if not _in_gold(c, q)]
    return out


def _refusal_breakdown(gold: list[dict], run_data: dict) -> dict:
    """Refusal reasons in each direction, over every run: wrong refusals of answer questions, and how
    refuse questions were refused (or answered)."""
    false_refusals, refuse_outcomes = Counter(), Counter()
    for q in gold:
        for call in run_data[q["id"]]:
            r = call["response"]
            if q["expect"] == "answer" and r["kind"] == "refusal":
                false_refusals[r["reason"]] += 1
            elif q["expect"] == "refuse":
                refuse_outcomes[r.get("reason", r["kind"])] += 1
    return {"false_refusals": dict(false_refusals), "refuse_questions": dict(refuse_outcomes)}


def compare(new: dict, previous: dict, column: str) -> str:
    """'better', 'worse' or '≈': a rung beats the previous one only by more than its own run-to-run spread."""
    if new["value"] is None or previous["value"] is None:
        return "≈"
    delta = new["value"] - previous["value"]
    if abs(delta) <= (new.get("spread") or 0.0):
        return "≈"
    return "better" if (delta < 0) == (column in LOWER_IS_BETTER) else "worse"
