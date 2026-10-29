"""Amending by-law chunker and `amends` parsing on short synthetic extracted streams (no City text)."""
import pytest

from ingest import bylaw, chunk as chunker
from ingest.bylaw import chunk_amending_bylaw, parse_amends
from ingest.store import ManifestRow

ROW = ManifestRow(sha256="abc", kind="amending_bylaw", ref="bylaw-470-2026", parent_ref="",
                  source_url="https://example.test/law0470.pdf", obtained_by="script",
                  obtained_at="2026-10-29T18:00:00Z", last_modified="", etag="", bytes=1,
                  content_type="application/pdf", encoding="")


def line(page, top, text, x0=72.0, bold=False):
    return {"kind": "line", "page": page, "top": top, "bottom": top + 12, "x0": x0,
            "size": 12.0, "bold": bold, "text": text}


def bylaw_records(*body, passed="Enacted and passed on May 21, 2026."):
    """A one-page by-law: authority, heading, title, enacting line, `body` lines, signature."""
    return [{"kind": "page", "page": 1, "width": 612.0, "height": 792.0},
            line(1, 38.8, "Authority: Infrastructure and Environment Committee Item IE29.6"),
            line(1, 150, "CITY OF TORONTO", x0=249, bold=True),
            line(1, 178, "BY-LAW 470-2026", x0=254, bold=True),
            line(1, 206, "To amend City of Toronto Municipal Code Chapter 999, Widgets.", bold=True),
            line(1, 234, "The Council of the City of Toronto enacts:"),
            *[line(1, 262 + 28 * i, text, x0=x0) for i, (text, x0) in enumerate(body)],
            line(1, 700, passed),
            line(1, 740, "(Seal of the City)")]


# ── amends parsing ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text, refs", [
    ("1. Subsection 681-4(J) of Chapter 681 is amended by deleting “0.05” and replacing it with “2.0”.",
     ["681-4(J)"]),
    ("1. Chapter 629 is amended by deleting subsection § 629-38F.", ["629-38F"]),
    ("A. Amending § 610-6.2.A. Composition by adding the words “, inclusive of a Chair”", ["610-6.2.A"]),
    ("a. Delete § 743-7C(3)(a) and replace it with a new § 743-7C(3)(a)", ["743-7C(3)(a)"]),
    ("1. By-law 823-2025 is amended by deleting section 103-4.6.", ["103-4.6"]),
])
def test_amends_names_the_sections_an_instruction_targets(text, refs):
    assert parse_amends(text)[0] == refs


def test_quoted_and_inserted_text_never_names_a_target():
    text = ("2. Subsection § 354-3.2B(7) of Chapter 354 is amended by replacing the words “an air-conditioned "
            "space” with “a cooled space, as defined in Chapter 497 and § 497-1.1”.\n\n"
            "“(7) the location of a cooled space, as defined in § 497-2.2;”\n\n"
            "In addition to the duties in § 610-6.6, the Vice-Chair may act as Chair.")
    refs, chapters, schedule_only = parse_amends(text)
    assert (refs, chapters, schedule_only) == (["354-3.2B(7)"], ["354"], False)


def test_schedule_only_when_every_targeted_instruction_names_a_schedule():
    sched = "1. Chapter 950 is amended as follows:\n\nA. By deleting from Schedule XIV in § 950-1313 the following:"
    assert parse_amends(sched) == ([], ["950"], True)
    mixed = sched + "\n\nB. By amending § 950-400D by adding the words “or a cargo bicycle”."
    assert parse_amends(mixed) == (["950-400D"], ["950"], False)
    assert parse_amends("1. Chapter 103 is amended by deleting “Board” wherever it occurs.")[2] is False


# ── chunking ─────────────────────────────────────────────────────────────────────────────

def test_one_chunk_per_operative_clause_and_the_in_force_date():
    recs = bylaw_records(
        ("1. Subsection 999-4(J) of Chapter 999 is amended by replacing “0.05” with “2.0”.", 72),
        ("2. Section 999-7 is amended by adding the words “or rockets”.", 72),
        ("3. This by-law comes into force on January 1, 2027.", 72),
    )
    doc, chunks = chunk_amending_bylaw(recs, ROW)
    assert {k: doc[k] for k in ("id", "kind", "title", "enacted", "in_force")} == {
        "id": "bl:470-2026", "kind": "amending_bylaw",
        "title": "By-law 470-2026: To amend City of Toronto Municipal Code Chapter 999, Widgets.",
        "enacted": "2026-05-21", "in_force": "2027-01-01"}
    assert [(c["id"], c["label"], c["amends"], c["section"]) for c in chunks] == [
        ("bl:470-2026:cl1", "By-law 470-2026 cl. 1", ["999-4(J)"], None),
        ("bl:470-2026:cl2", "By-law 470-2026 cl. 2", ["999-7"], None),
    ]
    assert "Authority" not in chunks[0]["body"] and "Seal" not in chunks[1]["body"]


def test_in_force_on_enactment_is_not_recorded_and_a_misprinted_date_still_parses():
    recs = bylaw_records(("1. Section 999-7 is amended by adding “or rockets”.", 72),
                         passed="Enacted and passed on November 9. 2023.")
    doc, _ = chunk_amending_bylaw(recs, ROW)
    assert (doc["enacted"], doc["in_force"]) == ("2023-11-09", None)


def test_a_clause_over_the_ceiling_splits_at_its_lettered_items(monkeypatch):
    for module in (chunker, bylaw):
        monkeypatch.setattr(module, "CEILING", 40)
    words = "the words " * 6
    recs = bylaw_records(
        ("1. Chapter 999 is amended as follows:", 72),
        (f"A. Amending § 999-1 by deleting {words}", 108),
        (f"B. Amending § 999-2 by deleting {words}", 108),
        ("“A. A quoted item that sits deeper and stays inside B.”", 144),
        (f"C. Amending § 999-3 by deleting {words}", 108),
    )
    _, chunks = chunk_amending_bylaw(recs, ROW)
    assert [(c["id"], c["amends"]) for c in chunks] == [
        ("bl:470-2026:cl1:A", ["999-1"]), ("bl:470-2026:cl1:B", ["999-2"]), ("bl:470-2026:cl1:C", ["999-3"])]
    assert chunks[0]["body"].startswith("1. Chapter 999 is amended as follows:")   # lead-in joins A
    assert chunks[1]["label"] == "By-law 470-2026 cl. 1 B"


def test_clauses_laid_out_as_a_table_read_as_text():
    recs = bylaw_records()
    recs.insert(-2, {"kind": "table", "page": 1, "top": 300, "bottom": 400, "x0": 72.0, "rows": [
        ["1. Chapter 999 is amended as follows:", ""], ["", ""],
        ["", "A. Amending § 999-3 by deleting “May”."]]})
    _, chunks = chunk_amending_bylaw(recs, ROW)
    assert [(c["id"], c["amends"]) for c in chunks] == [("bl:470-2026:cl1", ["999-3"])]
    assert "|" not in chunks[0]["body"]
