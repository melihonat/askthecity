"""python -m evals run --rung <rung> [--split dev] — one rung against the deployed /api/ask.
python -m evals calibrate <dev run dir> — set the refusal threshold from a dev run.
python -m evals results — regenerate RESULTS.md, the README's blocks and /evals from the committed runs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    p = argparse.ArgumentParser(prog="python -m evals")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="run one rung, write evals/runs/<date>-<rung>[-dev][-<suffix>]/run.json and report.md")
    r.add_argument("--rung", required=True, choices=["dense", "hybrid", "rerank", "shipped", "side-sonnet", "side-quoted"])
    r.add_argument("--split", default="test", choices=["test", "dev"])
    r.add_argument("--base-url", default="https://ask-the-city.vercel.app", help="the deployment to measure")
    r.add_argument("--runs", type=int, default=3)
    r.add_argument("--suffix", default="", help="names a second run of the rung on the same day, e.g. 2")
    r.add_argument("--skip-preflight", action="store_true", help="don't check the remaining Gateway credit")
    c = sub.add_parser("calibrate", help="threshold from a dev run: rewrite EVALS.md's table and lib/ask/config.ts")
    c.add_argument("run_dir", type=Path, help="e.g. evals/runs/2026-10-31-shipped-dev")
    sub.add_parser("results", help="from evals/runs: write evals/RESULTS.md, the README's generated blocks and the /evals data")
    args = p.parse_args()

    if args.command == "results":
        from .results import ResultsError, apply
        try:
            data = apply()
        except ResultsError as e:
            raise SystemExit(f"can't render results: {e}")
        print(f"{len(data['ladder'])} ladder and {len(data['side'])} side rungs; {data['headerLink']}; "
              "wrote evals/RESULTS.md, README.md and app/evals/results.json")
        return

    if args.command == "calibrate":
        from .calibrate import CalibrationError, apply, calibrate
        from .harness import load_gold
        try:
            result = calibrate(json.loads((args.run_dir / "run.json").read_text(encoding="utf-8")), load_gold("dev"))
        except CalibrationError as e:
            raise SystemExit(f"can't calibrate: {e}")
        apply(result)
        print(f"threshold {result['threshold']} (0.5 × {result['lowest']:.4f}); wrote EVALS.md and lib/ask/config.ts")
        return

    from ingest.config import env
    from .harness import RunInvalid, run

    try:
        out = run(args.rung, args.split, args.base_url, env("EVAL_HEADER_SECRET"), env("AI_GATEWAY_API_KEY"),
                  runs=args.runs, skip_preflight=args.skip_preflight, suffix=args.suffix)
    except RunInvalid as e:
        raise SystemExit(f"run invalid, nothing written: {e}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
