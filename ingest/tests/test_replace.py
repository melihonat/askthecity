"""Replacement by-laws on short synthetic extracted streams (no City text): which ids a replacement's
§§ take, which chapter is the law, and the old → new § map gate."""
import pytest

from ingest import config
from ingest.link import link
from ingest.replace import (chunk_replacement, draft_map, link_replacements, map_path, map_problems, read_map,
                            supersede, write_map)
from ingest.store import ManifestRow

ROW = ManifestRow(sha256="def", kind="replacement_bylaw", ref="bylaw-77-2025", parent_ref="",
                  source_url="https://example.test/law0077.pdf", obtained_by="script",
                  obtained_at="2026-10-29T18:00:00Z", last_modified="", etag="", bytes=1,
                  content_type="application/pdf", encoding="")


def line(page, top, text, x0=72.0, bold=False, size=12.0):
    return {"kind": "line", "page": page, "top": top, "bottom": top + size, "x0": x0,
            "size": size, "bold": bold, "text": text}


def bylaw_records(in_force="June 1, 2026"):
    return [
        {"kind": "page", "page": 1, "width": 612.0, "height": 792.0},
        line(1, 38, "Authority: Committee Item XX1.1"),
        line(1, 180, "CITY OF TORONTO", x0=249, bold=True),
        line(1, 208, "BY-LAW 77-2025", x0=253, bold=True),
        line(1, 236, "To repeal City of Toronto Municipal Code Chapter 999, Widgets and replace with new", bold=True),
        line(1, 250, "Chapter 999, Widget Standards as set out in Schedule A to this by-law.", bold=True),
        line(1, 360, "The Council of the City of Toronto enacts:"),
        line(1, 388, "1. Chapter 999, Widgets is repealed and replaced with the new chapter in Schedule A.", bold=True),
        line(1, 442, f"2. This by-law shall come into force on {in_force}.", bold=True),
        line(1, 470, "Enacted and passed on December 17, 2025."),
        line(1, 524, "Speaker City Clerk"),
        {"kind": "page", "page": 2, "width": 612.0, "height": 792.0},
        line(2, 38, "2", x0=303),
        line(2, 52, "City of Toronto By-law 77-2025", x0=221),
        line(2, 80, "SCHEDULE A", x0=267, bold=True),
        line(2, 108, "Chapter 999", x0=276, bold=True),
        line(2, 136, "ARTICLE 1", x0=278),
        line(2, 150, "General", x0=258, bold=True),
        line(2, 178, "§ 999-1.1 Hours.", x0=71.4, bold=True),
        line(2, 204, "No widget may run after 9 p.m."),
        line(2, 232, "§ 999- 1.2. Widgets in parks and other", x0=71.4, bold=True),   # spaced number, wrapped
        line(2, 246, "public places.", x0=71.4, bold=True),
        line(2, 272, "No widget may run in a park."),
        line(2, 300, "§ 999-1.3. Permits.", x0=71.4, bold=True),
        line(2, 326, "A permit is needed for a loud widget."),
    ]


def old_chapter(consolidated="2025-04-30", noted=()):
    doc = {"id": "tmc:999", "kind": "chapter", "title": "Ch 999 Widgets", "consolidated_as_of": consolidated,
           "enacted": None, "in_force": None, "chapter": "999", "noted_bylaws": list(noted)}
    chunks = [{"id": f"tmc:{s}", "document_id": "tmc:999", "kind": "chapter", "chapter": "999", "section": s,
               "heading": h, "amended_since": [], "sublabel": f"consolidated {consolidated}",
               "breadcrumb": f"[Toronto Municipal Code › Ch 999 Widgets › § {s} {h}]\n[consolidated as of {consolidated}]"}
              for s, h in [("999-1", "Hours"), ("999-2", "Parks"), ("999-3", "Signs")]]
    return doc, chunks


REVIEWED = [
    {"old_section": "999-1", "new_section": "999-1.1", "note": ""},
    {"old_section": "999-2", "new_section": "999-1.2", "note": ""},
    {"old_section": "999-3", "new_section": "repealed", "note": ""},
    {"old_section": "new", "new_section": "999-1.3", "note": ""},
]


@pytest.fixture
def review(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(config, "REVIEW", tmp_path / "review")
    return tmp_path / "review"


# ── chunking: ids by in-force date ───────────────────────────────────────────────────────

def test_a_replacement_not_yet_in_force_gets_bylaw_ids_and_says_not_yet_law():
    doc, chunks = chunk_replacement(bylaw_records("May 1, 2027"), ROW, "2026-10-28")
    assert doc["id"] == "bl:77-2025" and doc["kind"] == "replacement_bylaw" and not doc["in_force_now"]
    assert (doc["chapter"], doc["enacted"], doc["in_force"]) == ("999", "2025-12-17", "2027-05-01")
    assert [c["id"] for c in chunks] == ["bl:77-2025:999-1.1", "bl:77-2025:999-1.2", "bl:77-2025:999-1.3"]
    c = chunks[1]
    assert (c["kind"], c["section"], c["label"]) == ("replacement_bylaw", "999-1.2", "Ch 999 § 999-1.2")
    assert c["heading"] == "Widgets in parks and other public places"
    assert c["body"] == "No widget may run in a park."
    assert c["sublabel"] == "By-law 77-2025 · in force 2027-05-01, not yet law"
    assert c["href"] == "https://example.test/law0077.pdf#page=2"
    assert c["breadcrumb"] == ("[By-law 77-2025 › new Ch 999 Widget Standards › Article 1 General › "
                               "§ 999-1.2 Widgets in parks and other public places]\n"
                               "[enacted 2025-12-17 · in force 2027-05-01, not yet law]")


def test_a_replacement_in_force_takes_the_chapters_tmc_ids():
    doc, chunks = chunk_replacement(bylaw_records("June 1, 2026"), ROW, "2026-10-28")
    assert doc["in_force_now"]
    assert [c["id"] for c in chunks] == ["tmc:999-1.1", "tmc:999-1.2", "tmc:999-1.3"]
    assert all(c["document_id"] == "bl:77-2025" for c in chunks)
    assert chunks[0]["sublabel"] == "By-law 77-2025 · in force 2026-06-01"
    assert chunks[0]["breadcrumb"].startswith("[Toronto Municipal Code › Ch 999 Widget Standards › ")


# ── which one is the law ─────────────────────────────────────────────────────────────────

def test_in_force_the_stale_consolidated_chapter_is_dropped():
    old, old_chunks = old_chapter()
    doc, chunks = chunk_replacement(bylaw_records("June 1, 2026"), ROW, "2026-10-28")
    docs, out, skipped = supersede([old, doc], [*old_chunks, *chunks])
    assert [d["id"] for d in docs] == ["bl:77-2025"]
    assert [c["id"] for c in out] == ["tmc:999-1.1", "tmc:999-1.2", "tmc:999-1.3"]
    assert skipped == [{"ref": "ch-999", "reason": "replaced by By-law 77-2025, in force 2026-06-01"}]


def test_in_force_but_already_consolidated_the_chapter_stays():
    old, old_chunks = old_chapter(consolidated="2026-06-01", noted=["77-2025"])
    doc, chunks = chunk_replacement(bylaw_records("June 1, 2026"), ROW, "2026-10-28")
    docs, out, skipped = supersede([old, doc], [*old_chunks, *chunks])
    assert [d["id"] for d in docs] == ["tmc:999"]
    assert all(c["document_id"] == "tmc:999" for c in out)
    assert skipped == [{"ref": "bylaw-77-2025", "reason": "already folded into Ch 999"}]


def test_not_yet_in_force_both_stay():
    old, old_chunks = old_chapter()
    doc, chunks = chunk_replacement(bylaw_records("May 1, 2027"), ROW, "2026-10-28")
    docs, out, skipped = supersede([old, doc], [*old_chunks, *chunks])
    assert [d["id"] for d in docs] == ["tmc:999", "bl:77-2025"] and len(out) == 6 and skipped == []


def test_an_amending_bylaw_links_to_an_in_force_replacement_as_its_chapter():
    doc, chunks = chunk_replacement(bylaw_records("June 1, 2026"), ROW, "2026-10-28")
    amending = {"id": "bl:5-2026", "kind": "amending_bylaw", "number": "5-2026", "enacted": "2026-07-01",
                "in_force": None, "short_title": "To amend Chapter 999"}
    clause = {"id": "bl:5-2026:cl1", "document_id": "bl:5-2026", "kind": "amending_bylaw", "amends": ["999-1.2"],
              "chapters": ["999"], "schedule_only": False, "body": "…", "breadcrumb": "", "sublabel": "",
              "amended_since": []}
    _, out, amendments, skipped = link([doc, amending], [*chunks, clause])
    assert amendments == [{"amending_chunk_id": "bl:5-2026:cl1", "target_section": "999-1.2"}]
    assert {c["id"]: c["amended_since"] for c in out}["tmc:999-1.2"] == ["5-2026"]
    assert "[amends Ch 999 Widget Standards § 999-1.2 · " in {c["id"]: c for c in out}["bl:5-2026:cl1"]["breadcrumb"]
    assert skipped == []


# ── the old → new § map ──────────────────────────────────────────────────────────────────

def test_map_problems_names_every_unmapped_or_unknown_section():
    old, new = ["999-1", "999-2", "999-3"], ["999-1.1", "999-1.2", "999-1.3"]
    assert map_problems(REVIEWED, old, new) == []
    assert map_problems(REVIEWED[:2] + [{"old_section": "999-9", "new_section": "999-1.3", "note": ""}], old, new) == [
        "line 4: old § '999-9' is not in the consolidated chapter",
        "old § 999-3 is not mapped (to a new § or 'repealed')",
    ]


def test_draft_keeps_reviewed_rows_and_pairs_the_rest_by_heading():
    old = {"999-1": "Hours", "999-2": "Widgets in parks", "999-3": "Signs"}
    new = {"999-1.1": "Hours", "999-1.2": "Widgets in parks and other public places", "999-1.3": "Permits"}
    draft = draft_map(REVIEWED[:1], old, new)
    assert [(r["old_section"], r["new_section"]) for r in draft] == [
        ("999-1", "999-1.1"), ("999-2", "999-1.2"), ("999-3", "repealed"), ("new", "999-1.3")]
    assert draft[0]["note"] == "" and all(r["note"].startswith("draft: ") for r in draft[1:])


def pending():
    old, old_chunks = old_chapter()
    doc, chunks = chunk_replacement(bylaw_records("May 1, 2027"), ROW, "2026-10-28")
    return [old, doc], [*old_chunks, *chunks]


def test_a_missing_map_stops_chunk_and_writes_a_draft(review):
    docs, chunks = pending()
    with pytest.raises(SystemExit, match=r"section_map_77-2025\.csv: missing"):
        link_replacements(docs, chunks)
    assert [(r["old_section"], r["new_section"]) for r in read_map(review / "section_map_77-2025.draft.csv")] == [
        ("999-1", "999-1.1"), ("999-2", "999-1.2"), ("999-3", "repealed"), ("new", "999-1.3")]


def test_an_incomplete_map_stops_chunk(review):
    docs, chunks = pending()
    write_map(map_path("77-2025"), REVIEWED[:3])
    with pytest.raises(SystemExit, match=r"new § 999-1\.3 is not mapped"):
        link_replacements(docs, chunks)
    assert (review / "section_map_77-2025.draft.csv").exists()


def test_a_complete_map_links_new_sections_to_the_old_ones_they_replace(review):
    docs, chunks = pending()
    write_map(map_path("77-2025"), REVIEWED)
    assert link_replacements(docs, chunks) == [
        {"amending_chunk_id": "bl:77-2025:999-1.1", "target_section": "999-1"},
        {"amending_chunk_id": "bl:77-2025:999-1.2", "target_section": "999-2"},
    ]
    by_id = {c["id"]: c for c in chunks}
    assert by_id["tmc:999-1"]["sublabel"] == "consolidated 2025-04-30 · replaced 2027-05-01 by By-law 77-2025"
    assert by_id["tmc:999-3"]["sublabel"] == "consolidated 2025-04-30 · repealed 2027-05-01 by By-law 77-2025"
    assert by_id["tmc:999-1"]["breadcrumb"].endswith(
        "[consolidated as of 2025-04-30 · replaced by § 999-1.1 of By-law 77-2025 from 2027-05-01]")
    assert by_id["bl:77-2025:999-1.1"]["breadcrumb"].endswith(
        "[enacted 2025-12-17 · in force 2027-05-01, not yet law · replaces § 999-1]")
    assert by_id["bl:77-2025:999-1.3"]["breadcrumb"].endswith("[enacted 2025-12-17 · in force 2027-05-01, not yet law]")
