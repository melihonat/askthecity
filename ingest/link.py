"""The amendment linker: Code chunks + amending by-law chunks → `amendments` rows and `amended_since`.

CHUNKING.md, "Rules: amending by-laws". A by-law amends a chapter *since* its consolidation when
its number is absent from the chapter's own bracketed notes and it took effect after the
chapter's consolidated-as-of date (a consolidation includes what took effect that day). By-laws
that amend no chapter that way, or whose every instruction touches a Schedule or Appendix, are
dropped (to build/skipped.jsonl). A replacement chapter in force stands in for its chapter: its
enactment notes and in-force date play the consolidation's part (ingest/replace.py). Pure: no I/O.
"""
from __future__ import annotations

import re
from collections import defaultdict

TITLE_CHAPTER = re.compile(r"\bChapter\s+(\d+[A-Z]?)\b")
REF = re.compile(r"(\d+[A-Z]?-\d+(?:\.\d+)*)([A-Z]?)(.*)")
MAX_SUBLABEL_TARGETS = 3


def resolve(ref: str, known: set[str]) -> tuple[str, str] | None:
    """'629-38F' → ('629-38', 'F') when § 629-38F doesn't exist but § 629-38 does; '950-1316B' stays
    whole when it is a § of its own. None when the snapshot has no such §."""
    m = REF.fullmatch(ref)
    if not m:
        return None
    base, letter, rest = m[1], m[2], m[3].lstrip(".")
    if letter and base + letter in known:
        return base + letter, rest
    if base in known:
        return base, letter + rest
    return None


def bylaw_key(number: str) -> tuple[int, int]:
    n, year = number.split("-")
    return int(year), int(n)


def link(documents: list[dict], chunks: list[dict]) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """→ (documents, chunks, amendments, skipped). By-law chunks get their final `amends`,
    breadcrumb and sublabel; Code chunks of an amended § get `amended_since`."""
    chapters = {d["id"].removeprefix("tmc:"): d for d in documents if d["kind"] == "chapter"}
    chapters |= {d["chapter"]: d for d in documents if d["kind"] == "replacement_bylaw" and d["in_force_now"]}
    as_of = {ch: d["consolidated_as_of"] or d["in_force"] or d["enacted"] for ch, d in chapters.items()}
    title = {ch: d.get("chapter_title") or d["title"] for ch, d in chapters.items()}
    sections: dict[str, set[str]] = defaultdict(set)
    for c in chunks:
        if c["id"].startswith("tmc:") and c["section"]:
            sections[c["chapter"]].add(c["section"])
    by_doc: dict[str, list[dict]] = defaultdict(list)
    for c in chunks:
        if c["kind"] == "amending_bylaw":
            by_doc[c["document_id"]].append(c)

    out_docs = [d for d in documents if d["kind"] != "amending_bylaw"]
    out_chunks = [c for c in chunks if c["kind"] != "amending_bylaw"]
    amendments: list[dict] = []
    skipped: list[dict] = []
    since: dict[str, set[str]] = defaultdict(set)

    for doc in (d for d in documents if d["kind"] == "amending_bylaw"):
        number, ref = doc["number"], f"bylaw-{doc['number']}"
        took_effect = max(doc["enacted"], doc["in_force"] or doc["enacted"])

        def live(ch: str) -> bool:
            chapter = chapters.get(ch)
            return bool(chapter) and number not in chapter["noted_bylaws"] and (
                not as_of[ch] or took_effect > as_of[ch])

        named = [ch for ch in dict.fromkeys(TITLE_CHAPTER.findall(doc["short_title"])) if ch in chapters]
        if not any(live(ch) for ch in named):
            reason = "names no snapshot chapter" if not named else \
                "already folded into " + ", ".join(f"Ch {ch}" for ch in named)
            skipped.append({"ref": ref, "reason": reason})
            continue
        own = by_doc[doc["id"]]
        if own and all(c["schedule_only"] for c in own):
            skipped.append({"ref": ref, "reason": "amends schedules only"})
            continue

        kept = []
        for c in own:
            if c["schedule_only"]:
                continue
            mentioned = {ch for ch in c["chapters"] if ch in chapters}
            allowed = set(named) | mentioned
            targets = []
            for r in c["amends"]:
                ch = r.split("-")[0]
                if ch in allowed:
                    mentioned.add(ch)
                    if live(ch) and (hit := resolve(r, sections[ch])) and hit not in targets:
                        targets.append(hit)
            if mentioned and not any(live(ch) for ch in mentioned):
                continue    # this clause only touches chapters that already carry the by-law
            kept.append((c, targets, sorted({ch for ch in mentioned if live(ch)} or
                                            {ch for ch in named if live(ch)}, key=_chapter_key)))
        if not kept:
            skipped.append({"ref": ref, "reason": "no clause amends a chapter since its consolidation"})
            continue

        out_docs.append(doc)
        if doc["in_force"]:
            dates = in_force = f"enacted {doc['enacted']} · in force {doc['in_force']}"
        else:
            dates, in_force = f"enacted {doc['enacted']} · in force on enactment", f"in force {doc['enacted']}"
        for c, targets, chs in kept:
            where = ", ".join(map(_section, targets))
            chapter_names = ", ".join(title[ch] for ch in chs)
            c["amends"] = [{"chapter": s.split("-")[0], "section": s, "sub": sub} for s, sub in targets]
            c["breadcrumb"] = (f"[By-law {number} › {doc['short_title']}]\n"
                               f"[amends {chapter_names}{' ' + where if where else ''} · {dates}]")
            shown = [_section(t) for t in targets[:MAX_SUBLABEL_TARGETS]]
            more = len(targets) - len(shown)
            amends = ", ".join(shown) + (f" +{more} more" if more > 0 else "") if shown else \
                ", ".join(f"Ch {ch}" for ch in chs)
            c["sublabel"] = f"amends {amends} · {in_force}"
            out_chunks.append(c)
            for s in dict.fromkeys(s for s, _ in targets):
                amendments.append({"amending_chunk_id": c["id"], "target_section": s})
                since[s].add(number)

    for c in out_chunks:
        if c["id"].startswith("tmc:") and c["section"] in since:
            c["amended_since"] = sorted(since[c["section"]], key=bylaw_key)
            dated, _, _ = c["breadcrumb"].rpartition("]")
            c["breadcrumb"] = dated + " · amended since by " + \
                ", ".join(f"By-law {n}" for n in c["amended_since"]) + "]"
    return out_docs, out_chunks, amendments, skipped


def _section(target: tuple[str, str]) -> str:
    """('681-4', 'J') → '§ 681-4 J'; ('778-3.3', '(A)') → '§ 778-3.3(A)'."""
    section, sub = target
    return f"§ {section}" + ("" if not sub else sub if sub.startswith("(") else f" {sub}")


def _chapter_key(ch: str) -> tuple[int, str]:
    m = re.match(r"\d+", ch)
    return int(m[0]), ch
