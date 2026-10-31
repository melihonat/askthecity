"""check-saves and the item-page chunker on synthetic pages shaped like TMMIS (no City text)."""
import pytest

from ingest import chunk as chunker
from ingest import tmmis
from ingest.store import ManifestRow

SNAPSHOT = "2026-10-28"


def page(item_id="2026.IE99.1", tracking=None, cards=None, pad=12_000):
    """A saved item page: heading, Tracking Status list, one accordion card per stage."""
    tracking = tracking if tracking is not None else [
        "This item was considered by Infrastructure and Environment Committee on May 6, 2026 and was "
        "adopted without amendment."]
    cards = cards if cards is not None else [committee_card(item_id)]
    lis = "".join(f"<li>{t}</li>" for t in tracking)
    body = "".join(
        f'<div class="card"><div class="card-header"><h2><button>{header}<br></button></h2></div>'
        f'<div class="collapse"><div class="card-body"><h3 class="heading">{item_id.split(".", 1)[1]} - Widget '
        f'Policy</h3><div class="d-info"><dl><dt class="inline">Status:</dt><dd class="inline">{status}</dd></dl>'
        f'{inner}</div></div></div></div>'
        for header, status, inner in cards)
    return (f'<html><head><title>Agenda Item History - {item_id}</title></head><body>'
            f'<h1 class="mt-3">Item - {item_id}</h1><!-- {"x" * pad} -->'
            f'<h2 class="section-title">Tracking Status</h2><div><ul>{lis}</ul></div>'
            f'<div class="accordion" id="agenda-item-accordion">{body}</div></body></html>')


def committee_card(item_id, status="Adopted", decision="Committee Decision", extra=""):
    return ("Infrastructure and Environment Committee consideration on May 6, 2026", status,
            f'<h4>{decision}</h4><div class="wep"><p>The Committee adopted the widget policy.</p></div></div>'
            f'<h4>Origin</h4><div>(April 1, 2026) Report from the General Manager</div>'
            f'<h4>Summary</h4><div class="wep"><p>Widgets are counted yearly.</p><p>&nbsp;</p></div>'
            f'<h4>Background Information</h4><div><span class="rpt-text">Report on widgets</span><br />'
            f'<a href="https://example.test/bgrd/backgroundfile-1.pdf">link</a></div>'
            f'<h4>Communications</h4><div><span class="rpt-text">(May 5, 2026) E-mail from Pat Private</span></div>'
            f'<h4>Speakers</h4><div>Sam Speaker, Widget Owners Association</div>'
            f'{extra}<div>')


COUNCIL_CARD = ("City Council consideration on May 20 and 21, 2026", "Amended",
                '<h4>City Council Decision</h4><div class="wep"><p>City Council adopted the widget policy '
                'with amendments.</p></div></div>'
                '<h4>Motions (City Council)</h4><div><div class="italics">1 - Motion to Amend Item moved by '
                'Councillor A <span>(Carried)</span></div>'
                '<h4 class="vote-table-header">Vote <span class="normal-text">(Amend Item)</span></h4>'
                '<table><thead><tr><th>Result: Carried</th><th>Majority Required</th></tr></thead>'
                '<tbody><tr><td><span class="sr-only">Total members that voted </span>Yes: 20</td>'
                '<td>Councillor A, Councillor B</td></tr></tbody></table></div>'
                '<h4>Communications (City Council)</h4><div>(May 19, 2026) Letter from Pat Private</div><div>')


def row(item_id="2026.IE99.1"):
    return ManifestRow(sha256="abc", kind="item_page", ref=item_id, parent_ref="",
                       source_url=tmmis.ITEM_URL.format(id=item_id), obtained_by="agent_fetch",
                       obtained_at="2026-10-31T17:00:00Z", last_modified="", etag="", bytes=1,
                       content_type="text/html; charset=iso-8859-1", encoding="windows-1252")


# ── check-saves ──────────────────────────────────────────────────────────────────────────

AKAMAI = ('<HTML><HEAD><TITLE>Access Denied</TITLE></HEAD><BODY><H1>Access Denied</H1>You don\'t have '
          'permission to access this page. Reference #18.1234</BODY></HTML>' + " " * 12_000)


@pytest.mark.parametrize("data, obtained_at, expected", [
    (page().encode("cp1252"), "2026-10-31T17:00:00Z", []),
    (page().encode("cp1252"), "2026-11-04T23:59:59Z", []),
    (AKAMAI.encode("cp1252"), "2026-10-31T17:00:00Z", ["Akamai Access Denied page"]),
    (page().encode("cp1252").replace(b"Widget", b"Widg\x81t"), "2026-10-31T17:00:00Z",
     ["not windows-1252: character maps to <undefined> at byte"]),
    (page(pad=0).encode("cp1252"), "2026-10-31T17:00:00Z", ["bytes, under 10000"]),
    (page().encode("cp1252"), "2026-11-05T00:00:01Z", ["saved 2026-11-05, outside 2026-10-28…2026-11-04"]),
    (page().encode("cp1252"), "2026-10-27T12:00:00Z", ["saved 2026-10-27, outside"]),
    (page().replace("Tracking Status", "Tracking").encode("cp1252"), "2026-10-31T17:00:00Z",
     ["no Tracking Status"]),
    (page(item_id="2026.IE99.2").encode("cp1252"), "2026-10-31T17:00:00Z", ["no item heading"]),
], ids=["passes", "last day of window", "akamai", "wrong encoding", "too small", "after window",
        "before snapshot", "no tracking status", "wrong item heading"])
def test_page_failures(data, obtained_at, expected):
    got = tmmis.page_failures("2026.IE99.1", data, obtained_at, SNAPSHOT)
    assert len(got) == len(expected)
    for g, e in zip(got, expected):
        assert e in g


def full_list():
    return [f"{m}.{i}" for m, n in tmmis.MEETING_COUNTS.items() for i in range(1, n + 1)]


@pytest.mark.parametrize("ids, expected", [
    (full_list(), []),
    ([i for i in full_list() if i != "2026.IE29.10"], ["2026.IE29: 9 items, expected 10"]),
    (full_list() + ["2026.IE31.13"], ["2026.IE31: 13 items, expected 12"]),
    (full_list() + ["2026.IE32.1"], ["2026.IE32: not an IE24–IE31 meeting"]),
    ([i for i in full_list() if i != "2025.IE24.2"] + ["2025.IE24.1"], ["listed twice: ['2025.IE24.1']"]),
], ids=["matches", "one missing", "one extra", "wrong meeting", "duplicate"])
def test_count_failures(ids, expected):
    assert tmmis.count_failures(ids) == expected


# ── status stamp ─────────────────────────────────────────────────────────────────────────

COMMITTEE = "This item was considered by Infrastructure and Environment Committee on May 6, 2026"


@pytest.mark.parametrize("lines, stamp, decided", [
    (["City Council adopted this item on May 20 and 21, 2026 with amendments.",
      f"{COMMITTEE} and was adopted with amendments. It will be considered by City Council on May 20 and 21, 2026.",
      "See also By-laws 470-2026 , 12-2026"],
     "Adopted with amendments by City Council 2026-05-21 · By-laws 12-2026, 470-2026", True),
    (["City Council adopted this item on December 16, 17 and 18, 2025 without amendments and without debate."],
     "Adopted by City Council 2025-12-18", True),
    ([f"{COMMITTEE} and was adopted without amendment."], "Adopted by IE Committee 2026-05-06", True),
    ([f"{COMMITTEE}. The Infrastructure and Environment Committee postponed consideration of this item."],
     "Deferred by IE Committee 2026-05-06; no decision", False),
    ([f"{COMMITTEE}. The Infrastructure and Environment Committee has referred this item to an official "
      "or other body without making a decision."], "Referred by IE Committee 2026-05-06; no decision", False),
    ([f"{COMMITTEE}. The Infrastructure and Environment Committee has referred this item to an official.",
      "See also By-law 470-2026"], "Referred by IE Committee 2026-05-06 · By-law 470-2026; no decision", False),
    ([f"{COMMITTEE}. The Committee received the item for information only."],
     "Received for information by IE Committee 2026-05-06; no decision", False),
    (["This item was ruled out of order at Infrastructure and Environment Committee on May 6, 2026."],
     "Ruled out of order at IE Committee 2026-05-06; no decision", False),
    (["City Council considered this item on May 20 and 21, 2026 and received the item for information."],
     "Received for information by City Council 2026-05-21; no decision", False),
])
def test_status_stamp(lines, stamp, decided):
    got_stamp, _, got_decided, _ = tmmis.status_stamp(lines)
    assert (got_stamp, got_decided) == (stamp, decided)
    assert got_stamp.endswith("; no decision") != decided


def test_status_stamp_refuses_an_item_still_awaiting_council():
    with pytest.raises(ValueError, match="awaiting City Council"):
        tmmis.status_stamp([f"{COMMITTEE} and was adopted. It will be considered by City Council on May 20, 2026."])


# ── chunker ──────────────────────────────────────────────────────────────────────────────

ADOPTED = page(tracking=[
    "City Council adopted this item on May 20 and 21, 2026 with amendments.",
    f"{COMMITTEE} and was adopted without amendment. It will be considered by City Council on May 20 and 21, 2026.",
    "See also By-law 470-2026"],
    cards=[COUNCIL_CARD, committee_card("2026.IE99.1", decision="Committee Recommendations")])


def test_stages_are_separate_chunks_and_carry_the_status_stamp():
    doc, chunks = tmmis.chunk_item_page(ADOPTED, row())
    assert [c["id"] for c in chunks] == ["ie:2026.IE99.1:council", "ie:2026.IE99.1:committee"]
    assert doc["status_stamp"] == "Adopted with amendments by City Council 2026-05-21 · By-law 470-2026"
    assert doc["bylaws"] == ["470-2026"] and doc["decision_date"] == "2026-05-21"
    for c in chunks:
        assert c["family"] == "decisions" and c["kind"] == "item_page"
        assert c["breadcrumb"].endswith(f"[Status: {doc['status_stamp']}]")
        assert c["sublabel"].endswith(doc["status_stamp"])
        assert c["href"] == "https://secure.toronto.ca/council/agenda-item.do?item=2026.IE99.1"
    council, committee = chunks
    assert "City Council adopted the widget policy" in council["body"]
    assert "Committee adopted" not in council["body"]
    assert "City Council" not in committee["body"]


def test_labels_name_the_stage():
    _, chunks = tmmis.chunk_item_page(ADOPTED, row())
    assert [c["label"] for c in chunks] == ["Item 2026.IE99.1 · City Council decision",
                                            "Item 2026.IE99.1 · IE Committee recommendation"]
    assert [c["sublabel"][:10] for c in chunks] == ["2026-05-21", "2026-05-06"]


def test_communications_speakers_and_background_are_stripped():
    _, chunks = tmmis.chunk_item_page(ADOPTED, row())
    text = "\n".join(c["breadcrumb"] + c["body"] for c in chunks)
    for gone in ("Pat Private", "Sam Speaker", "Communications", "Speakers", "Background Information",
                 "backgroundfile"):
        assert gone not in text
    assert "Origin" in text and "Summary" in text and "Motions (City Council)" in text


def test_votes_render_as_a_table_without_screen_reader_text():
    _, chunks = tmmis.chunk_item_page(ADOPTED, row())
    council = chunks[0]["body"]
    assert "| Result: Carried | Majority Required |\n| --- | --- |\n| Yes: 20 | Councillor A, Councillor B |" in council
    assert "Total members" not in council


def test_a_referred_item_reads_no_decision():
    html = page(tracking=[f"{COMMITTEE}. The Infrastructure and Environment Committee has referred this item to "
                          "an official or other body without making a decision."],
                cards=[committee_card("2026.IE99.1", status="Referred")])
    doc, chunks = tmmis.chunk_item_page(html, row())
    assert doc["status_stamp"] == "Referred by IE Committee 2026-05-06; no decision"
    assert chunks and all(c["sublabel"].endswith("; no decision") for c in chunks)
    assert all("Adopted" not in c["sublabel"] and "Adopted" not in c["breadcrumb"] for c in chunks)
    assert chunks[0]["label"] == "Item 2026.IE99.1 · IE Committee decision"


def test_a_stage_over_the_ceiling_splits_at_its_blocks(monkeypatch):
    monkeypatch.setattr(chunker, "CEILING", 20)
    _, chunks = tmmis.chunk_item_page(page(), row())
    assert [c["id"] for c in chunks] == ["ie:2026.IE99.1:committee:1", "ie:2026.IE99.1:committee:2",
                                         "ie:2026.IE99.1:committee:3"]
    assert [c["heading"] for c in chunks] == ["Committee Decision", "Origin", "Summary"]
    assert chunks[0]["label"] == "Item 2026.IE99.1 · IE Committee decision (1/3)"
    assert all(c["stage"] == "committee" for c in chunks)
