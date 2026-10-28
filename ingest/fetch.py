"""fetch-rules: download Code chapter PDFs from toronto.ca into the snapshot store."""
from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone

import requests

from . import config, store


def chapter_urls() -> dict[str, str]:
    """Chapter number ('591') → PDF URL, from the City's Code index page."""
    html = requests.get(config.CODE_INDEX_URL, timeout=60).text
    links = re.findall(r'href="([^"]+\.pdf)"[^>]*>\s*Chapter\s+(\d+[A-Z]?)\s*<', html)
    return {ch: url.replace("http://", "https://", 1) for url, ch in links}


def fetch_rules(chapters: list[str]) -> None:
    urls = chapter_urls()
    for ch in chapters:
        url = urls.get(ch)
        if not url:
            raise SystemExit(f"Chapter {ch} is not on {config.CODE_INDEX_URL}")
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        row = store.put(resp.content, store.ManifestRow(
            sha256="", kind="code_chapter", ref=f"ch-{ch}", parent_ref="", source_url=url,
            obtained_by="script",
            obtained_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            last_modified=resp.headers.get("Last-Modified", ""), etag=resp.headers.get("ETag", ""),
            bytes=0, content_type=resp.headers.get("Content-Type", ""), encoding="",
        ))
        print(f"ch-{ch}: {row.bytes} bytes, sha256 {row.sha256[:12]}…")
    write_snapshot_md()


def write_snapshot_md() -> None:
    rows = store.read_manifest()
    fetched = sorted(r.obtained_at[:10] for r in rows if r.obtained_by == "script")
    counts = Counter(r.kind for r in rows)
    lines = ["# Snapshot", "",
             f"Snapshot date: **{fetched[0]}** (the day `fetch-rules` ran).", "",
             "| Kind | Files |", "| --- | --- |",
             *[f"| `{k}` | {n} |" for k, n in sorted(counts.items())], "",
             "The files are not in this repo. To rebuild `corpus/` from the private R2 copy, verifying",
             "every sha256 against `manifest.csv`:", "", "```", "python -m ingest restore", "```", ""]
    (config.SNAPSHOT / "SNAPSHOT.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
