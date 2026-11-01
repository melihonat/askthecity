"""python -m ingest <stage>. Every stage reads files and writes files, so any stage re-runs alone."""
from __future__ import annotations

import argparse
import sys


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    p = argparse.ArgumentParser(prog="python -m ingest")
    sub = p.add_subparsers(dest="stage", required=True)
    fr = sub.add_parser("fetch-rules", help="toronto.ca → corpus/, R2, manifest")
    fr.add_argument("--chapter", action="append", help="chapter number, e.g. 591 (repeatable); default: all")
    sub.add_parser("fetch-bylaws", help="amending by-laws for the chunked chapters → corpus/, R2, manifest")
    rs = sub.add_parser("receive-saves", help="localhost receiver the SAVE_TMMIS.md runbook posts item pages to")
    rs.add_argument("--port", type=int, default=8765)
    sub.add_parser("check-saves", help="saved item pages vs snapshot/tmmis_items.txt; fails on any missing or bad page")
    sub.add_parser("fetch-reports", help="staff reports the label gate lets in → corpus/, R2, manifest; stops on an unreviewed label")
    sub.add_parser("restore", help="R2 → corpus/, verifying sha256")
    sub.add_parser("extract", help="corpus/ → build/text/")
    sub.add_parser("chunk", help="build/text/ → build/chunks.jsonl")
    em = sub.add_parser("embed", help="chunks → build/embeddings.jsonl")
    em.add_argument("--yes", action="store_true", help="skip the spend confirmation")
    sub.add_parser("load", help="build/ → staging schema")
    sub.add_parser("smoke", help="check staging: counts, embeddings, U+FFFD, pins")
    sub.add_parser("swap", help="staging → live, one transaction; refuses if smoke fails")
    al = sub.add_parser("all", help="check-saves → fetch-reports → extract → chunk → embed → load, stopping at the first failure")
    al.add_argument("--yes", action="store_true", help="skip the spend confirmation")
    args = p.parse_args()

    if args.stage == "fetch-rules":
        from .fetch import fetch_rules
        fetch_rules(args.chapter)
    elif args.stage == "fetch-bylaws":
        from .fetch import fetch_bylaws
        fetch_bylaws()
    elif args.stage == "receive-saves":
        from .tmmis import receive
        receive(args.port)
    elif args.stage == "check-saves":
        from .tmmis import check_saves
        check_saves()
    elif args.stage == "fetch-reports":
        from .reports import fetch_reports
        fetch_reports()
    elif args.stage == "restore":
        from .store import restore
        restore()
    elif args.stage == "extract":
        from .extract import extract
        extract()
    elif args.stage == "chunk":
        from .chunk import chunk
        chunk()
    elif args.stage == "embed":
        from .embed import embed
        embed(yes=args.yes)
    elif args.stage == "load":
        from .db import load
        load()
    elif args.stage == "smoke":
        from .db import smoke
        smoke()
    elif args.stage == "swap":
        from .db import swap
        swap()
    elif args.stage == "all":
        from .chunk import chunk
        from .db import load
        from .embed import embed
        from .extract import extract
        from .reports import fetch_reports
        from .tmmis import check_saves
        check_saves()
        fetch_reports()
        extract()
        chunk()
        embed(yes=args.yes)
        load()
        print("next, by hand: python -m ingest smoke, then python -m ingest swap")


if __name__ == "__main__":
    main()
