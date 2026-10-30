"""fetch-rules: Code chapter PDFs; fetch-bylaws: amending and replacement by-law PDFs. toronto.ca → the snapshot store."""
from __future__ import annotations

import html
import json
import re
from collections import Counter
from datetime import datetime, timezone

import requests

from . import config, store

# One row of a yearly by-law list: number cell (link to the PDF), then the title cell.
LIST_ROW = re.compile(r'<a href="([^"]+\.pdf)"[^>]*>\s*(\d+-\d{4})\s*</a>.*?</td>\s*<td>(.*?)</td>', re.S)
TITLE_CHAPTER = re.compile(r"\bChapter\s+(\d+[A-Z]?)\b")
# A title naming a street, an address or a ward: traffic and site-specific by-laws.
STREET = re.compile(r"\brespecting\s+(?!the\s)[A-Z0-9]|\bin respect of \d|\bmunicipally known\b|\bat \d+(?:-\d+)? [A-Z]")
# Whole-chapter replacements and new chapters (1511-2025, 1512-2025, 1513-2025) are not amending by-laws.
REPLACEMENT = re.compile(r"^To (repeal\b.*\breplace with new Chapter|enact a new\b.*\bChapter)")
# "To repeal … Chapter 629, Property Standards and replace with new Chapter 629, …": a replacement
# by-law. A new chapter with no old one (1513-2025, Ch 611) is out of scope.
REPEAL_AND_REPLACE = re.compile(r"^To repeal\b.*?\bChapter (\d+[A-Z]?)\b.*\breplace with new Chapter (\d+[A-Z]?)\b")


def chapter_urls() -> dict[str, str]:
    """Chapter number ('591') → PDF URL, from the City's Code index page."""
    html = requests.get(config.CODE_INDEX_URL, timeout=60).text
    links = re.findall(r'href="([^"]+\.pdf)"[^>]*>\s*Chapter\s+(\d+[A-Z]?)\s*<', html)
    return {ch: url.replace("http://", "https://", 1) for url, ch in links}


def fetch_rules(chapters: list[str] | None = None) -> None:
    """Fetch the given chapters, or every chapter on the index (stubs included; `chunk` drops them)."""
    urls = chapter_urls()
    chapters = chapters or sorted(urls, key=lambda c: (int(re.match(r"\d+", c)[0]), c))
    print(f"{len(chapters)} chapters")
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


def bylaw_list(page: str) -> list[tuple[str, str, str]]:
    """A yearly law-list page → (number, PDF URL, title) per by-law."""
    return [(num, url.replace("http://", "https://", 1), " ".join(html.unescape(re.sub(r"<[^>]+>", " ", title)).split()))
            for url, num, title in LIST_ROW.findall(page)]


def bylaw_candidates(listing: list[tuple[str, str, str]], consolidated: dict[str, str | None]
                     ) -> list[tuple[str, str, str, list[str]]]:
    """By-laws whose title amends a Code chapter in the snapshot, enacted in or after that chapter's
    consolidated-as-of year, naming no street or address. The chunk stage's linker decides the
    rest (already folded in, schedule-only). `consolidated`: chapter → date, or None if unprinted."""
    out = []
    for num, url, title in listing:
        if "Municipal Code" not in title or STREET.search(title) or REPLACEMENT.match(title):
            continue
        year = num[-4:]
        chapters = sorted({ch for ch in TITLE_CHAPTER.findall(title)
                           if ch in consolidated and year >= (consolidated[ch] or "0000")[:4]})
        if chapters:
            out.append((num, url, title, chapters))
    return out


def replacement_candidates(listing: list[tuple[str, str, str]], consolidated: dict[str, str | None]
                           ) -> list[tuple[str, str, str, list[str]]]:
    """By-laws that repeal a snapshot chapter and replace it with a new one of the same number,
    enacted in or after its consolidated-as-of year. Whether one stands in for the chapter, rides
    along as not yet law, or is already consolidated is the chunk stage's call (ingest/replace.py)."""
    out = []
    for num, url, title in listing:
        m = REPEAL_AND_REPLACE.match(title)
        if m and m[1] == m[2] and m[1] in consolidated and num[-4:] >= (consolidated[m[1]] or "0000")[:4]:
            out.append((num, url, title, [m[1]]))
    return out


def fetch_bylaws() -> None:
    """Amending and replacement by-laws for the chapters in build/documents.jsonl (run `extract` and
    `chunk` first). A replacement in force counts as its chapter, consolidated on its in-force date."""
    if not config.DOCUMENTS.exists():
        raise SystemExit(f"{config.DOCUMENTS.relative_to(config.ROOT)} is missing: run extract and chunk first")
    documents = [json.loads(line) for line in config.DOCUMENTS.read_text(encoding="utf-8").splitlines()]
    consolidated = {d["id"].removeprefix("tmc:"): d["consolidated_as_of"] for d in documents if d["kind"] == "chapter"}
    consolidated |= {d["chapter"]: d["in_force"] or d["enacted"] for d in documents
                     if d["kind"] == "replacement_bylaw" and d["in_force_now"]}
    listing = []
    for year in config.BYLAW_YEARS:
        resp = requests.get(config.LAW_LIST_URL.format(year=year), timeout=60)
        resp.raise_for_status()
        listing += bylaw_list(resp.text)
    candidates = [("amending_bylaw", *c) for c in bylaw_candidates(listing, consolidated)] + \
        [("replacement_bylaw", *c) for c in replacement_candidates(listing, consolidated)]
    have = {(r.kind, r.ref): r for r in store.read_manifest()}
    print(f"{len(listing)} by-laws listed {config.BYLAW_YEARS[0]}–{config.BYLAW_YEARS[-1]}, "
          f"{len(candidates)} name a snapshot chapter")
    for kind, num, url, _, chapters in candidates:
        ref = f"bylaw-{num}"
        if (kind, ref) in have and have[kind, ref].local_path.exists():
            continue
        resp = requests.get(url, timeout=600)
        resp.raise_for_status()
        row = store.put(resp.content, store.ManifestRow(
            sha256="", kind=kind, ref=ref, parent_ref="", source_url=url,
            obtained_by="script",
            obtained_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            last_modified=resp.headers.get("Last-Modified", ""), etag=resp.headers.get("ETag", ""),
            bytes=0, content_type=resp.headers.get("Content-Type", ""), encoding="",
        ))
        print(f"{ref} ({kind}, Ch {', '.join(chapters)}): {row.bytes} bytes, sha256 {row.sha256[:12]}…")
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
