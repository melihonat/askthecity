"""The eval harness (EVALS.md, "Harness"): calls the deployed /api/ask with the eval header, one rung
at a time, and writes run.json and report.md. Retrieval logic lives only in the app.

Sequential calls, a discarded warm-up, 3 runs per rung. A 5xx or an `unavailable` limit (the app's
form of a server error) is retried once, then the run aborts; any other `limit` response or HTTP
error invalidates it. An invalid run writes nothing.
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Protocol

import requests
import yaml

from . import judge as judge_
from . import report
from .score import score

HARNESS_VERSION = "1"
# Bumped when gold is widened (EVALS.md, "Gold audit"); a run without it in its header scored against 1.
# Rows scored against different gold versions are never compared.
GOLD_VERSION = 2
ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "evals" / "questions.yaml"
RUNS_DIR = ROOT / "evals" / "runs"

EVAL_HEADER = "x-eval-key"       # lib/ask/eval.ts
EVAL_RUN_HEADER = "x-eval-run"
# lib/ask/config.ts RUNGS; `shipped-3` is the last fix rung LADDER.md allows, so no suffix may name it either
RUNGS = ["dense", "hybrid", "rerank", "shipped", "shipped-2", "side-sonnet", "side-quoted"]
RESERVED = set(RUNGS) | {"shipped-3"}
GATEWAY = "https://ai-gateway.vercel.sh"
COST_PER_CALL = 0.0011           # an answered Haiku question, STACK.md; refusals cost less
# Sonnet 5.5 is 20× Haiku 5.5's per-token price: generation ≈ $0.011 plus the same rerank
RUNG_COST_PER_CALL = {"side-sonnet": 0.012}
JUDGE_USD_PER_MTOK = (2.0, 10.0)  # Sonnet 5 input, output; billed to the judge's own key
RESERVE_USD = 3.0                # left for the public demo (evals/LADDER.md, "Spend preflight")
TIMEOUT_S = 60


class RunInvalid(Exception):
    """The run can't be scored and is never committed."""


class Transport(Protocol):
    def post(self, question: str, rung: str) -> tuple[int, list[dict]]: ...


class HttpTransport:
    def __init__(self, base_url: str, secret: str, run_id: str):
        self.url = base_url.rstrip("/") + "/api/ask"
        self.headers = {EVAL_HEADER: secret, EVAL_RUN_HEADER: run_id}

    def post(self, question: str, rung: str) -> tuple[int, list[dict]]:
        r = requests.post(self.url, json={"question": question, "rung": rung}, headers=self.headers, timeout=TIMEOUT_S)
        if r.status_code != 200 or not r.headers.get("content-type", "").startswith("application/x-ndjson"):
            return r.status_code, []
        r.encoding = "utf-8"
        return 200, [json.loads(line) for line in r.text.splitlines() if line.strip()]


def load_gold(split: str, path: Path = QUESTIONS) -> list[dict]:
    return [q for q in yaml.safe_load(path.read_text(encoding="utf-8")) if q["split"] == split]


def call(transport: Transport, question: str, rung: str) -> dict:
    """One question, as {passages, debug, response, wall_ms}."""
    for attempt in (1, 2):
        t0 = time.perf_counter()
        status, events = transport.post(question, rung)
        wall_ms = round((time.perf_counter() - t0) * 1000)
        server_error = status >= 500 or any(
            e.get("type") == "error" or e.get("type") == "final" and e["response"].get("limit") == "unavailable"
            for e in events)
        if not server_error:
            break
        if attempt == 2:
            raise RunInvalid(f"server error twice on {question!r} (HTTP {status})")
    if status != 200:
        raise RunInvalid(f"HTTP {status} on {question!r}")

    final = next((e["response"] for e in events if e.get("type") == "final"), None)
    if final and final["kind"] == "limit":
        raise RunInvalid(f"`{final['limit']}` limit on {question!r}")
    types = [e.get("type") for e in events]
    if types != ["passages", "debug", "final"]:
        # no debug event means the app didn't accept the eval header
        raise RunInvalid(f"expected passages → debug → final, got {types} on {question!r}")
    return {"passages": events[0]["passages"], "debug": events[1]["debug"], "response": final, "wall_ms": wall_ms}


def run_rung(questions: list[dict], rung: str, transport: Transport, runs: int = 3, log=print) -> dict[str, list[dict]]:
    """Every question `runs` times, sequentially, after one discarded warm-up call."""
    call(transport, questions[0]["question"], rung)
    data: dict[str, list[dict]] = {q["id"]: [] for q in questions}
    for run in range(1, runs + 1):
        for i, q in enumerate(questions, 1):
            c = call(transport, q["question"], rung)
            data[q["id"]].append(c)
            log(f"  run {run}/{runs} · {i}/{len(questions)} {q['id']}: {c['response']['kind']}")
    return data


def strip_bodies(c: dict) -> dict:
    """City text stays out of the public repo (CORPUS.md): passage bodies go, ids, labels and hrefs stay."""
    strip = lambda ps: [{k: v for k, v in p.items() if k != "body"} for p in ps]  # noqa: E731
    response = dict(c["response"])
    for key in ("passages", "nearest"):
        if key in response:
            response[key] = strip(response[key])
    return {**c, "passages": strip(c["passages"]), "response": response}


# ── the world outside: git, the database, the Gateway ─────────────────────────────────────────

def git_state() -> dict:
    """HEAD and whether the tree differs from it. Earlier rungs' output under evals/runs/ doesn't count:
    a ladder runs in one sitting and commits its runs together afterwards."""
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT, check=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", ".", ":(exclude)evals/runs"],
                                capture_output=True, text=True, cwd=ROOT, check=True).stdout.strip())
    return {"sha": sha, "dirty": dirty}


def read_snapshot() -> tuple[dict, set[str]]:
    from ingest import db
    with db.connect() as conn:
        cur = conn.execute("select id, snapshot_date::text, chunker_version, embed_model, embed_dim from snapshot")
        snapshot = dict(zip([d.name for d in cur.description], cur.fetchone()))
        ids = {r[0] for r in conn.execute("select id from chunks")}
    return snapshot, ids


def _gateway_get(path: str, key: str, params: dict | None = None) -> dict:
    r = requests.get(f"{GATEWAY}{path}", params=params, headers={"Authorization": f"Bearer {key}"}, timeout=30)
    r.raise_for_status()
    return r.json()


def preflight(calls: int, key: str, rung: str = "shipped") -> dict:
    """Refuses to start unless RESERVE_USD of Gateway credit would remain for the public demo."""
    balance = float(_gateway_get("/v1/credits", key)["balance"])
    estimate = round(calls * RUNG_COST_PER_CALL.get(rung, COST_PER_CALL), 4)
    if balance - estimate < RESERVE_USD:
        raise SystemExit(f"preflight: ${balance:.2f} credit, run ≈ ${estimate:.2f}; under ${RESERVE_USD:.0f} would remain. Top up first.")
    return {"balance_usd": balance, "estimate_usd": estimate}


def utc_day() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def read_spend(run_id: str, start: str, end: str, key: str) -> dict:
    """The run's real Gateway spend, from its tag. The reporting API can lag or be off the plan;
    a failure is recorded, not fatal."""
    try:
        rows = _gateway_get("/v1/report", key, {"start_date": start, "end_date": end, "group_by": "tag", "tags": f"eval:{run_id}"})["results"]
        row = next((r for r in rows if r.get("tag") == f"eval:{run_id}"), None)
        return {"usd": row["total_cost"] if row else 0.0, "requests": row.get("request_count") if row else 0}
    except (requests.RequestException, KeyError, ValueError) as e:
        return {"usd": None, "error": str(e)[:200]}


# ── one rung, end to end ──────────────────────────────────────────────────────────────────────

def judge_header(judge: judge_.Judge | None) -> dict | None:
    """The judge's model and prompt, and what it cost on its own key (estimated from token usage)."""
    if judge is None:
        return None
    usage = getattr(judge, "usage", None)
    usd = usage and round((usage["input_tokens"] * JUDGE_USD_PER_MTOK[0] + usage["output_tokens"] * JUDGE_USD_PER_MTOK[1]) / 1e6, 4)
    return {**judge_.info(), "usage": usage, "usd_estimate": usd}


def header(*, run_id: str, rung: str, split: str, base_url: str, data: dict, git: dict, snapshot: dict, spend: dict,
           preflight_: dict | None, judge: dict | None = None) -> dict:
    debug = next(iter(data.values()))[0]["debug"]
    return {
        "run_id": run_id,
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "harness_version": HARNESS_VERSION,
        "gold": GOLD_VERSION,
        "rung": rung,
        "config": debug["config"],
        "split": split,
        "base_url": base_url,
        "git": git,
        "deployed_sha": debug["build"]["sha"],
        "snapshot": snapshot,
        "embedder": debug["build"]["embedder"],
        "reranker": debug["build"]["reranker"],
        "llm": debug["config"]["model"],
        "prompt": {"version": debug["build"]["promptVersion"], "hash": debug["build"]["promptHash"]},
        "judge": judge,
        "threshold": debug["threshold"],
        "runs": len(next(iter(data.values()))),
        "preflight": preflight_,
        "spend": spend,
    }


def run_dir(rung: str, split: str, day: str, suffix: str = "") -> Path:
    """`<date>-<rung>[-dev][-<suffix>]`; the suffix names a second run of a rung on the same day."""
    if split == "test" and suffix and f"{rung}-{suffix}" in RESERVED:
        raise SystemExit(f"--suffix {suffix} would name the `{rung}-{suffix}` rung's directory; pick another suffix")
    return RUNS_DIR / (f"{day}-{rung}" + ("" if split == "test" else f"-{split}") + (f"-{suffix}" if suffix else ""))


def run(rung: str, split: str, base_url: str, secret: str, gateway_key: str, runs: int = 3,
        skip_preflight: bool = False, transport: Transport | None = None, suffix: str = "",
        judge: judge_.Judge | None = None) -> Path:
    """`judge` None leaves answer correct out of the run (`--skip-judge`)."""
    gold = load_gold(split)
    out = run_dir(rung, split, date.today().isoformat(), suffix)
    if out.exists():
        raise SystemExit(f"{out.relative_to(ROOT)} exists; a committed run is never overwritten")
    run_id = f"{out.name}-{datetime.now().strftime('%H%M%S')}"

    git = git_state()
    snapshot, chunk_ids = read_snapshot()
    pre = None if skip_preflight else preflight(len(gold) * runs + 1, gateway_key, rung)
    started = utc_day()  # Gateway reports by UTC day
    print(f"{run_id}: {len(gold)} {split} questions × {runs} runs on `{rung}` against {base_url}")

    data = run_rung(gold, rung, transport or HttpTransport(base_url, secret, run_id), runs)
    if judge is not None:
        try:
            judge_.judge_run(data, gold, judge)
        except judge_.JudgeError as e:
            raise RunInvalid(f"judge: {e}") from e
    scores = score(data, gold, chunk_ids)
    head = header(run_id=run_id, rung=rung, split=split, base_url=base_url, data=data, git=git, snapshot=snapshot,
                  spend=read_spend(run_id, started, utc_day(), gateway_key), preflight_=pre, judge=judge_header(judge))

    out.mkdir(parents=True)
    record = {"header": head, "scores": scores,
              "questions": [{"id": q["id"], "runs": [strip_bodies(c) for c in data[q["id"]]]} for q in gold]}
    (out / "run.json").write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "report.md").write_text(report.render(head, scores, data), encoding="utf-8")
    return out
