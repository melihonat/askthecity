"""The report label gate and the staff-report chunker on synthetic inputs (no City text)."""
import pytest

from ingest import chunk as chunker
from ingest import reports
from ingest.store import ManifestRow

BGRD = "https://www.toronto.ca/legdocs/mmis/2026/ie/bgrd/backgroundfile-{}.pdf"
COMM = "https://www.toronto.ca/legdocs/mmis/2026/ie/comm/communicationfile-{}.pdf"


# ── label gate ───────────────────────────────────────────────────────────────────────────

REVIEWED = {
    "(April 2, 2026) Report and Attachment 1 from the General Manager on Widgets": "in",
    "(April 2, 2026) Report from the General Manager on Widgets": "out",   # superseded by a revision
    "(April 9, 2026) Presentation from the General Manager on Widgets": "out",
}


@pytest.mark.parametrize("label, url, expected", [
    ("(April 22, 2026) Report from the General Manager, Toronto Water on Widgets", BGRD.format(1), "in"),
    ("Report from the General Manager on Widgets", BGRD.format(1), "in"),
    ("(April 23, 2026) Supplementary Report from the City Manager on Widgets", BGRD.format(2), "in"),
    ("Attachment 1 - Summary of Widget Amendments", BGRD.format(3), "out"),
    ("Attachments 1 to 3 from the General Manager on Widgets", BGRD.format(3), "out"),
    ("(May 1, 2026) Letter from Councillor A on Widgets", BGRD.format(4), "out"),
    ("(May 5, 2026) Report from the General Manager on Widgets", COMM.format(5), "out"),
    ("(May 5, 2026) E-mail from Pat Private", COMM.format(6), "out"),
    ("(April 2, 2026) Report and Attachment 1 from the General Manager on Widgets", BGRD.format(7), "in"),
    ("(April 2, 2026) Report from the General Manager on Widgets", BGRD.format(8), "out"),
    ("(April 9, 2026) Presentation from the General Manager on Widgets", BGRD.format(9), "out"),
    ("(April 9, 2026) Staff Presentation from the General Manager on Widgets", BGRD.format(10), "pending"),
    ("Supplementary report from the General Manager on Widgets", BGRD.format(11), "pending"),
    ("Notice of Public Meeting", BGRD.format(12), "pending"),
    ("", BGRD.format(13), "pending"),
], ids=["report", "report undated", "supplementary report", "attachment", "attachments", "councillor letter",
        "comm/ even if labelled a report", "communication", "reviewed in", "reviewed out overrides allowlist",
        "reviewed out", "unreviewed presentation", "unreviewed lowercase supplementary", "unreviewed notice",
        "no label"])
def test_gate(label, url, expected):
    assert reports.gate(label, url, REVIEWED) == expected


def item_page(*links):
    """Background Information block with (label, url) links, plus a Summary link and a Communication."""
    bg = "".join(f'<span class="rpt-text">{label}</span><br /><a class="rpt-text" href="{url}">{url}</a><br />'
                 for label, url in links)
    return (f'<h4>Summary</h4><div class="wep"><p>See <a href="{BGRD.format(999)}">the old report</a>.</p></div>'
            f'<h4>Background Information</h4><div>{bg}</div>'
            f'<h4>Communications</h4><div><span class="rpt-text">(May 5, 2026) Letter from Pat Private</span><br />'
            f'<a class="rpt-text" href="{COMM.format(1)}">{COMM.format(1)}</a></div>')


def test_report_links_reads_background_information_only():
    html = item_page(("(April 22, 2026)\n   Report from the GM  on Widgets", BGRD.format(1)),
                     ("Attachment 1 - Widgets", BGRD.format(2)))
    assert reports.report_links(html) == [("(April 22, 2026) Report from the GM on Widgets", BGRD.format(1)),
                                          ("Attachment 1 - Widgets", BGRD.format(2))]


def test_decide_keeps_reports_and_stops_on_unreviewed_labels():
    pages = [("2026.IE99.1", item_page(("Report from the GM on Widgets", BGRD.format(1)),
                                       ("Attachment 1 - Widgets", BGRD.format(2)),
                                       ("Staff Presentation on Widgets", BGRD.format(3)))),
             ("2026.IE99.2", item_page(("Report from the GM on Widgets", BGRD.format(1))))]
    keep, pending = reports.decide(pages, {})
    assert keep == {"backgroundfile-1": (BGRD.format(1), "2026.IE99.1", "Report from the GM on Widgets")}
    assert pending == [("Staff Presentation on Widgets", "2026.IE99.1", BGRD.format(3))]


def test_fetch_reports_writes_pending_labels_and_downloads_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(reports, "LABELS", tmp_path / "report_labels.csv")
    monkeypatch.setattr(reports, "PENDING", tmp_path / "report_labels.pending.csv")
    monkeypatch.setattr(reports.config, "ROOT", tmp_path)
    html = item_page(("Report from the GM on Widgets", BGRD.format(1)), ("Notice of Public Meeting", BGRD.format(2)))
    path = tmp_path / "2026.IE99.1.html"
    path.write_bytes(html.encode("cp1252"))
    row = ManifestRow(sha256="abc", kind="item_page", ref="2026.IE99.1", parent_ref="", source_url="",
                      obtained_by="agent_fetch", obtained_at="2026-10-31T17:00:00Z", last_modified="", etag="",
                      bytes=1, content_type="", encoding="windows-1252")
    monkeypatch.setattr(ManifestRow, "local_path", property(lambda self: path))
    monkeypatch.setattr(reports.store, "read_manifest", lambda: [row])
    monkeypatch.setattr(reports.requests, "get", lambda *a, **k: pytest.fail("downloaded before review"))
    with pytest.raises(SystemExit, match="1 unreviewed report labels"):
        reports.fetch_reports()
    assert reports.PENDING.read_text(encoding="utf-8") == (
        f"label,decision,note\nNotice of Public Meeting,,2026.IE99.1 · {BGRD.format(2)}\n")


def test_review_file_rejects_a_decision_other_than_in_or_out(tmp_path, monkeypatch):
    monkeypatch.setattr(reports, "LABELS", tmp_path / "report_labels.csv")
    reports.LABELS.write_text("label,decision,note\nNotice of Public Meeting,maybe,\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="Notice of Public Meeting"):
        reports.read_labels()


# ── chunker ──────────────────────────────────────────────────────────────────────────────

ROW = ManifestRow(sha256="abc", kind="staff_report", ref="backgroundfile-123", parent_ref="2026.IE99.1",
                  source_url=BGRD.format(123), obtained_by="script", obtained_at="2026-10-31T18:00:00Z",
                  last_modified="", etag="", bytes=1, content_type="application/pdf", encoding="")
ITEM = {"item_id": "2026.IE99.1", "title": "Item 2026.IE99.1 Widget Policy",
        "status_stamp": "Adopted with amendments by City Council 2026-05-21 · By-law 470-2026",
        "decision_date": "2026-05-21", "bylaws": ["470-2026"]}


def line(page, top, text, bold=False, size=12.0, x0=72.0):
    return {"kind": "line", "page": page, "top": top, "bottom": top + size, "x0": x0,
            "size": size, "bold": bold, "text": text}


def major(page, top, text):
    return line(page, top, text, bold=True, size=13.0)


def sub(page, top, text, size=12.0):
    return line(page, top, text, bold=True, size=size)


REPORT = [
    {"kind": "page", "page": 1, "width": 612.0, "height": 792.0},
    line(1, 65, "REPORT FOR ACTION", bold=True, size=18.0, x0=348),
    line(1, 131, "Widget Policy Review", bold=True, size=18.0),
    line(1, 196, "Date: April 22, 2026", bold=True),
    major(1, 284, "SUMMARY"),
    line(1, 310, "This report reviews the widget policy."),
    major(1, 340, "RECOMMENDATIONS"),
    line(1, 366, "The General Manager recommends that:"),
    line(1, 392, "1. City Council amend the widget limit."),
    major(1, 420, "FINANCIAL IMPACT"),
    line(1, 446, "There is no financial impact."),
    line(1, 747, "Widget Policy Review Page 1 of 2", size=10.0),
    {"kind": "page", "page": 2, "width": 612.0, "height": 792.0},
    major(2, 58, "COMMENTS"),
    sub(2, 100, "Background", size=13.0),
    line(2, 126, "Widgets were first counted in 2019."),
    sub(2, 160, "Review of Widget Limits"),
    line(2, 186, "The widget limit is 0.05 per block."),
    sub(2, 220, "Stage 1: An initial screening which identifies"),
    line(2, 234, "every widget by size."),
    sub(2, 270, "Implementation of the Amended"),
    sub(2, 284, "Widget Limit"),
    line(2, 310, "The new limit applies from 2027."),
    major(2, 400, "CONTACT"),
    line(2, 426, "Pat Staffer, Manager"),
    major(2, 460, "SIGNATURE"),
    line(2, 486, "Sam Signer, General Manager"),
    major(2, 520, "ATTACHMENTS"),
    line(2, 546, "Attachment 1 - Widget Maps"),
    line(2, 747, "Widget Policy Review Page 2 of 2", size=10.0),
]


def ids(chunks):
    return [c["id"] for c in chunks]


def test_one_chunk_per_major_with_status_stamp_and_pdf_page_link():
    doc, chunks = reports.chunk_staff_report(REPORT, ROW, ITEM)
    assert doc["id"] == "sr:123" and doc["kind"] == "staff_report" and doc["family"] == "decisions"
    assert doc["item_id"] == "2026.IE99.1" and doc["status_stamp"] == ITEM["status_stamp"]
    assert ids(chunks) == ["sr:123:summary", "sr:123:recommendations", "sr:123:financial-impact", "sr:123:comments"]
    for c in chunks:
        assert c["family"] == "decisions" and c["kind"] == "staff_report"
        assert c["breadcrumb"].endswith(f"[Status: {ITEM['status_stamp']}]")
        assert c["sublabel"] == ITEM["status_stamp"]
    summary = chunks[0]
    assert summary["breadcrumb"].startswith("[Staff report for 2026.IE99.1 · Widget Policy › SUMMARY]")
    assert summary["label"] == "Staff report · 2026.IE99.1 › SUMMARY"
    assert summary["body"] == "This report reviews the widget policy."
    assert chunks[3]["href"] == f"{BGRD.format(123)}#page=2"
    assert (chunks[3]["page_start"], chunks[3]["page_end"]) == (2, 2)


def test_title_block_footers_contact_signature_and_attachments_are_dropped():
    _, chunks = reports.chunk_staff_report(REPORT, ROW, ITEM)
    text = "\n".join(c["breadcrumb"] + c["body"] for c in chunks)
    for gone in ("REPORT FOR ACTION", "Date: April 22", "Page 1 of 2", "Pat Staffer", "Sam Signer", "Widget Maps",
                 "CONTACT", "SIGNATURE", "ATTACHMENTS"):
        assert gone not in text


def test_a_major_over_the_ceiling_splits_at_its_subheads(monkeypatch):
    monkeypatch.setattr(chunker, "CEILING", 35)
    _, chunks = reports.chunk_staff_report(REPORT, ROW, ITEM)
    comments = [c for c in chunks if c["id"].startswith("sr:123:comments")]
    assert ids(comments) == ["sr:123:comments:1", "sr:123:comments:2", "sr:123:comments:3"]
    assert [c["heading"] for c in comments] == [
        "COMMENTS › Background", "COMMENTS › Review of Widget Limits",
        "COMMENTS › Implementation of the Amended Widget Limit"]
    assert comments[1]["label"] == "Staff report · 2026.IE99.1 › COMMENTS › Review of Widget Limits (2/3)"
    assert comments[1]["breadcrumb"] == (
        "[Staff report for 2026.IE99.1 · Widget Policy › COMMENTS › Review of Widget Limits]\n"
        f"[Status: {ITEM['status_stamp']}]")
    # the subhead rides with its text; a bold lead-in the paragraph continues stays body text
    assert comments[1]["body"].startswith("Review of Widget Limits\n\nThe widget limit is 0.05 per block.")
    assert "Stage 1: An initial screening which identifies every widget by size." in comments[1]["body"]
    assert comments[2]["body"].startswith("Implementation of the Amended Widget Limit\n\n")


def test_an_undecided_item_stamps_its_reports_no_decision():
    item = {**ITEM, "status_stamp": "Referred by IE Committee 2026-05-06; no decision", "bylaws": []}
    _, chunks = reports.chunk_staff_report(REPORT, ROW, item)
    assert chunks and all(c["sublabel"].endswith("; no decision") for c in chunks)
