"""Staff reports: the report label gate, fetch-reports, and the staff-report chunker.

A staff report is a bgrd/ file whose item-page label reads "Report from …" or "Supplementary
Report from …" (CHUNKING.md, "Decisions: what enters"). Attachments, councillor letters and
anything under /comm/ never enter. Any other label is a hand decision in
snapshot/review/report_labels.csv, which also overrides the rules (an original report a
revised one supersedes is decided `out` there).
"""
from __future__ import annotations

import csv
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from . import config, store

LABELS = config.REVIEW / "report_labels.csv"
PENDING = config.REVIEW / "report_labels.pending.csv"
LABEL_COLUMNS = ["label", "decision", "note"]

ALLOW = re.compile(r"^(Supplementary )?Report from\b")
BLOCK = re.compile(r"^(Attachments?\b|Letter from Councillor\b)")
DATED = re.compile(r"^\([^)]*\d{4}\)\s*")            # "(April 22, 2026) Report from …"
BACKGROUND_FILE = re.compile(r"/(backgroundfile-\d+)\.pdf$")


def _norm(s: str) -> str:
    return " ".join(s.split())


def report_links(html: str) -> list[tuple[str, str]]:
    """An item page → (label, url) for each file in its Background Information blocks, first
    occurrence of a url only. The label is the rpt-text span before the link, date included.
    Links inside the Summary or Motions are not background files and are never read."""
    soup = BeautifulSoup(html, "html.parser")
    out: dict[str, str] = {}
    for h4 in soup.find_all("h4"):
        if not _norm(h4.get_text(" ")).startswith("Background Information"):
            continue
        for a in h4.find_next_sibling().find_all("a", href=True):
            span = a.find_previous_sibling("span")
            out.setdefault(a["href"], _norm(span.get_text(" ")) if span else "")
    return [(label, url) for url, label in out.items()]


def gate(label: str, url: str, reviewed: dict[str, str]) -> str:
    """in | out | pending. The review file wins over the rules; /comm/ is always out."""
    if "/comm/" in url:
        return "out"
    if label in reviewed:
        return reviewed[label]
    bare = DATED.sub("", label)
    if ALLOW.match(bare):
        return "in"
    if BLOCK.match(bare):
        return "out"
    return "pending"


def read_labels() -> dict[str, str]:
    if not LABELS.exists():
        return {}
    with LABELS.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if bad := [r["label"] for r in rows if r["decision"] not in ("in", "out")]:
        raise SystemExit(f"{LABELS.name}: decision must be in or out for:\n  " + "\n  ".join(bad))
    return {r["label"]: r["decision"] for r in rows}


def decide(pages: list[tuple[str, str]], reviewed: dict[str, str]
           ) -> tuple[dict[str, tuple[str, str, str]], list[tuple[str, str, str]]]:
    """(item id, html) per saved page → (ref → (url, item id, label) for every file in, pending
    (label, item id, url)). A file linked from two items keeps the first item."""
    keep: dict[str, tuple[str, str, str]] = {}
    pending: list[tuple[str, str, str]] = []
    for item_id, html in pages:
        for label, url in report_links(html):
            decision = gate(label, url, reviewed)
            if decision == "pending":
                pending.append((label, item_id, url))
            elif decision == "in":
                if not (m := BACKGROUND_FILE.search(url)):
                    raise SystemExit(f"{item_id}: {url} is not a backgroundfile PDF")
                keep.setdefault(m[1], (url, item_id, label))
    return keep, pending


def fetch_reports() -> None:
    """Gate every bgrd/ label, stop on any pending one, then download the files decided in.
    Rows for files no longer in are dropped from the manifest."""
    rows = store.read_manifest()
    pages = [(r.ref, r.local_path.read_bytes().decode(r.encoding)) for r in rows if r.kind == "item_page"]
    keep, pending = decide(pages, read_labels())
    if pending:
        seen: dict[str, str] = {}
        for label, item_id, url in pending:
            seen.setdefault(label, f"{item_id} · {url}")
        with PENDING.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(LABEL_COLUMNS)
            w.writerows([label, "", note] for label, note in sorted(seen.items()))
        raise SystemExit(f"{len(seen)} unreviewed report labels: decide each in or out in "
                         f"{PENDING.relative_to(config.ROOT)}, move the rows to {LABELS.name}, re-run")
    PENDING.unlink(missing_ok=True)

    have = {r.ref: r for r in rows if r.kind == "staff_report"}
    if stale := sorted(set(have) - set(keep)):
        store.write_manifest([r for r in rows if not (r.kind == "staff_report" and r.ref in stale)])
        print(f"dropped {len(stale)} staff reports no longer in: {', '.join(stale)}")
    for ref, (url, item_id, _) in sorted(keep.items()):
        if (old := have.get(ref)) and old.parent_ref == item_id and old.local_path.exists():
            continue
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        row = store.put(resp.content, store.ManifestRow(
            sha256="", kind="staff_report", ref=ref, parent_ref=item_id, source_url=url,
            obtained_by="script", obtained_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            last_modified=resp.headers.get("Last-Modified", ""), etag=resp.headers.get("ETag", ""),
            bytes=0, content_type=resp.headers.get("Content-Type", ""), encoding="",
        ))
        print(f"{ref} ({item_id}): {row.bytes} bytes, sha256 {row.sha256[:12]}…")
    print(f"{len(keep)} staff reports")
    from .fetch import write_snapshot_md
    write_snapshot_md()


# ── chunks ───────────────────────────────────────────────────────────────────────────────

MAJOR_SIZE = 13.0          # the template's majors: SUMMARY, RECOMMENDATIONS, …, all caps
SUBHEAD_SIZE = 12.0        # subheads are bold at 12 or 13, not all caps
DROPPED = {"CONTACT", "SIGNATURE", "ATTACHMENT", "ATTACHMENTS"}   # attachments bundled in the PDF go with them
CAPTION = re.compile(r"^(Figure|Table|Chart|Map)\s+\d")


def heading_kind(r: dict) -> str | None:
    from .chunk import MARGIN
    if r["kind"] != "line" or not r["bold"] or r["x0"] >= MARGIN:
        return None
    text = r["text"]
    if abs(r["size"] - MAJOR_SIZE) < 0.5 and re.search(r"[A-Z]", text) and text == text.upper():
        return "major"
    if r["size"] >= SUBHEAD_SIZE and not CAPTION.match(text):
        return "sub"
    return None


def parse_report(records: list[dict]) -> list[dict]:
    """A report's extracted stream → one dict per major: {"major", "units": [[subhead | None, records]]}.
    The title block before the first major goes, and so does small print (footers, footnotes).
    A heading that wraps onto a second bold line joins it."""
    from .chunk import MIN_BODY_SIZE, PARA_GAP
    body = [r for r in records if r["kind"] == "table" or (r["kind"] == "line" and r["size"] >= MIN_BODY_SIZE)]

    def close(a: dict, b: dict) -> bool:
        return a["page"] == b["page"] and b["top"] - a["bottom"] <= PARA_GAP

    # A subhead stands alone: a bold run that the next line continues without a gap is a lead-in
    # ("Stage 1: An initial screening which …"), so the whole run stays body text.
    kinds = [heading_kind(r) for r in body]
    i = 0
    while i < len(body):
        j = i
        while kinds[i] == "sub" and j + 1 < len(body) and kinds[j + 1] == "sub" and close(body[j], body[j + 1]):
            j += 1
        if kinds[i] == "sub" and j + 1 < len(body) and kinds[j + 1] is None and close(body[j], body[j + 1]):
            kinds[i:j + 1] = [None] * (j + 1 - i)
        i = j + 1

    sections: list[dict] = []
    prev = None
    for r, kind in zip(body, kinds):
        wraps = (kind and prev is not None and prev[1] == kind and close(prev[0], r))
        if kind == "major" and wraps and sections[-1]["units"] == [[None, []]]:
            sections[-1]["major"] += " " + r["text"]
        elif kind == "major":
            sections.append({"major": r["text"], "units": [[None, []]]})
        elif not sections:
            pass
        elif kind == "sub" and wraps and not sections[-1]["units"][-1][1]:
            sections[-1]["units"][-1][0] += " " + r["text"]
        elif kind == "sub" and sections[-1]["units"][-1][0] and not sections[-1]["units"][-1][1]:
            sections[-1]["units"][-1][0] += f" › {r['text']}"   # "Background › Objectives of …"
        elif kind == "sub":
            sections[-1]["units"].append([r["text"], []])
        else:
            sections[-1]["units"][-1][1].append(r)
        prev = (r, kind)
    return sections


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def chunk_staff_report(records: list[dict], row: store.ManifestRow, item: dict) -> tuple[dict, list[dict]]:
    """One report → (document, chunks). One chunk per major; a major over the ceiling packs its
    subhead units up to the ceiling (ids :1, :2, …). Every chunk carries its item's status stamp.
    `item` is the parent item page's document."""
    from . import chunk as chunker

    num = row.ref.removeprefix("backgroundfile-")
    item_id, stamp = item["item_id"], item["status_stamp"]
    title = item["title"].removeprefix(f"Item {item_id} ")
    document = {
        "id": f"sr:{num}", "kind": "staff_report", "family": "decisions",
        "title": f"Staff report for {item_id} {title}", "source_url": row.source_url, "sha256": row.sha256,
        "fetched_at": row.obtained_at[:10], "consolidated_as_of": None, "enacted": None, "in_force": None,
        "item_id": item_id, "status_stamp": stamp, "decision_date": item["decision_date"],
        "bylaws": item["bylaws"],
    }
    chunks, slugs = [], set()
    for section in parse_report(records):
        major = section["major"]
        if major in DROPPED:
            continue
        units = []
        for sub, lines in section["units"]:
            if not (bs := chunker.to_blocks(lines)):
                continue
            if sub is not None:   # the subhead rides with its first paragraph, never alone
                if bs[0].kind == "para":
                    bs[0].text = f"{sub}\n\n{bs[0].text}"
                else:
                    bs.insert(0, chunker.Block("para", bs[0].page, text=sub))
            units.append((sub, bs))
        if not units:
            continue
        whole = [b for _, bs in units for b in bs]
        pieces = [(units[0][0], units[-1][0], whole)] if chunker.size(whole) <= chunker.CEILING \
            else chunker.pack(units, lambda label, bs: chunker.pack_flat(bs, label))
        slug = _slug(major)
        while slug in slugs:   # a major repeated in one report
            slug += "-2"
        slugs.add(slug)
        for n, (first, last, bs) in enumerate(pieces, 1):
            subs = [s for s in (first, last) if s]
            heading = " › ".join([major, " – ".join(dict.fromkeys(subs))] if subs else [major])
            split = len(pieces) > 1
            text = chunker.render(bs)
            pages = [b.page for b in bs]
            chunks.append({
                "id": f"sr:{num}:{slug}" + (f":{n}" if split else ""),
                "document_id": document["id"], "family": "decisions", "kind": "staff_report",
                "chapter": None, "article": None, "section": None, "subsection_range": None,
                "stage": None, "heading": heading,
                "breadcrumb": f"[Staff report for {item_id} · {title} › {heading}]\n[Status: {stamp}]",
                "body": text,
                "label": f"Staff report · {item_id} › {heading}" + (f" ({n}/{len(pieces)})" if split else ""),
                "sublabel": stamp,
                "href": f"{row.source_url}#page={min(pages)}",
                "amended_by": [], "amended_since": [], "page_start": min(pages), "page_end": max(pages),
                "tokens": chunker.tokens(text),
            })
    if not chunks:
        raise SystemExit(f"{row.ref}: no report sections found")
    return document, chunks
