"""Amending by-laws: an extracted stream → (document, chunks), one chunk per operative clause.

CHUNKING.md, "Rules: amending by-laws". A clause over the ceiling splits at its lettered items
(A., B., … or a., b., …), packed up to the ceiling. Each chunk records the § numbers its
instructions name (`amends`) and whether every instruction touches only a Schedule or
Appendix (`schedule_only`). Resolving those against the snapshot's chapters, and dropping
by-laws already folded in, is the linker's job (`ingest/link.py`). Text after the signature
(attachments: new schedules, maps, whole new chapters) is not in the snapshot.
"""
from __future__ import annotations

import re

from . import store
from .chunk import (CEILING, HEADER_BAND, MARGIN, MIN_BODY_SIZE, Block, _succ, iso_date, pack, pack_flat,
                    render, size, to_blocks, tokens)

BYLAW_HEAD = re.compile(r"^BY-LAW\s+(?:No\.\s*)?(\d+-\d{4})\b")
ENACTS = re.compile(r"\benacts\b(?:\s+as\s+follows)?\s*:?\s*$")
PASSED = re.compile(r"^Enacted and passed (?:on |this )?(.*?)\.?\s*$")
DATE = re.compile(r"([A-Z][a-z]+ \d{1,2})[,.] (\d{4})")   # "November 9. 2023" happens
IN_FORCE = re.compile(r"\bcomes? into (?:force|effect) on ([A-Z][a-z]+ \d{1,2}, \d{4})")
CLAUSE = re.compile(r"^(\d+)\.\s")
ITEM = re.compile(r"^(?:([A-Za-z])(\.\d+)?\.|\(([a-z])\))\s")
# Lead-in words of an instruction ("Deleting § 608-1 …", "… is amended by adding …").
INSTRUCTION = re.compile(r"\b(?:amend|delet|add(?:s|ed|ing)?\b|insert|replac|repeal|renumber|strik|substitut)", re.I)
# A § number: 629-38F, 610-6.2, 743-7C. Never the by-law's own kind of number ("By-law 823-2025").
SECTION_REF = re.compile(r"(?<![\w.-])(?<!By-law )(?<!Bylaw )(?<!By-Law )(\d{1,4}[A-Z]?-\d+(?:\.\d+)*[A-Z]?)"
                         r"((?:\.?[A-Z](?:\.\d+)?)?(?:\(\w{1,4}\))*)(?![\w-])")
SCHEDULE_REF = re.compile(r"\b(?:Schedule|Appendix|SCHEDULE|APPENDIX)\b")
QUOTE_START = re.compile(r"^[\"“”']")
QUOTED = re.compile(r"“[^”]*”|\"[^\"]*\"")      # words an instruction inserts or deletes
CHAPTER_REF = re.compile(r"\bChapter\s+(\d+[A-Z]?)\b")
NOT_OPERATIVE = re.compile(r"^\d+\.\s+(?:This|The)\s+[Bb]y-?law\b.*\b(?:into (?:force|effect)|cited as|short title)", re.S)


def flatten_layout_tables(records: list[dict]) -> list[dict]:
    """Some by-laws lay their clauses out in a table, one text cell per row. Those become lines
    again (indented by column, an empty row a paragraph break); real tables stay tables."""
    out = []
    for r in records:
        if r["kind"] != "table" or any(sum(bool(c) for c in row) > 1 for row in r["rows"]):
            out.append(r)
            continue
        top = r["top"]
        for row in r["rows"]:
            col = next((i for i, c in enumerate(row) if c), None)
            if col is None:
                top += 14
                continue
            out.append({"kind": "line", "page": r["page"], "top": top, "bottom": top + 12,
                        "x0": r["x0"] + 36 * col, "size": 12.0, "bold": False, "text": row[col]})
            top += 13.8
    return out


def parse_amends(text: str) -> tuple[list[str], list[str], bool]:
    """(§ references the instructions name, in order: '629-38F', '354-3.2B(7)'; chapters they name;
    schedule_only). Only instruction paragraphs count, never the quoted text they insert.
    schedule_only: there are instructions with a target, and every one names a Schedule or Appendix."""
    refs: list[str] = []
    chapters: list[str] = []
    targeted = schedule = 0
    for para in text.split("\n\n"):
        para = re.sub(r"^\d+\.\s+|^(?:[A-Za-z](?:\.\d+)?\.|\([a-z]\))\s+", "", para.strip())
        if QUOTE_START.match(para) or not INSTRUCTION.search(para):
            continue
        para = QUOTED.sub("", para)
        found = [m[1] + m[2] for m in SECTION_REF.finditer(para)]
        on_schedule = bool(SCHEDULE_REF.search(para))
        if found or on_schedule:
            targeted += 1
            schedule += on_schedule
        if not on_schedule:
            refs += [f for f in dict.fromkeys(found) if f not in refs]
        chapters += [ch for ch in dict.fromkeys(CHAPTER_REF.findall(para)) if ch not in chapters]
    return refs, chapters, bool(targeted) and schedule == targeted


def items(blocks: list[Block]) -> list[tuple[str, list[Block]]]:
    """A clause's lettered items (A., B., … or a., b., … or (a), (b), …) at the indent of its first
    item; inserted text quoting its own A., B. sits deeper and stays inside its item."""
    first = next((b for b in blocks if b.kind == "para" and (m := ITEM.match(b.text))
                  and (m[1] or m[3]) in ("A", "a")), None)
    if first is None:
        return []
    starts, prev = [], None
    for i, b in enumerate(blocks):
        if b.kind != "para" or abs(b.x0 - first.x0) > 3 or not (m := ITEM.match(b.text)):
            continue
        base, ins = m[1] or m[3], m[2] or ""
        ok = base in ("A", "a") and not ins if prev is None else (
            (base == prev and ins) or (base == _succ(prev) and not ins))
        if ok:
            starts.append((i, base + ins))
            prev = base
    if len(starts) < 2:
        return []
    bounds = [0] + [i for i, _ in starts[1:]] + [len(blocks)]
    return [(label, blocks[bounds[k]:bounds[k + 1]]) for k, (_, label) in enumerate(starts)]


def chunk_amending_bylaw(records: list[dict], row: store.ManifestRow) -> tuple[dict, list[dict]]:
    """One by-law's extracted stream → (document, chunks). Breadcrumbs and sublabels are drafts
    the linker completes once it knows which chapters and §§ the by-law really amends."""
    lines = [r for r in flatten_layout_tables([r for r in records if r["kind"] != "page"])
             if not (r["page"] > 1 and r["top"] < HEADER_BAND)
             and (r["kind"] == "table" or r["size"] >= MIN_BODY_SIZE)]
    text_of = lambda r: r.get("text", "")

    number = row.ref.removeprefix("bylaw-")
    heads = [(i, m[1]) for i, r in enumerate(lines) if (m := BYLAW_HEAD.match(text_of(r)))]
    # the heading names the by-law's own number, except where the PDF misprints it (297-2026: "297-2025")
    head = next((i for i, n in heads if n == number), heads[0][0] if heads else None)
    if head is None:
        raise SystemExit(f"{row.ref}: no 'BY-LAW {number}' heading")
    title_lines = []
    for r in lines[head + 1:]:
        if r["kind"] != "line" or not r["bold"]:
            break
        title_lines.append(r["text"])
    title = re.sub(r"\s+", " ", " ".join(title_lines)).strip()

    passed = next((i for i, r in enumerate(lines) if i > head and PASSED.match(text_of(r))), None)
    if passed is None or not (d := DATE.search(lines[passed]["text"])):
        raise SystemExit(f"{row.ref}: no 'Enacted and passed on <date>' line")
    enacted = iso_date(f"{d[1]}, {d[2]}")
    start = next((i + 1 for i, r in enumerate(lines[:passed]) if i > head and ENACTS.search(text_of(r))
                  and not text_of(r).startswith("Whereas")), None)
    if start is None:
        start = next((i for i, r in enumerate(lines[:passed]) if i > head and r["kind"] == "line"
                      and r["x0"] < MARGIN and text_of(r).startswith("1. ")), None)
    if start is None:
        raise SystemExit(f"{row.ref}: no enacting line and no clause 1")
    operative = lines[start:passed]

    clauses: list[tuple[str, list[dict]]] = []
    for r in operative:
        m = CLAUSE.match(text_of(r)) if r["kind"] == "line" and r["x0"] < MARGIN else None
        if m and m[1] == (str(int(clauses[-1][0]) + 1) if clauses else "1"):
            clauses.append((m[1], [r]))
        elif clauses:
            clauses[-1][1].append(r)
        else:
            clauses.append(("1", [r]))    # an unnumbered single-clause by-law

    whole = render(to_blocks(operative))
    in_force = next((iso_date(m[1]) for m in IN_FORCE.finditer(whole)), None)
    in_force = in_force if in_force and in_force != enacted else None

    document = {
        "id": f"bl:{number}", "kind": "amending_bylaw", "family": "rules",
        "title": f"By-law {number}: {title}", "source_url": row.source_url, "sha256": row.sha256,
        "fetched_at": row.obtained_at[:10], "consolidated_as_of": None,
        "enacted": enacted, "in_force": in_force,
        "item_id": None, "status_stamp": None, "decision_date": None, "bylaws": None,
        "number": number, "short_title": title,
    }

    chunks = []
    for n, clause_lines in clauses:
        blocks = to_blocks(clause_lines)
        if NOT_OPERATIVE.match(render(blocks)):
            continue
        if size(blocks) <= CEILING:
            pieces = [(None, None, blocks)]
        elif units := items(blocks):
            pieces = pack(units, lambda label, bs: pack_flat(bs, label))
        else:
            pieces = pack_flat(blocks, None)
        seen: dict[str, int] = {}
        for first, last, bs in pieces:
            rng = None if first is None else first if first == last else f"{first}–{last}"
            cid = f"bl:{number}:cl{n}"
            if len(pieces) > 1:
                key = "" if first is None else first if first == last else f"{first}-{last}"
                part = seen[key] = seen.get(key, 0) + 1
                if not first or part > 1:   # same label twice: one item split by paragraph
                    key = f"{key}p{part}" if key else f"p{part}"
                    rng = f"{rng}, part {part}" if rng else f"part {part}"
                cid += f":{key}"
            body = render(bs)
            amends, chapters, schedule_only = parse_amends(body)
            pages = [b.page for b in bs]
            label = f"By-law {number} cl. {n}" + (f" {rng}" if rng else "")
            chunks.append({
                "id": cid, "document_id": document["id"],
                "family": "rules", "kind": "amending_bylaw",
                "chapter": None, "article": None, "section": None,
                "subsection_range": rng, "stage": None, "heading": title,
                "breadcrumb": f"[By-law {number} › {title}]",
                "body": body, "label": label, "sublabel": "",
                "href": f"{row.source_url}#page={min(pages)}",
                "amended_by": [], "amended_since": [],
                "amends": amends, "chapters": chapters, "schedule_only": schedule_only,
                "page_start": min(pages), "page_end": max(pages),
                "tokens": tokens(body),
            })
    return document, chunks
