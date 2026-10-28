"""Code chapter chunker on short synthetic extracted streams (no City text).

The split tests lower the ceiling so a few lines stand in for a § over ~800 tokens.
"""
import json

import pytest

from ingest import chunk as chunker
from ingest.chunk import chunk_code_chapter
from ingest.store import ManifestRow

ROW = ManifestRow(sha256="abc", kind="code_chapter", ref="ch-999", parent_ref="",
                  source_url="https://example.test/999.pdf", obtained_by="script",
                  obtained_at="2026-10-27T18:00:00Z", last_modified="", etag="", bytes=1,
                  content_type="application/pdf", encoding="")


def line(page, top, text, x0=72.0, bold=False, size=12.0):
    return {"kind": "line", "page": page, "top": top, "bottom": top + size, "x0": x0,
            "size": size, "bold": bold, "text": text}


def table(page, top, rows):
    return {"kind": "table", "page": page, "top": top, "bottom": top + 20 * len(rows), "x0": 72.0, "rows": rows}


def page(n, footer_top=737.8, footer_date="March 5, 2025"):
    return [{"kind": "page", "page": n, "width": 612.0, "height": 792.0},
            line(n, 38.8, "TORONTO MUNICIPAL CODE", x0=225),
            line(n, 52.6, "CHAPTER 999, WIDGETS AND GADGETS", x0=240),
            line(n, footer_top, f"999-{n} {footer_date}", x0=274)]


def paras(page_no, top, items):
    """(text, x0) items as separate paragraphs, 26 pt apart."""
    return [line(page_no, top + 26 * i, text, x0=x0) for i, (text, x0) in enumerate(items)]


def chapter(*pages_and_lines):
    return [r for part in pages_and_lines for r in part]


def ids(chunks):
    return [c["id"] for c in chunks]


@pytest.fixture
def ceiling(monkeypatch):
    def set_to(n):
        monkeypatch.setattr(chunker, "CEILING", n)
    return set_to


# ── one chunk per §, drops ───────────────────────────────────────────────────────────────

RECORDS = [
    *page(1),
    line(1, 100, "ARTICLE 1", x0=274, bold=True),
    line(1, 114, "General", x0=277, bold=True),
    line(1, 140, "§ 999-1.1. Definitions.", bold=True),          # table of contents
    line(1, 166, "§ 999-1.2. Hours.", bold=True),
    *page(2),
    line(2, 80, "ARTICLE 1", x0=276),
    line(2, 94, "General", x0=277, bold=True),
    line(2, 108, "[Adopted 2000-01-01 by By-law 1-2000]", x0=186, bold=True),
    line(2, 120, "§ 999-1.1. Definitions.", bold=True),
    line(2, 146, "WIDGET - A device that is self-"),
    line(2, 160, "propelled."),
    line(2, 186, "GADGET - Any other device. [Added 2024-01-02 by By-"),
    line(2, 200, "law 12-2024]", bold=True),
    line(2, 700, "1 Editor's Note: footnote text.", size=9.96),
    *page(3, footer_top=726.9),
    line(3, 80, "§ 999-1.2. Hours.", bold=True),
    line(3, 106, "[Amended 2024-05-06 by By-law 34-2024]", bold=True),
    line(3, 132, "A. No widget may run from 7 p.m. until 8 a.m. as set out in § 999-1.1."),
    table(3, 160, [["Day", "Hours"], ["Sunday", "9 a.m."]]),
    line(3, 715, "B. Holidays are as for Sundays."),                 # body text low on the page
    line(3, 740, "§ 999-1.3. Reserved. [Repealed 2020-01-01 by By-", bold=True),
    *page(4),
    line(4, 80, "law 9-2020]"),
]


def test_one_chunk_per_section_with_label_sublabel_href():
    doc, chunks = chunk_code_chapter(RECORDS, ROW)

    assert doc["id"] == "tmc:999"
    assert doc["title"] == "Ch 999 Widgets and Gadgets"
    assert doc["consolidated_as_of"] == "2025-03-05"
    assert ids(chunks) == ["tmc:999-1.1", "tmc:999-1.2"]

    defs, hours = chunks
    assert defs["label"] == "Ch 999 § 999-1.1"
    assert defs["sublabel"] == "consolidated 2025-03-05"
    assert defs["href"] == "https://example.test/999.pdf#page=2"
    assert defs["breadcrumb"] == ("[Toronto Municipal Code › Ch 999 Widgets and Gadgets › Article 1 General"
                                  " › § 999-1.1 Definitions]\n[consolidated as of 2025-03-05]")
    assert defs["body"] == ("WIDGET - A device that is self-propelled.\n\n"
                            "GADGET - Any other device. [Added 2024-01-02 by By-law 12-2024]")
    assert defs["amended_by"] == ["12-2024"]
    assert defs["subsection_range"] is None

    assert hours["page_start"] == 3
    assert hours["amended_by"] == ["34-2024"]
    assert "| Day | Hours |\n| --- | --- |\n| Sunday | 9 a.m. |" in hours["body"]


def test_header_footer_toc_footnotes_and_article_notes_are_dropped():
    _, chunks = chunk_code_chapter(RECORDS, ROW)
    text = "\n".join(c["breadcrumb"] + c["body"] for c in chunks)
    for dropped in ("TORONTO MUNICIPAL CODE", "CHAPTER 999", "999-2 March", "999-3 March",
                    "footnote", "Adopted 2000-01-01"):
        assert dropped not in text
    # the TOC's § lines did not become chunks of their own, and body text at 715 pt stayed
    assert chunks[1]["body"].endswith("B. Holidays are as for Sundays.")


def test_a_section_holding_only_a_note_is_dropped():
    _, chunks = chunk_code_chapter(RECORDS, ROW)
    assert "tmc:999-1.3" not in ids(chunks)


def test_reserved_stub_yields_nothing():
    stub = [{"kind": "page", "page": 1, "width": 612.0, "height": 792.0},
            line(1, 51, "Chapter 998", x0=274, bold=True),
            line(1, 94.8, "(RESERVED)", x0=269, bold=True),
            line(1, 138.6, "[Former Chapter 998, Widgets, was repealed by By-law 1-2018.]", bold=True)]
    assert chunk_code_chapter(stub, ROW) is None


def test_inline_section_reference_never_splits():
    _, chunks = chunk_code_chapter(RECORDS, ROW)
    assert "as set out in § 999-1.1." in chunks[1]["body"]


def test_iso_footer_date_and_header_without_chapter_number():
    records = [{"kind": "page", "page": 1, "width": 612.0, "height": 792.0},
               line(1, 38.8, "TORONTO MUNICIPAL CODE", x0=225),
               line(1, 52.6, "TAXATION, WIDGET TAX", x0=214),
               line(1, 737.5, "999-1 2011-06-15", x0=274),
               line(1, 100, "§ 999-1. Tax.", bold=True),
               line(1, 120, "§ 999-1. Tax.", bold=True),
               line(1, 146, "A tax is imposed on widgets.")]
    doc, chunks = chunk_code_chapter(records, ROW)
    assert doc["title"] == "Ch 999 Taxation, Widget Tax"
    assert doc["consolidated_as_of"] == "2011-06-15"
    assert ids(chunks) == ["tmc:999-1"]


# ── a § over the ceiling ─────────────────────────────────────────────────────────────────

def section(heading, body):
    return chapter(page(1), [line(1, 100, heading, bold=True)], page(2),
                   [line(2, 80, heading, bold=True)], body)


PERMITS = section("§ 999-2.1. Permits.", paras(2, 106, [
    ("[Amended 2025-01-02 by By-law 5-2025]", 72),
    ("A. No person shall operate a widget without a permit issued under this article.", 72),
    ("B. An application for a permit shall be made to the Executive Director.", 72),
    ("C. The Executive Director may refuse a permit where:", 72),
    ("(1) the applicant has failed to pay any fee owing to the City under this chapter;", 108),
    ("(2) the widget does not meet the safety requirements set out in § 999-3.1; or", 108),
    ("(3) the applicant was convicted of an offence under this chapter in the past year.", 108),
    ("D. A permit expires one year after it is issued.", 72),
]))


def test_section_over_ceiling_packs_top_level_subsections_then_splits_at_numbered_items(ceiling):
    ceiling(50)
    _, chunks = chunk_code_chapter(PERMITS, ROW)

    assert ids(chunks) == ["tmc:999-2.1:A-B", "tmc:999-2.1:C(1)", "tmc:999-2.1:C(2)-C(3)", "tmc:999-2.1:D"]
    assert [c["label"] for c in chunks] == ["Ch 999 § 999-2.1 A–B", "Ch 999 § 999-2.1 C(1)",
                                            "Ch 999 § 999-2.1 C(2)–C(3)", "Ch 999 § 999-2.1 D"]
    assert [c["subsection_range"] for c in chunks] == ["A–B", "C(1)", "C(2)–C(3)", "D"]
    assert all(c["section"] == "999-2.1" for c in chunks)
    assert all(c["tokens"] <= 50 for c in chunks)
    assert chunks[0]["breadcrumb"] == ("[Toronto Municipal Code › Ch 999 Widgets and Gadgets"
                                       " › § 999-2.1 Permits (A–B)]\n[consolidated as of 2025-03-05]")
    assert chunks[0]["href"] == "https://example.test/999.pdf#page=2"
    # the § note travels with the first piece; C's lead-in stays with its first item
    assert chunks[0]["body"].startswith("[Amended 2025-01-02 by By-law 5-2025]\n\nA. No person")
    assert chunks[0]["amended_by"] == ["5-2025"] and chunks[1]["amended_by"] == []
    assert chunks[1]["body"].startswith("C. The Executive Director may refuse a permit where:\n\n(1) the applicant")


def test_split_is_lossless():
    _, whole = chunk_code_chapter(PERMITS, ROW)
    chunker.CEILING, saved = 40, chunker.CEILING
    try:
        _, parts = chunk_code_chapter(PERMITS, ROW)
    finally:
        chunker.CEILING = saved
    assert "\n\n".join(c["body"] for c in parts) == whole[0]["body"]


def test_definitions_split_into_runs_of_whole_terms(ceiling):
    ceiling(37)
    records = section("§ 999-1.1. Definitions.", paras(2, 106, [
        ("As used in this chapter, the following terms shall have the meanings indicated:", 72),
        ("APPLIANCE - A widget used in a dwelling unit for domestic purposes.", 72),
        ("DEVICE - Any widget or gadget.", 72),
        ("POINT OF RECEPTION - Any location where sound is received, including:", 72),
        ("(1) an outdoor area; or", 108),
        ("(2) an indoor area.", 108),
        ("WIDGET - A self-propelled device.", 72),
    ]))
    _, chunks = chunk_code_chapter(records, ROW)

    assert ids(chunks) == ["tmc:999-1.1:appliance", "tmc:999-1.1:device", "tmc:999-1.1:widget"]
    assert [c["subsection_range"] for c in chunks] == ["APPLIANCE", "DEVICE – POINT OF RECEPTION", "WIDGET"]
    assert chunks[0]["body"].startswith("As used in this chapter")
    assert chunks[1]["body"].endswith("(1) an outdoor area; or\n\n(2) an indoor area.")
    assert chunks[1]["label"] == "Ch 999 § 999-1.1 DEVICE – POINT OF RECEPTION"


def test_table_split_across_chunks_repeats_its_header_row(ceiling):
    ceiling(60)
    rows = [["Parameter", "Limit"]] + [[f"Metal {i}", f"0.{i}"] for i in range(1, 13)]
    records = section("§ 999-3.1. Discharge limits.", [
        line(2, 106, "A. No person shall discharge water exceeding these limits:"),
        table(2, 132, rows),
    ])
    _, chunks = chunk_code_chapter(records, ROW)

    assert len(chunks) > 1
    tables = [c["body"][c["body"].index("| Parameter"):] for c in chunks if "| Parameter" in c["body"]]
    assert len(tables) == len(chunks)
    assert all(t.startswith("| Parameter | Limit |\n| --- | --- |\n") for t in tables)
    body_rows = [r for t in tables for r in t.splitlines()[2:]]
    assert body_rows == [f"| Metal {i} | 0.{i} |" for i in range(1, 13)]      # never duplicated
    assert chunks[0]["body"].startswith("A. No person shall discharge water exceeding these limits:\n\n| Parameter")
    assert ids(chunks) == [f"tmc:999-3.1:p{i}" for i in range(1, len(chunks) + 1)]
    assert [c["subsection_range"] for c in chunks] == [f"part {i}" for i in range(1, len(chunks) + 1)]


def test_a_table_title_moves_with_its_table(ceiling):
    rows = [["Parameter", "Limit"]] + [[f"Metal {i}", f"0.{i}"] for i in range(1, 6)]
    title = "Table 2 - Storm Limits [Amended 2016-02-04 by By-law 100-2016]"
    ceiling(chunker.tokens(f"{title}\n\n{chunker.table_markdown(rows)}"))   # title + table fill a chunk
    records = section("§ 999-3.3. Storm sewers.", [
        line(2, 106, "J. No person shall exceed the limits in Table 2."),
        line(2, 132, title),
        table(2, 158, rows),
    ])
    _, chunks = chunk_code_chapter(records, ROW)
    assert [c["body"].split("\n\n")[0] for c in chunks] == ["J. No person shall exceed the limits in Table 2.", title]


def test_two_column_pair_table_unfolds_to_one_row_per_parameter():
    records = section("§ 999-3.2. Storm limits.", [
        table(2, 106, [["Parameter", "Limit", "Parameter", "Limit"],
                       ["Arsenic", "0.02", "Lead", "0.12"],
                       ["Cadmium", "0.008", "", ""]]),
    ])
    _, [c] = chunk_code_chapter(records, ROW)
    assert c["body"] == ("| Parameter | Limit |\n| --- | --- |\n| Arsenic | 0.02 |\n"
                         "| Cadmium | 0.008 |\n| Lead | 0.12 |")


def test_schedule_after_the_last_section_is_its_own_chunk():
    records = section("§ 999-4. Penalties.", paras(2, 106, [
        ("Every person who contravenes this chapter is guilty of an offence.", 72),
        ("Schedule A Prohibited Widgets", 250),
        ("Steam widgets, clockwork widgets.", 72),
    ]))
    _, chunks = chunk_code_chapter(records, ROW)

    assert ids(chunks) == ["tmc:999-4", "tmc:999:schedule-a"]
    assert chunks[0]["body"] == "Every person who contravenes this chapter is guilty of an offence."
    sched = chunks[1]
    assert sched["label"] == "Ch 999 Schedule A"
    assert sched["section"] is None
    assert sched["breadcrumb"].startswith("[Toronto Municipal Code › Ch 999 Widgets and Gadgets"
                                          " › Schedule A Prohibited Widgets]")


def test_deterministic(ceiling):
    ceiling(40)
    for records in (RECORDS, PERMITS):
        dump = lambda: json.dumps(chunk_code_chapter(records, ROW), sort_keys=True, ensure_ascii=False)
        assert dump() == dump()
