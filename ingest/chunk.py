"""chunk: build/text/ → build/documents.jsonl + build/chunks.jsonl.

Code chapter strategy, basic form: one chunk per §, no splitting yet (CHUNKING.md rules 1–3).
Output is deterministic: the same input yields byte-identical files.
"""
from __future__ import annotations

import json
import re
from datetime import datetime

import tiktoken

from . import config, store

BAND = 62                 # running header / footer height, pt
MIN_BODY_SIZE = 11        # smaller print is footnotes and the General References box
PARA_GAP = 6              # vertical gap (pt) between lines that starts a new paragraph

SECTION = re.compile(r"^§\s*(\d+[A-Z]?-\d+(?:\.\d+)*[A-Z]?)\.?\s+(.*)")
ARTICLE = re.compile(r"^ARTICLE\s+([IVXLC\d]+[A-Z]?)\b", re.I)
CHAPTER_HEADER = re.compile(r"^CHAPTER\s+(\d+[A-Z]?),\s*(.+)$")
FOOTER_DATE = re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4})\s*$")
NOTE = re.compile(r"\[[^\]]*\]")
BYLAW = re.compile(r"By-law\s+(\d+-\d{4})")

SMALL_WORDS = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to"}

_enc = tiktoken.get_encoding("cl100k_base")


def tokens(text: str) -> int:
    return len(_enc.encode(text))


def title_case(s: str) -> str:
    words = s.lower().split()
    return " ".join(w if i and w in SMALL_WORDS else w[:1].upper() + w[1:] for i, w in enumerate(words))


def iso_date(text: str) -> str:
    return datetime.strptime(text, "%B %d, %Y").strftime("%Y-%m-%d")


def join_lines(lines: list[dict]) -> str:
    """Wrapped lines → paragraphs separated by a blank line; tables as markdown."""
    paras: list[str] = []
    prev = None
    for ln in lines:
        if ln["kind"] == "table":
            paras.append(table_markdown(ln["rows"]))
            prev = None
            continue
        text = ln["text"]
        if prev is None:
            new_para = True
        elif ln["page"] == prev["page"]:
            new_para = ln["top"] - prev["bottom"] > PARA_GAP
        else:
            new_para = prev["text"].endswith((".", ":", ";", "]"))
        if new_para:
            paras.append(text)
        elif re.search(r"\w-$", paras[-1]):
            paras[-1] += text
        else:
            paras[-1] += " " + text
        prev = ln
    return "\n\n".join(paras)


def table_markdown(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    cell = lambda s: s.replace("|", "\\|")
    out = ["| " + " | ".join(map(cell, rows[0])) + " |", "|" + " --- |" * width]
    out += ["| " + " | ".join(map(cell, r)) + " |" for r in rows[1:]]
    return "\n".join(out)


def chunk_code_chapter(records: list[dict], row: store.ManifestRow) -> tuple[dict, list[dict]]:
    heights = {r["page"]: r["height"] for r in records if r["kind"] == "page"}
    content = [r for r in records if r["kind"] != "page"]

    def band(r: dict) -> str:
        if r["top"] < BAND:
            return "header"
        if r["top"] > heights[r["page"]] - BAND:
            return "footer"
        return "body"

    chapter = title = consolidated = None
    for r in content:
        if r["kind"] != "line":
            continue
        if band(r) == "header" and (m := CHAPTER_HEADER.match(r["text"])):
            chapter, title = chapter or m[1], title or title_case(m[2])
        if band(r) == "footer" and (m := FOOTER_DATE.search(r["text"])):
            consolidated = consolidated or iso_date(m[1])
    if not chapter:
        raise SystemExit(f"{row.ref}: no 'CHAPTER N, TITLE' running header")

    body = [r for r in content
            if band(r) == "body" and (r["kind"] == "table" or r["size"] >= MIN_BODY_SIZE)]

    def is_heading(r: dict):
        return r["kind"] == "line" and r["bold"] and r["x0"] < 80 and SECTION.match(r["text"])

    # The page-1 table of contents repeats every § heading; the body starts at the first repeat.
    seen, start = set(), 0
    for i, r in enumerate(body):
        if m := is_heading(r):
            if m[1] in seen:
                start = i
                break
            seen.add(m[1])

    sections: list[dict] = []
    article = None
    pending_article = None
    for i, r in enumerate(body):
        if r["kind"] == "line" and (m := ARTICLE.match(r["text"])) and r["x0"] > 150:
            pending_article = f"Article {m[1]}"
            continue
        if pending_article and r["kind"] == "line":
            article, pending_article = f"{pending_article} {r['text']}", None
            continue
        if i < start:
            continue
        if m := is_heading(r):
            sections.append({"section": m[1], "heading": m[2].rstrip(". "), "article": article,
                             "page": r["page"], "lines": []})
        elif sections:
            sections[-1]["lines"].append(r)

    document = {
        "id": f"tmc:{chapter}", "kind": "chapter", "family": "rules",
        "title": f"Ch {chapter} {title}", "source_url": row.source_url, "sha256": row.sha256,
        "fetched_at": row.obtained_at[:10], "consolidated_as_of": consolidated,
        "enacted": None, "in_force": None,
        "item_id": None, "status_stamp": None, "decision_date": None, "bylaws": None,
    }

    chunks = []
    for s in sections:
        text = join_lines(s["lines"])
        if not text:
            continue
        pages = [ln["page"] for ln in s["lines"]]
        trail = " › ".join(p for p in ("Toronto Municipal Code", f"Ch {chapter} {title}", s["article"],
                                       f"§ {s['section']} {s['heading']}") if p)
        amended_by = sorted({b for note in NOTE.findall(text) for b in BYLAW.findall(note)})
        chunks.append({
            "id": f"tmc:{s['section']}", "document_id": document["id"],
            "family": "rules", "kind": "chapter",
            "chapter": chapter, "article": s["article"],
            "section": s["section"], "subsection_range": None, "stage": None, "heading": s["heading"],
            "breadcrumb": f"[{trail}]\n[consolidated as of {consolidated}]",
            "body": text,
            "label": f"Ch {chapter} § {s['section']}",
            "sublabel": f"consolidated {consolidated}",
            "href": f"{row.source_url}#page={s['page']}",
            "amended_by": amended_by, "amended_since": [],
            "page_start": s["page"], "page_end": max(pages, default=s["page"]),
            "tokens": tokens(text),
        })
    return document, chunks


def _dump(rec: dict) -> str:
    return json.dumps(rec, ensure_ascii=False, sort_keys=True)


def chunk() -> None:
    documents, chunks = [], []
    for row in sorted(store.read_manifest(), key=lambda r: r.ref):
        if row.kind != "code_chapter":
            continue
        path = config.TEXT_DIR / f"{row.ref}.jsonl"
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        doc, cs = chunk_code_chapter(records, row)
        documents.append(doc)
        chunks += cs
        print(f"{row.ref}: {len(cs)} chunks, {sum(c['tokens'] for c in cs)} tokens")

    ids = [c["id"] for c in chunks]
    if dupes := sorted({i for i in ids if ids.count(i) > 1}):
        raise SystemExit(f"duplicate chunk ids: {dupes}")
    config.BUILD.mkdir(parents=True, exist_ok=True)
    config.DOCUMENTS.write_text("".join(_dump(d) + "\n" for d in documents), encoding="utf-8", newline="\n")
    config.CHUNKS.write_text("".join(_dump(c) + "\n" for c in chunks), encoding="utf-8", newline="\n")
