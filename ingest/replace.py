"""Replacement by-laws: a by-law that repeals a whole chapter and replaces it with the new chapter
set out in its Schedule A (CHUNKING.md, "Whole-chapter replacement"; 1511-2025 → Ch 497,
1512-2025 → Ch 629).

The schedule runs through the Code chapter splitter as that chapter. A replacement supersedes only
once in force:

- in force on the snapshot date: its §§ take `tmc:` ids and the consolidated chapter is dropped,
  unless the consolidation already carries the by-law (then the by-law is the one dropped);
- not yet in force: the consolidated chapter stays the law; the replacement's §§ get
  `bl:<n>:<§>` ids and ride along as companion passages of the old §§, linked by a
  hand-reviewed old → new § map (`snapshot/review/section_map_<n>.csv`).

Everything but the map file I/O is pure.
"""
from __future__ import annotations

import csv
import difflib
import re
from pathlib import Path

from . import config, store
from .bylaw import read_bylaw
from .chunk import chapter_chunks, noted_bylaws, parse_sections

# "To repeal … Chapter 629, Property Standards and replace with new Chapter 629, Property Standards
# as set out in Schedule A to this by-law."
NEW_CHAPTER = re.compile(r"\breplace\b.*?\bnew Chapter (\d+[A-Z]?),?\s+(.+?)(?:,? as set out\b.*|\.)?$")
SCHEDULE_A = re.compile(r"^SCHEDULE\s+A\b")
SPACED_SECTION = re.compile(r"^(§\s*\d+[A-Z]?-)\s+(?=\d)")     # "§ 629- 4.13." in 1512-2025
MAP_COLUMNS = ["old_section", "new_section", "note"]
NEW, REPEALED = "new", "repealed"
DRAFT_MATCH = 0.6     # heading similarity a draft pairing needs


def chunk_replacement(records: list[dict], row: store.ManifestRow, snapshot_date: str) -> tuple[dict, list[dict]]:
    """One replacement by-law's extracted stream → (document, chunks) for its Schedule A chapter."""
    bl = read_bylaw(records, row)
    number = bl["number"]
    if not (m := NEW_CHAPTER.search(bl["title"])):
        raise SystemExit(f"{row.ref}: title names no new chapter: {bl['title']!r}")
    chapter, title = m[1], m[2].strip()
    effective = bl["in_force"] or bl["enacted"]
    in_force_now = effective <= snapshot_date

    after = bl["lines"][bl["passed"] + 1:]
    start = next((i for i, r in enumerate(after) if r["kind"] == "line" and r["bold"]
                  and SCHEDULE_A.match(r["text"])), None)
    if start is None:
        raise SystemExit(f"{row.ref}: no SCHEDULE A after the signature")
    body = [{**r, "text": SPACED_SECTION.sub(r"\1", r["text"])} if r["kind"] == "line" else r
            for r in after[start + 1:]]
    sections = parse_sections(body)
    if not sections:
        raise SystemExit(f"{row.ref}: no § in Schedule A")

    document = {
        "id": f"bl:{number}", "kind": "replacement_bylaw", "family": "rules",
        "title": f"By-law {number}: {bl['title']}", "source_url": row.source_url, "sha256": row.sha256,
        "fetched_at": row.obtained_at[:10], "consolidated_as_of": None,
        "enacted": bl["enacted"], "in_force": bl["in_force"],
        "item_id": None, "status_stamp": None, "decision_date": None, "bylaws": None,
        "number": number, "chapter": chapter, "chapter_title": f"Ch {chapter} {title}",
        "in_force_now": in_force_now, "noted_bylaws": sorted({number, *noted_bylaws(after)}),
    }
    status = f"in force {effective}" + ("" if in_force_now else ", not yet law")
    if in_force_now:
        id_prefix, trail = "tmc:", ["Toronto Municipal Code", f"Ch {chapter} {title}"]
        dated = f"By-law {number}, replacing the chapter · enacted {bl['enacted']} · {status}"
    else:
        id_prefix, trail = f"bl:{number}:", [f"By-law {number}", f"new Ch {chapter} {title}"]
        dated = f"enacted {bl['enacted']} · {status}"
    chunks = chapter_chunks(sections, chapter=chapter, title=title, document_id=document["id"],
                            kind="replacement_bylaw", id_prefix=id_prefix, trail=trail, dated=dated,
                            sublabel=f"By-law {number} · {status}", url=row.source_url)
    return document, chunks


def supersede(documents: list[dict], chunks: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """An in-force replacement stands in for its chapter; a pending one rides along. → (documents,
    chunks, skipped)."""
    by_id = {d["id"]: d for d in documents}
    drop: set[str] = set()
    skipped: list[dict] = []
    for doc in (d for d in documents if d["kind"] == "replacement_bylaw"):
        ref, ch = f"bylaw-{doc['number']}", doc["chapter"]
        old = by_id.get(f"tmc:{ch}")
        effective = doc["in_force"] or doc["enacted"]
        if old and (doc["number"] in old["noted_bylaws"] or (old["consolidated_as_of"] or "") >= effective):
            drop.add(doc["id"])
            skipped.append({"ref": ref, "reason": f"already folded into Ch {ch}"})
        elif doc["in_force_now"] and old:
            drop.add(old["id"])
            skipped.append({"ref": f"ch-{ch}", "reason": f"replaced by By-law {doc['number']}, in force {effective}"})
        elif not doc["in_force_now"] and not old:
            drop.add(doc["id"])
            skipped.append({"ref": ref, "reason": f"replaces Ch {ch}, which is not in the snapshot"})
    return ([d for d in documents if d["id"] not in drop],
            [c for c in chunks if c["document_id"] not in drop], skipped)


def section_headings(chunks: list[dict], document_id: str) -> dict[str, str]:
    """§ → heading, in chunk order, for one document's §§ (schedules have no §)."""
    out: dict[str, str] = {}
    for c in chunks:
        if c["document_id"] == document_id and c["section"]:
            out.setdefault(c["section"], c["heading"])
    return out


def map_problems(rows: list[dict], old: list[str], new: list[str]) -> list[str]:
    """What keeps a § map from being complete: every old § maps to a new § or says `repealed`, every
    new § maps from an old § or says `new`, and the map names no § that doesn't exist."""
    olds, news = set(old), set(new)
    problems = []
    for i, r in enumerate(rows, start=2):     # line 1 is the header
        o, n = r["old_section"].strip(), r["new_section"].strip()
        if o not in olds and o != NEW:
            problems.append(f"line {i}: old § {o!r} is not in the consolidated chapter")
        if n not in news and n != REPEALED:
            problems.append(f"line {i}: new § {n!r} is not in the replacement")
        if o == NEW and n == REPEALED:
            problems.append(f"line {i}: 'new' → 'repealed' says nothing")
    mapped_old = {r["old_section"].strip() for r in rows}
    mapped_new = {r["new_section"].strip() for r in rows}
    problems += [f"old § {s} is not mapped (to a new § or 'repealed')" for s in old if s not in mapped_old]
    problems += [f"new § {s} is not mapped (from an old § or 'new')" for s in new if s not in mapped_new]
    return problems


def draft_map(rows: list[dict], old: dict[str, str], new: dict[str, str]) -> list[dict]:
    """The reviewed rows that are valid, then a draft row for every § they leave unmapped, paired
    by heading similarity. Drafted notes start with `draft:` for the reviewer."""
    valid = [r for r in rows if (r["old_section"] in old or r["old_section"] == NEW)
             and (r["new_section"] in new or r["new_section"] == REPEALED)]
    mapped_old = {r["old_section"] for r in valid}
    mapped_new = {r["new_section"] for r in valid}
    def similarity(a: str, b: str) -> float:
        a, b = a.lower(), b.lower()
        contained = 0.9 if a in b or b in a else 0.0     # "Walls and ceilings" → "Interior walls and ceilings"
        return max(contained, difflib.SequenceMatcher(None, a, b).ratio())

    out = list(valid)
    for o, heading in old.items():
        if o in mapped_old:
            continue
        best = max(new, key=lambda n: similarity(heading, new[n]), default=None)
        score = similarity(heading, new[best]) if best else 0.0
        if best and score >= DRAFT_MATCH:
            out.append({"old_section": o, "new_section": best,
                        "note": f"draft: {heading} → {new[best]} ({score:.2f})"})
            mapped_new.add(best)
        else:
            out.append({"old_section": o, "new_section": REPEALED, "note": f"draft: {heading}, no match"})
    out += [{"old_section": NEW, "new_section": n, "note": f"draft: {heading}, no match"}
            for n, heading in new.items() if n not in mapped_new]
    return out


def link_pending(doc: dict, chunks: list[dict], rows: list[dict]) -> list[dict]:
    """A pending replacement's `amendments` rows (each chunk of a new § → the old §§ it replaces).
    Notes the pairing on both sides' breadcrumbs. Mutates chunks."""
    old_of: dict[str, list[str]] = {}
    new_of: dict[str, list[str]] = {}
    for r in rows:
        if r["old_section"] != NEW and r["new_section"] != REPEALED:
            old_of.setdefault(r["new_section"], []).append(r["old_section"])
            new_of.setdefault(r["old_section"], []).append(r["new_section"])
    effective = doc["in_force"] or doc["enacted"]
    amendments = []
    for c in chunks:
        if c["document_id"] == doc["id"] and c["section"] in old_of:
            olds = old_of[c["section"]]
            head, _, dated = c["breadcrumb"].rpartition("[")
            c["breadcrumb"] = f"{head}[{dated[:-1]} · replaces " + ", ".join(f"§ {s}" for s in olds) + "]"
            amendments += [{"amending_chunk_id": c["id"], "target_section": s} for s in olds]
        elif c["document_id"] == f"tmc:{doc['chapter']}":
            # the model sees the sublabel, not the breadcrumb: a § repealed outright has no
            # companion, so this is all that tells it the § ends on that date
            to = new_of.get(c["section"], [])
            change = ("replaced by " + ", ".join(f"§ {s}" for s in to) + " of") if to else "repealed by"
            c["breadcrumb"] = c["breadcrumb"][:-1] + f" · {change} By-law {doc['number']} from {effective}]"
            c["sublabel"] += f" · {'replaced' if to else 'repealed'} {effective} by By-law {doc['number']}"
    return amendments


# ── the hand-review file ─────────────────────────────────────────────────────────────────

def map_path(number: str) -> Path:
    return config.REVIEW / f"section_map_{number}.csv"


def read_map(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return [{k: (r.get(k) or "").strip() for k in MAP_COLUMNS} for r in csv.DictReader(f)]


def write_map(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=MAP_COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def link_replacements(documents: list[dict], chunks: list[dict]) -> list[dict]:
    """Every pending replacement's § map, checked; → its `amendments` rows. A missing or incomplete
    map writes a draft next to it and stops the stage."""
    amendments, failures = [], []
    for doc in (d for d in documents if d["kind"] == "replacement_bylaw" and not d["in_force_now"]):
        old = section_headings(chunks, f"tmc:{doc['chapter']}")
        new = section_headings(chunks, doc["id"])
        path = map_path(doc["number"])
        rows = read_map(path)
        if problems := map_problems(rows, list(old), list(new)):
            draft = path.with_suffix(".draft.csv")
            write_map(draft, draft_map(rows, old, new))
            failures.append(f"{path.relative_to(config.ROOT).as_posix()}: "
                            + ("missing" if not path.exists() else f"{len(problems)} problems")
                            + "".join(f"\n    {p}" for p in problems[:15])
                            + (f"\n    … {len(problems) - 15} more" if len(problems) > 15 else "")
                            + f"\n  draft written to {draft.relative_to(config.ROOT).as_posix()}: review it, save it as "
                            f"{path.name}, re-run chunk")
            continue
        amendments += link_pending(doc, chunks, rows)
    if failures:
        raise SystemExit("§ map for a replacement not yet in force:\n  " + "\n  ".join(failures))
    return amendments
