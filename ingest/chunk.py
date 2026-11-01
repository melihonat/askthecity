"""chunk: build/text/ → build/documents.jsonl + build/chunks.jsonl (+ build/skipped.jsonl).

Code chapter rules, CHUNKING.md: one chunk per §; a § over the ceiling splits at its
subsections (A., then (1), then (a)), packing consecutive siblings up to the ceiling;
definitions split by whole terms; tables are markdown, split by rows with the header repeated.
Output is deterministic: the same input yields byte-identical files.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime

import tiktoken

from . import config, store

CEILING = 800             # body tokens per chunk (cl100k); no minimum
HEADER_BAND = 62          # running header height, pt
FOOTER_BAND = 75          # footers sit 33–68 pt from the bottom; body text reaches 71
MIN_BODY_SIZE = 11        # smaller print is footnotes and the General References box
PARA_GAP = 6              # vertical gap (pt) between lines that starts a new paragraph
MARGIN = 80               # x0 below this is the left margin

SECTION = re.compile(r"^§\s*(\d+[A-Z]?-\d+(?:\.\d+)*[A-Z]?)\.?\s+(.*)")
ARTICLE = re.compile(r"^ARTICLE\s+([IVXLC\d]+[A-Z]?)\b", re.I)
CHAPTER_HEADER = re.compile(r"^CHAPTER\s+(\d+[A-Z]?),?\s+(.+)$")
FOOTER = re.compile(r"^\d+[A-Z]?-\d+[A-Z]?\b")
FOOTER_DATE = re.compile(r"([A-Z][a-z]+ \d{1,2}, \d{4}|\d{4}-\d{2}-\d{2})\s*$")
RESERVED = re.compile(r"^\(?RESERVED\)?$", re.I)
NOTE = re.compile(r"\[[^\]]*\]")
BYLAW = re.compile(r"By-law\s+(\d+-\d{4})")
DEFINITIONS = re.compile(r"\bdefinitions?\b", re.I)
TERM = re.compile(r"^(\S.{0,79}?)\s+[-–—]\s+\S")
SCHEDULE = re.compile(r"^(SCHEDULE|Schedule|APPENDIX|Appendix)\s+([A-Z0-9]{1,3}(?:-\d+)?)\b")
SENTENCE = re.compile(r"(?<=[.;:])\s+")

# Subsection levels, outermost first: A. (and A.1.), 1., (1), (a).
LEVELS = [
    (re.compile(r"^([A-Z]{1,2})(\.\d+)?\.\s"), "{}"),
    (re.compile(r"^(\d+)(\.\d+)?\.\s"), "{}"),
    (re.compile(r"^\((\d+)(\.\d+)?\)\s"), "({})"),
    (re.compile(r"^\(([a-z]{1,2})(\.\d+)?\)\s"), "({})"),
]
FIRST = {"A", "1", "a"}

SMALL_WORDS = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to"}

_enc = tiktoken.get_encoding("cl100k_base")


def tokens(text: str) -> int:
    return len(_enc.encode(text))


def title_case(s: str) -> str:
    words = s.lower().split()
    return " ".join(w if i and w in SMALL_WORDS else w[:1].upper() + w[1:] for i, w in enumerate(words))


def iso_date(text: str) -> str:
    return text if text[0].isdigit() else datetime.strptime(text, "%B %d, %Y").strftime("%Y-%m-%d")


# ── blocks: paragraphs and tables ────────────────────────────────────────────────────────

@dataclass
class Block:
    kind: str                       # para | table
    page: int
    x0: float = 0.0
    text: str = ""
    rows: list[list[str]] | None = None

    def render(self) -> str:
        return self.text if self.kind == "para" else table_markdown(self.rows or [])


def to_blocks(lines: list[dict]) -> list[Block]:
    """Wrapped lines → paragraphs; table records → table blocks (over-ceiling tables split by rows)."""
    out: list[Block] = []
    prev = None
    for ln in lines:
        if ln["kind"] == "table":
            out.append(Block("table", ln["page"], rows=[r for r in unfold_pairs(ln["rows"]) if any(r)]))
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
            out.append(Block("para", ln["page"], ln["x0"], text))
        elif re.search(r"\w-$", out[-1].text):
            out[-1].text += text
        else:
            out[-1].text += " " + text
        prev = ln
    return out


def render(blocks: list[Block]) -> str:
    return "\n\n".join(b.render() for b in blocks)


def size(blocks: list[Block]) -> int:
    return tokens(render(blocks))


def table_markdown(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    cell = lambda s: s.replace("|", "\\|")
    out = ["| " + " | ".join(map(cell, rows[0])) + " |", "|" + " --- |" * width]
    out += ["| " + " | ".join(map(cell, r)) + " |" for r in rows[1:]]
    return "\n".join(out)


def unfold_pairs(rows: list[list[str]]) -> list[list[str]]:
    """A two-column-pair layout (Parameter | Limit | Parameter | Limit) → one row per parameter."""
    if not rows or len(rows[0]) < 4 or len(rows[0]) % 2:
        return rows
    half = len(rows[0]) // 2
    head = [c.lower() for c in rows[0]]
    if not all(head[:half]) or head[:half] != head[half:]:
        return rows
    body = rows[1:]
    return [rows[0][:half], *(r[:half] for r in body), *(r[half:] for r in body if any(r[half:]))]


# ── splitting a § over the ceiling ───────────────────────────────────────────────────────

def _succ(base: str) -> str:
    if base.isdigit():
        return str(int(base) + 1)
    if base[-1] in "zZ":
        return ("a" if base.islower() else "A") * (len(base) + 1)
    return base[:-1] + chr(ord(base[-1]) + 1)


def labelled_units(blocks: list[Block], level: int, prefix: str) -> tuple[int, list[tuple[str, list[Block]]]]:
    """Units at one subsection level, and the block index where the sequence starts. A paragraph
    starts a unit only if its label continues the sequence (A, B, B.1, C…), so stray matches stay
    text. The lead-in joins the first unit."""
    pattern, fmt = LEVELS[level]
    starts: list[tuple[int, str]] = []
    prev = None
    for i, b in enumerate(blocks):
        if b.kind != "para" or not (m := pattern.match(b.text)):
            continue
        if level == 0 and b.x0 >= MARGIN:
            continue
        base, ins = m[1], m[2] or ""
        ok = (base in FIRST and not ins) if prev is None else (
            (base == prev and ins) or (base == _succ(prev) and not ins))
        if ok:
            starts.append((i, prefix + fmt.format(base + ins)))
            prev = base
    if len(starts) < 2:
        return 0, []
    bounds = [0] + [i for i, _ in starts[1:]] + [len(blocks)]
    return starts[0][0], [(label, blocks[bounds[k]:bounds[k + 1]]) for k, (_, label) in enumerate(starts)]


def term_units(blocks: list[Block]) -> list[tuple[str, list[Block]]]:
    """Definitions: one unit per defined term; a term's indented list stays with it."""
    matches = [(i, m[1], b.x0) for i, b in enumerate(blocks) if b.kind == "para" and (m := TERM.match(b.text))]
    if not matches:
        return []
    xs = [x for _, _, x in matches]
    x0 = max(sorted(set(xs)), key=xs.count)    # terms share an indent; nested items don't
    starts = [(i, term) for i, term, x in matches if abs(x - x0) < 3]
    if len(starts) < 2:
        return []
    bounds = [0] + [i for i, _ in starts[1:]] + [len(blocks)]
    return [(term, blocks[bounds[k]:bounds[k + 1]]) for k, (_, term) in enumerate(starts)]


Piece = tuple[str | None, str | None, list[Block]]     # first label, last label, blocks


def pack(units: list[tuple[str | None, list[Block]]], split_unit) -> list[Piece]:
    """Consecutive siblings packed up to the ceiling; a sibling over it goes to split_unit."""
    pieces: list[Piece] = []
    run: list[tuple[str | None, list[Block]]] = []

    def flush():
        if run:
            pieces.append((run[0][0], run[-1][0], [b for _, bs in run for b in bs]))
            run.clear()

    for label, bs in units:
        if size(bs) > CEILING:
            flush()
            pieces += split_unit(label, bs)
        else:
            if run and size([b for _, r in run for b in r] + bs) > CEILING:
                flush()
            run.append((label, bs))
    flush()
    return pieces


def split_blocks(blocks: list[Block], prefix: str = "", level: int = 0) -> list[Piece]:
    """Blocks over the ceiling → pieces at the outermost subsection level: the one whose sequence
    starts first (a "1." list can sit inside a "(8)", so the pattern order alone can't tell)."""
    found = [(start, lv, units) for lv in range(level, len(LEVELS))
             for start, units in [labelled_units(blocks, lv, prefix)] if units]
    if found:
        _, lv, units = min(found, key=lambda f: f[:2])
        return pack(units, lambda label, bs, lv=lv: split_blocks(bs, label, lv + 1))
    return pack_flat(blocks, prefix or None)


def pack_flat(blocks: list[Block], label: str | None) -> list[Piece]:
    """No further structure: paragraphs packed whole, tables row by row. A table carried over
    into the next chunk repeats its header row, and a lead-in keeps the table's first rows."""
    pieces: list[Piece] = []
    run: list[Block] = []

    def flush():
        if run:
            pieces.append((label, label, run[:]))
            run.clear()

    for b in blocks:
        if b.kind == "table" and b.rows and size([b]) > CEILING:
            head, filling = b.rows[0], False
            for r in b.rows[1:]:
                if filling:
                    grown = Block("table", b.page, rows=[*run[-1].rows, r])
                    if size([*run[:-1], grown]) <= CEILING:
                        run[-1] = grown
                        continue
                    flush()
                start = Block("table", b.page, rows=[head, r])
                if run and size([*run, start]) > CEILING:
                    flush()
                run.append(start)
                filling = True
            continue
        for part in split_para(b) if size([b]) > CEILING else [b]:
            if run and size([*run, part]) > CEILING:
                # a table's title or lead-in ("Table 2 - Limits …", "… as follows:") moves with it
                title = run.pop() if part.kind == "table" and len(run) > 1 and run[-1].kind == "para" \
                    and not run[-1].text.endswith(".") and tokens(NOTE.sub("", run[-1].text)) <= 40 else None
                flush()
                run.extend([title] if title else [])
            run.append(part)
    flush()
    return pieces


def split_para(b: Block) -> list[Block]:
    """A single paragraph over the ceiling: whole sentences, and whole words inside a sentence
    that is itself over (a table the PDF lays out as plain text)."""
    if b.kind != "para":
        return [b]
    parts = [w for s in SENTENCE.split(b.text) for w in (s.split(" ") if tokens(s) > CEILING else [s])]
    out = [""]
    for part in parts:
        if out[-1] and tokens(f"{out[-1]} {part}") > CEILING:
            out.append("")
        out[-1] = f"{out[-1]} {part}".lstrip()
    return [Block("para", b.page, b.x0, t) for t in out]


def split_section(blocks: list[Block], definitions: bool) -> list[Piece]:
    if size(blocks) <= CEILING:
        return [(None, None, blocks)]
    if definitions and (units := term_units(blocks)):
        return pack(units, lambda term, bs: split_blocks(bs, term, 1))
    return split_blocks(blocks)


def range_text(first: str | None, last: str | None, terms: bool) -> str | None:
    if first is None:
        return None
    if first == last:
        return first
    return f"{first} – {last}" if terms else f"{first}–{last}"


def range_id(first: str | None, last: str | None, terms: bool) -> str:
    if terms:
        return re.sub(r"[^a-z0-9]+", "-", (first or "").lower()).strip("-")
    return first if first == last else f"{first}-{last}"


# ── a Code chapter ───────────────────────────────────────────────────────────────────────

def noted_bylaws(records: list[dict]) -> list[str]:
    """Every by-law named in the chapter's bracketed notes ([Amended …], [Added …], [History: …]),
    anywhere in the PDF, footnotes included. Notes wrap: "By-law 600-" / "2023]"."""
    parts: list[str] = []
    for r in records:
        if r["kind"] == "line":
            wrapped = parts and re.search(r"\w-$", parts[-1])
            parts.append(r["text"] if wrapped else " " + r["text"])
    return sorted({b for note in NOTE.findall("".join(parts)) for b in BYLAW.findall(note)})


def chunk_code_chapter(records: list[dict], row: store.ManifestRow) -> tuple[dict, list[dict]] | None:
    """One chapter's extracted stream → (document, chunks), or None for a "Reserved" stub."""
    heights = {r["page"]: r["height"] for r in records if r["kind"] == "page"}
    content = [r for r in records if r["kind"] != "page"]

    def band(r: dict) -> str:
        if r["top"] < HEADER_BAND:
            return "header"
        if r["top"] > heights[r["page"]] - FOOTER_BAND and r["kind"] == "line" and FOOTER.match(r["text"]):
            return "footer"
        return "body"

    if any(r["kind"] == "line" and RESERVED.match(r["text"]) for r in content) and \
            not any(r["kind"] == "line" and SECTION.match(r["text"]) for r in content):
        return None

    chapter = row.ref.removeprefix("ch-")
    title = consolidated = None
    for r in content:
        if r["kind"] != "line":
            continue
        if band(r) == "header" and r["text"] != "TORONTO MUNICIPAL CODE":
            # "CHAPTER 591, NOISE", "CHAPTER 142 LOCAL APPEAL BODY" or just "TAXATION, VACANT HOME TAX"
            m = CHAPTER_HEADER.match(r["text"])
            if m and m[1] != chapter:
                raise SystemExit(f"{row.ref}: running header names Chapter {m[1]}")
            title = title or title_case(m[2] if m else r["text"])
        if band(r) == "footer" and (m := FOOTER_DATE.search(r["text"])):
            consolidated = consolidated or iso_date(m[1])
    if not title:
        raise SystemExit(f"{row.ref}: no running header with the chapter title")

    body = [r for r in content
            if band(r) == "body" and (r["kind"] == "table" or r["size"] >= MIN_BODY_SIZE)]

    document = {
        "id": f"tmc:{chapter}", "kind": "chapter", "family": "rules",
        "title": f"Ch {chapter} {title}", "source_url": row.source_url, "sha256": row.sha256,
        "fetched_at": row.obtained_at[:10], "consolidated_as_of": consolidated,
        "enacted": None, "in_force": None,
        "item_id": None, "status_stamp": None, "decision_date": None, "bylaws": None,
        "chapter": chapter, "noted_bylaws": noted_bylaws(content),
    }
    dated = f"consolidated as of {consolidated}" if consolidated else "consolidation date not printed"
    sublabel = f"consolidated {consolidated}" if consolidated else "consolidation date not printed"
    chunks = chapter_chunks(parse_sections(body), chapter=chapter, title=title, document_id=document["id"],
                            kind="chapter", id_prefix="tmc:", trail=["Toronto Municipal Code", f"Ch {chapter} {title}"],
                            dated=dated, sublabel=sublabel, url=row.source_url)
    return document, chunks


def parse_sections(body: list[dict]) -> list[dict]:
    """A chapter's body records (running headers, footers and small print gone) → one dict per §:
    number, heading, article, first page and its lines."""
    def is_heading(r: dict):
        return r["kind"] == "line" and r["bold"] and r["x0"] < MARGIN and SECTION.match(r["text"])

    def wraps(prev: dict, r: dict, heading: str) -> bool:
        """r is the second line of a § heading that didn't end with a period."""
        return (is_heading(prev) and prev["text"].rstrip()[-1:] not in ".]" and r["kind"] == "line"
                and r["bold"] and r["x0"] < MARGIN and r["page"] == prev["page"]
                and r["top"] - prev["bottom"] <= PARA_GAP and not SECTION.match(r["text"])
                and not r["text"].startswith("[") and bool(heading))

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
    pending_article = False
    in_article_head = False   # an article's title and [Adopted …] note, up to its first §
    for i, r in enumerate(body):
        if r["kind"] == "line" and (m := ARTICLE.match(r["text"])) and r["x0"] > 150:
            pending_article, article = True, f"Article {m[1]}"
            continue
        if pending_article and r["kind"] == "line":
            article, pending_article, in_article_head = f"{article} {r['text']}", False, True
            continue
        if i < start:
            continue
        if sections and not sections[-1]["lines"] and wraps(body[i - 1], r, sections[-1]["heading"]):
            sections[-1]["heading"] += " " + r["text"].strip().rstrip(". ")   # "… parts of" / "buildings."
            continue
        if m := is_heading(r):
            in_article_head = False
            # A note that starts on the heading line ("… Maps [Added 2021-04-") belongs to the body.
            heading, bracket, note = m[2].partition("[")
            if bracket and "]" in note:
                heading, note = m[2], ""
            lines = [{**r, "text": f"[{note}"}] if note else []
            sections.append({"section": m[1], "heading": heading.strip().rstrip(". "), "article": article,
                             "page": r["page"], "lines": lines})
        elif sections and not in_article_head:
            sections[-1]["lines"].append(r)
    return sections


def chapter_chunks(sections: list[dict], *, chapter: str, title: str, document_id: str, kind: str,
                   id_prefix: str, trail: list[str], dated: str, sublabel: str, url: str) -> list[dict]:
    """§§ → chunks: one per §, split over the ceiling; schedules printed after the last § are
    their own chunks. Shared by Code chapters and replacement chapters (ingest/replace.py)."""
    units = [{"section": s["section"], "heading": s["heading"], "article": s["article"],
              "id": f"{id_prefix}{s['section']}", "label": f"Ch {chapter} § {s['section']}",
              "crumb": f"§ {s['section']} {s['heading']}", "blocks": to_blocks(s["lines"])} for s in sections]

    # Schedules and appendices printed after the last § are their own units, not that §'s text.
    schedules: list[dict] = []
    if units and (cut := next((i for i, b in enumerate(units[-1]["blocks"])
                               if b.kind == "para" and SCHEDULE.match(b.text)), None)) is not None:
        rest = units[-1]["blocks"][cut:]
        units[-1]["blocks"] = units[-1]["blocks"][:cut]
        for b in rest:
            m = SCHEDULE.match(b.text) if b.kind == "para" else None
            key = f"{m[1].lower()}-{m[2].lower()}" if m else None
            if key and key not in {u["key"] for u in schedules}:   # a repeated page heading stays inside
                name = f"{m[1].title()} {m[2]}"
                heading = b.text if len(b.text) <= 100 else b.text[:100].rsplit(" ", 1)[0] + " …"
                schedules.append({"key": key, "section": None, "heading": heading, "article": None,
                                  "id": f"{id_prefix}{chapter}:{key}", "label": f"Ch {chapter} {name}",
                                  "crumb": heading, "blocks": []})
            schedules[-1]["blocks"].append(b)

    chunks = []
    for u in units + schedules:
        if not NOTE.sub("", render(u["blocks"])).strip():
            continue    # empty: schedule stubs, repealed, reserved
        terms = bool(u["section"] and DEFINITIONS.search(u["heading"]))
        pieces = split_section(u["blocks"], terms)
        seen_ranges: dict[str, int] = {}
        for first, last, bs in pieces:
            rng = range_text(first, last, terms)
            cid = u["id"]
            if len(pieces) > 1:
                key = range_id(first, last, terms) if first else ""
                seen_ranges[key] = seen_ranges.get(key, 0) + 1
                part = seen_ranges[key]
                if not first or part > 1:   # same label twice: a long unit split by paragraph
                    key, rng = f"{key}p{part}" if key else f"p{part}", f"{rng}, part {part}" if rng else f"part {part}"
                cid += f":{key}"
            text = render(bs)
            pages = [b.page for b in bs]
            trail_text = " › ".join(p for p in (*trail, u["article"], u["crumb"] + (f" ({rng})" if rng else "")) if p)
            amended_by = sorted({b for note in NOTE.findall(text) for b in BYLAW.findall(note)})
            chunks.append({
                "id": cid, "document_id": document_id,
                "family": "rules", "kind": kind,
                "chapter": chapter, "article": u["article"],
                "section": u["section"], "subsection_range": rng, "stage": None, "heading": u["heading"],
                "breadcrumb": f"[{trail_text}]\n[{dated}]",
                "body": text,
                "label": u["label"] + (f" {rng}" if rng else ""),
                "sublabel": sublabel,
                "href": f"{url}#page={min(pages)}",
                "amended_by": amended_by, "amended_since": [],
                "page_start": min(pages), "page_end": max(pages),
                "tokens": tokens(text),
            })
    return chunks


def _dump(rec: dict) -> str:
    return json.dumps(rec, ensure_ascii=False, sort_keys=True)


def chunk() -> None:
    from .bylaw import chunk_amending_bylaw
    from .link import link
    from .replace import chunk_replacement, link_replacements, supersede
    from .reports import chunk_staff_report
    from .tmmis import chunk_item_page

    today = store.snapshot_date()
    documents, chunks, skipped = [], [], []
    items: dict[str, dict] = {}
    # sorted by kind: item pages come before the staff reports that take their status stamp
    for row in sorted(store.read_manifest(), key=lambda r: (r.kind, r.ref)):
        if row.kind == "item_page":
            doc, cs = chunk_item_page(row.local_path.read_bytes().decode(row.encoding), row)
            items[row.ref] = doc
            documents.append(doc)
            chunks += cs
            print(f"{row.ref}: {len(cs)} chunks, {sum(c['tokens'] for c in cs)} tokens")
            continue
        if row.kind not in ("code_chapter", "amending_bylaw", "replacement_bylaw", "staff_report"):
            continue
        path = config.TEXT_DIR / f"{row.ref}.jsonl"
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        if row.kind == "staff_report":
            if row.parent_ref not in items:
                raise SystemExit(f"{row.ref}: parent item {row.parent_ref} has no saved page")
            doc, cs = chunk_staff_report(records, row, items[row.parent_ref])
        elif row.kind == "amending_bylaw":
            doc, cs = chunk_amending_bylaw(records, row)
        elif row.kind == "replacement_bylaw":
            doc, cs = chunk_replacement(records, row, today)
        elif (result := chunk_code_chapter(records, row)) is None:
            skipped.append({"ref": row.ref, "reason": "reserved stub"})
            print(f"{row.ref}: reserved stub, skipped")
            continue
        else:
            doc, cs = result
            if not cs:
                raise SystemExit(f"{row.ref}: no § found")
        documents.append(doc)
        chunks += cs
        print(f"{row.ref}: {len(cs)} chunks, {sum(c['tokens'] for c in cs)} tokens")

    documents, chunks, replaced = supersede(documents, chunks)
    documents, chunks, amendments, dropped = link(documents, chunks)
    amendments += link_replacements(documents, chunks)
    for s in replaced + dropped:
        print(f"{s['ref']}: {s['reason']}, skipped")
    skipped += replaced + dropped

    ids = [c["id"] for c in chunks]
    if dupes := sorted({i for i in ids if ids.count(i) > 1}):
        raise SystemExit(f"duplicate chunk ids: {dupes}")
    bylaws = sum(d["kind"] == "amending_bylaw" for d in documents)
    replacements = sum(d["kind"] == "replacement_bylaw" for d in documents)
    pages = sum(d["kind"] == "item_page" for d in documents)
    reports = sum(d["kind"] == "staff_report" for d in documents)
    print(f"{len(documents)} documents ({bylaws} amending, {replacements} replacement by-laws, {pages} item pages, "
          f"{reports} staff reports), "
          f"{len(chunks)} chunks, "
          f"{sum(c['tokens'] for c in chunks):,} tokens; {len(amendments)} amendments; {len(skipped)} skipped")
    config.BUILD.mkdir(parents=True, exist_ok=True)
    config.DOCUMENTS.write_text("".join(_dump(d) + "\n" for d in documents), encoding="utf-8", newline="\n")
    config.CHUNKS.write_text("".join(_dump(c) + "\n" for c in chunks), encoding="utf-8", newline="\n")
    config.AMENDMENTS.write_text("".join(_dump(a) + "\n" for a in amendments), encoding="utf-8", newline="\n")
    config.SKIPPED.write_text("".join(_dump(s) + "\n" for s in skipped), encoding="utf-8", newline="\n")
