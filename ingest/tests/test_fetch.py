"""fetch-bylaws: reading a yearly law list and choosing the candidate amending and replacement by-laws."""
from ingest.fetch import bylaw_candidates, bylaw_list, replacement_candidates

PAGE = """
<tr><td class="bylawNum"><font><a href="http://www.toronto.ca/legdocs/bylaws/2026/law0470.pdf" target="_blank">
  470-2026
  </a></font></td>
<td>
  To amend City of Toronto Municipal Code Chapter 681, Sewers, to reflect the new &amp; lower limit.
  &nbsp;
</td></tr>
"""

CONSOLIDATED = {"681": "2023-05-15", "950": "2026-07-30", "608": "2024-06-03", "39": None, "497": "2025-01-01"}


def test_a_list_row_reads_as_number_url_and_title():
    assert bylaw_list(PAGE) == [(
        "470-2026", "https://www.toronto.ca/legdocs/bylaws/2026/law0470.pdf",
        "To amend City of Toronto Municipal Code Chapter 681, Sewers, to reflect the new & lower limit.")]


def test_candidates_name_a_snapshot_chapter_consolidated_no_later_than_their_year():
    listing = [
        ("470-2026", "u1", "To amend City of Toronto Municipal Code Chapter 681, Sewers."),
        ("1482-2025", "u2", "To amend City of Toronto Municipal Code Chapter 608 Parks"),
        ("5-2026", "u3", "To amend City of Toronto Municipal Code Chapter 950, Traffic and Parking."),
        ("5-2025", "u4", "To amend City of Toronto Municipal Code Chapter 950, Traffic and Parking."),
        ("7-2020", "u5", "To amend City of Toronto Municipal Code Chapter 39, Debentures."),
        ("8-2026", "u6", "To amend Zoning By-law 569-2013 with respect to Chapter 681."),
        ("9-2026", "u7", "To amend City of Toronto Municipal Code Chapter 123, Widgets."),
    ]
    assert [(n, chs) for n, _, _, chs in bylaw_candidates(listing, CONSOLIDATED)] == [
        ("470-2026", ["681"]), ("1482-2025", ["608"]), ("5-2026", ["950"]), ("7-2020", ["39"])]


def test_street_address_and_replacement_titles_are_left_out_but_not_other_respecting():
    listing = [
        ("18-2026", "u", "To amend City of Toronto Municipal Code Chapter 950, Traffic and Parking, respecting "
                         "Beverly Glen Boulevard."),
        ("736-2026", "u", "To amend City of Toronto Municipal Code Chapter 950, Traffic and Parking, respecting The Kingsway"),
        ("61-2026", "u", "To amend City of Toronto Municipal Code Chapter 950, in respect of 1337-1355 King Street"),
        ("1511-2025", "u", "To repeal City of Toronto Municipal Code Chapter 497, Heating and replace with new "
                           "Chapter 497, Indoor Temperature Standards"),
        ("1086-2025", "u", "To amend Bylaw 104-2025, respecting the amendment of City of Toronto Municipal Code "
                           "Chapter 608"),
        ("1381-2025", "u", "To amend City of Toronto Municipal Code Chapter 608, in respect of increased penalty amounts"),
    ]
    assert [n for n, *_ in bylaw_candidates(listing, CONSOLIDATED)] == ["1086-2025", "1381-2025"]


def test_replacement_candidates_repeal_and_replace_the_same_snapshot_chapter():
    listing = [
        ("1512-2025", "u1", "To repeal City of Toronto Municipal Code Chapter 629, Property Standards and replace "
                            "with new Chapter 629, Property Standards as set out in Schedule A to this by-law"),
        ("1511-2025", "u2", "To repeal City of Toronto Municipal Code Chapter 497, Heating and replace with new "
                            "Chapter 497, Indoor Temperature Standards"),     # Ch 497 consolidated 2025: in
        ("1498-2019", "u3", "To repeal the current City of Toronto Municipal Code Chapter 681, Sewers, and replace "
                            "it with a new City of Toronto Municipal Code Chapter 681, Sewers."),   # before 2023
        ("1513-2025", "u4", "To enact a new City of Toronto Municipal Code Chapter 611, Pest Management"),
        ("1131-2020", "u5", "To repeal City of Toronto Municipal Code Chapter 39, Debentures."),
    ]
    consolidated = {**CONSOLIDATED, "629": "2025-04-30"}
    assert [(n, chs) for n, _, _, chs in replacement_candidates(listing, consolidated)] == [
        ("1512-2025", ["629"]), ("1511-2025", ["497"])]
