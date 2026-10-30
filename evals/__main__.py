"""python -m evals run --rung <rung> [--split dev] — one rung against the deployed /api/ask."""
from __future__ import annotations

import argparse
import sys


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    p = argparse.ArgumentParser(prog="python -m evals")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="run one rung, write evals/runs/<date>-<rung>[-dev]/run.json and report.md")
    r.add_argument("--rung", required=True, choices=["dense", "hybrid", "rerank", "shipped"])
    r.add_argument("--split", default="test", choices=["test", "dev"])
    r.add_argument("--base-url", default="https://ask-the-city.vercel.app", help="the deployment to measure")
    r.add_argument("--runs", type=int, default=3)
    r.add_argument("--skip-preflight", action="store_true", help="don't check the remaining Gateway credit")
    args = p.parse_args()

    from ingest.config import env
    from .harness import RunInvalid, run

    try:
        out = run(args.rung, args.split, args.base_url, env("EVAL_HEADER_SECRET"), env("AI_GATEWAY_API_KEY"),
                  runs=args.runs, skip_preflight=args.skip_preflight)
    except RunInvalid as e:
        raise SystemExit(f"run invalid, nothing written: {e}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
