"""The answer judge (EVALS.md, "Answer judge"): a pinned Sonnet 5 on its own key grades each answer
against its question's key facts, per fact `present | absent | contradicted` with the quoted span.

It sees only the question, the key facts and the answer text: no passages (citations already
measure grounding). The verdicts are stored on each call as `judge`; the scorer turns them into
the answer correct column.

Sonnet 5 takes no sampling parameters, so "temperature 0" is as close as the API allows: thinking
off and a fixed JSON schema. The model id and prompt hash go in every run.json.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Protocol

ROOT = Path(__file__).resolve().parent.parent
PROMPT = ROOT / "evals" / "judge_prompt.md"
MODEL = "claude-sonnet-5"
PROMPT_VERSION = "1"            # bump with any change to judge_prompt.md; a change needs a fresh audit
VERDICTS = ("present", "absent", "contradicted")
MAX_TOKENS = 2000

SCHEMA = {
    "type": "object",
    "properties": {
        "facts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "fact": {"type": "integer"},
                    "verdict": {"type": "string", "enum": list(VERDICTS)},
                    "span": {"type": "string"},
                },
                "required": ["fact", "verdict", "span"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["facts"],
    "additionalProperties": False,
}


class JudgeError(Exception):
    """The judge's reply can't be used; the run isn't committed."""


class Judge(Protocol):
    def grade(self, question: str, key_facts: list[str], answer: str) -> list[dict]: ...


def prompt_text() -> str:
    return PROMPT.read_text(encoding="utf-8")


def info() -> dict:
    """What run.json records about the judge."""
    return {"model": MODEL, "prompt_version": PROMPT_VERSION,
            "prompt_hash": hashlib.sha256(prompt_text().encode("utf-8")).hexdigest()[:12]}


def user_message(question: str, key_facts: list[str], answer: str) -> str:
    facts = "\n".join(f"{i}. {f}" for i, f in enumerate(key_facts, 1))
    return f"Question: {question}\n\nKey facts:\n{facts}\n\nAnswer:\n<answer>\n{answer}\n</answer>"


def parse(reply: str, key_facts: list[str], answer: str) -> list[dict]:
    """One verdict per key fact, in order: `{fact, verdict, span, span_found}`. `span_found` is false
    when a quoted span isn't in the answer word for word, for the audit to look at."""
    try:
        facts = json.loads(reply)["facts"]
    except (ValueError, KeyError, TypeError) as e:
        raise JudgeError(f"unreadable judge reply: {reply[:200]!r}") from e
    if sorted(f.get("fact") for f in facts) != list(range(1, len(key_facts) + 1)):
        raise JudgeError(f"judge graded facts {[f.get('fact') for f in facts]}, expected 1–{len(key_facts)}")
    out = []
    for f in sorted(facts, key=lambda f: f["fact"]):
        if f["verdict"] not in VERDICTS:
            raise JudgeError(f"unknown verdict {f['verdict']!r}")
        out.append({"fact": f["fact"], "verdict": f["verdict"], "span": f["span"],
                    "span_found": f["verdict"] == "absent" or (bool(f["span"]) and f["span"] in answer)})
    return out


class AnthropicJudge:
    """Calls Anthropic directly on JUDGE_ANTHROPIC_API_KEY, never the demo's Gateway credit."""

    def __init__(self, api_key: str):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.system = prompt_text()
        self.usage = {"input_tokens": 0, "output_tokens": 0, "calls": 0}

    def grade(self, question: str, key_facts: list[str], answer: str) -> list[dict]:
        r = self.client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=self.system,
            thinking={"type": "disabled"},
            output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": user_message(question, key_facts, answer)}],
        )
        self.usage["input_tokens"] += r.usage.input_tokens
        self.usage["output_tokens"] += r.usage.output_tokens
        self.usage["calls"] += 1
        if r.stop_reason != "end_turn":
            raise JudgeError(f"judge stopped with {r.stop_reason} on {question!r}")
        return parse(next(b.text for b in r.content if b.type == "text"), key_facts, answer)


def judge_run(run_data: dict[str, list[dict]], gold: list[dict], judge: Judge, log=print) -> None:
    """Adds `judge` verdicts to every answered call of an `answer` question, in place."""
    for q in gold:
        if q["expect"] != "answer" or q["id"] not in run_data:
            continue
        for run, call in enumerate(run_data[q["id"]], 1):
            if call["response"]["kind"] == "answer":
                call["judge"] = judge.grade(q["question"], q["key_facts"], call["response"]["text"])
                log(f"  judged run {run} {q['id']}: " + ", ".join(v["verdict"] for v in call["judge"]))
