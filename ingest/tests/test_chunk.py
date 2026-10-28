"""Code chapter chunker on a short synthetic extracted stream (no City text)."""
import json

from ingest.chunk import chunk_code_chapter
from ingest.store import ManifestRow

ROW = ManifestRow(sha256="abc", kind="code_chapter", ref="ch-999", parent_ref="",
                  source_url="https://example.test/999.pdf", obtained_by="script",
                  obtained_at="2026-10-27T18:00:00Z", last_modified="", etag="", bytes=1,
                  content_type="application/pdf", encoding="")


def line(page, top, text, x0=72.0, bold=False, size=12.0):
    return {"kind": "line", "page": page, "top": top, "bottom": top + size, "x0": x0,
            "size": size, "bold": bold, "text": text}


def page(n):
    return [{"kind": "page", "page": n, "width": 612.0, "height": 792.0},
            line(n, 38.8, "TORONTO MUNICIPAL CODE", x0=225),
            line(n, 52.6, "CHAPTER 999, WIDGETS AND GADGETS", x0=240),
            line(n, 737.8, f"999-{n} March 5, 2025", x0=274)]


RECORDS = [
    *page(1),
    line(1, 100, "ARTICLE 1", x0=274, bold=True),
    line(1, 114, "General", x0=277, bold=True),
    line(1, 140, "§ 999-1.1. Definitions.", bold=True),          # table of contents
    line(1, 166, "§ 999-1.2. Hours.", bold=True),
    *page(2),
    line(2, 80, "ARTICLE 1", x0=276),
    line(2, 94, "General", x0=277, bold=True),
    line(2, 120, "§ 999-1.1. Definitions.", bold=True),
    line(2, 146, "WIDGET - A device that is self-"),
    line(2, 160, "propelled."),
    line(2, 186, "GADGET - Any other device. [Added 2024-01-02 by By-"),
    line(2, 200, "law 12-2024]", bold=True),
    line(2, 700, "1 Editor's Note: footnote text.", size=9.96),
    *page(3),
    line(3, 80, "§ 999-1.2. Hours.", bold=True),
    line(3, 106, "[Amended 2024-05-06 by By-law 34-2024]", bold=True),
    line(3, 132, "A. No widget may run from 7 p.m. until 8 a.m. as set out in § 999-1.1."),
    {"kind": "table", "page": 3, "top": 160, "bottom": 200, "x0": 72.0,
     "rows": [["Day", "Hours"], ["Sunday", "9 a.m."]]},
]


def test_one_chunk_per_section_with_label_sublabel_href():
    doc, chunks = chunk_code_chapter(RECORDS, ROW)

    assert doc["id"] == "tmc:999"
    assert doc["title"] == "Ch 999 Widgets and Gadgets"
    assert doc["consolidated_as_of"] == "2025-03-05"
    assert [c["id"] for c in chunks] == ["tmc:999-1.1", "tmc:999-1.2"]

    defs, hours = chunks
    assert defs["label"] == "Ch 999 § 999-1.1"
    assert defs["sublabel"] == "consolidated 2025-03-05"
    assert defs["href"] == "https://example.test/999.pdf#page=2"
    assert defs["breadcrumb"] == ("[Toronto Municipal Code › Ch 999 Widgets and Gadgets › Article 1 General"
                                  " › § 999-1.1 Definitions]\n[consolidated as of 2025-03-05]")
    assert defs["body"] == ("WIDGET - A device that is self-propelled.\n\n"
                            "GADGET - Any other device. [Added 2024-01-02 by By-law 12-2024]")
    assert defs["amended_by"] == ["12-2024"]
    assert "footnote" not in defs["body"]

    assert hours["page_start"] == 3
    assert hours["amended_by"] == ["34-2024"]
    assert hours["body"].endswith("| Day | Hours |\n| --- | --- |\n| Sunday | 9 a.m. |")


def test_inline_section_reference_never_splits():
    _, chunks = chunk_code_chapter(RECORDS, ROW)
    assert "as set out in § 999-1.1." in chunks[1]["body"]


def test_deterministic():
    dump = lambda: json.dumps(chunk_code_chapter(RECORDS, ROW), sort_keys=True, ensure_ascii=False)
    assert dump() == dump()
