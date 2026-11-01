"""python -m evals run --rung <rung> [--split dev] — one rung against the deployed /api/ask.
python -m evals audit sheet <run dir> | agreement — the judge/human audit.
python -m evals gold-audit — the review sheet of citations outside gold.
python -m evals calibrate <dev run dir> — set the refusal threshold from a dev run.
python -m evals results — regenerate RESULTS.md, the README's blocks and /evals from the committed runs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .harness import RUNGS


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    p = argparse.ArgumentParser(prog="python -m evals")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run", help="run one rung, write evals/runs/<date>-<rung>[-dev][-<suffix>]/run.json and report.md")
    r.add_argument("--rung", required=True, choices=RUNGS)
    r.add_argument("--split", default="test", choices=["test", "dev"])
    r.add_argument("--base-url", default="https://ask-the-city.vercel.app", help="the deployment to measure")
    r.add_argument("--runs", type=int, default=3)
    r.add_argument("--suffix", default="", help="names a second run of the rung on the same day, e.g. 2")
    r.add_argument("--skip-preflight", action="store_true", help="don't check the remaining Gateway credit")
    r.add_argument("--skip-judge", action="store_true", help="no answer correct column (no JUDGE_ANTHROPIC_API_KEY spend)")
    a = sub.add_parser("audit", help="judge/human audit: write the blind hand-scoring sheet, or compute agreement from it")
    a.add_argument("step", choices=["sheet", "agreement"])
    a.add_argument("run_dir", type=Path, nargs="?", help="sheet: the judged run to hand-score, e.g. evals/runs/2026-11-02-shipped")
    a.add_argument("--runs", default="1", help="sheet: which of its runs, e.g. 1 or 1,2,3")
    sub.add_parser("gold-audit", help="write evals/gold_audit.csv: citations outside gold in every committed test run, for review")
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

    if args.command == "audit":
        from .audit import SHEET, AuditError, apply, write_sheet
        from .harness import RUNS_DIR, load_gold
        try:
            if args.step == "sheet":
                if args.run_dir is None:
                    raise AuditError("sheet needs the run dir")
                record = json.loads((args.run_dir / "run.json").read_text(encoding="utf-8"))
                n = write_sheet(args.run_dir, load_gold(record["header"]["split"]), [int(x) for x in args.runs.split(",")])
                print(f"wrote {n} key facts to {SHEET}; fill `human` with present / absent / contradicted, then "
                      "`python -m evals audit agreement`")
            else:
                result = apply(RUNS_DIR)
                print(f"judge agreed on {result['agree']} of {result['total']} facts; wrote evals/judge_agreement.json. "
                      "Run `python -m evals results` to publish it.")
        except AuditError as e:
            raise SystemExit(f"audit: {e}")
        return

    if args.command == "gold-audit":
        from .gold_audit import SHEET, GoldAuditError, write_sheet
        from .harness import RUNS_DIR, load_gold
        try:
            n = write_sheet(RUNS_DIR, load_gold("test"))
        except GoldAuditError as e:
            raise SystemExit(f"gold audit: {e}")
        print(f"wrote {n} off-gold citations to {SHEET}; fill `decision` with accept / reject")
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
    from .judge import AnthropicJudge

    judge = None if args.skip_judge else AnthropicJudge(env("JUDGE_ANTHROPIC_API_KEY"))
    try:
        out = run(args.rung, args.split, args.base_url, env("EVAL_HEADER_SECRET"), env("AI_GATEWAY_API_KEY"),
                  runs=args.runs, skip_preflight=args.skip_preflight, suffix=args.suffix, judge=judge)
    except RunInvalid as e:
        raise SystemExit(f"run invalid, nothing written: {e}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
