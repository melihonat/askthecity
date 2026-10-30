"""The amendment linker: which by-laws count as amending a chapter since its consolidation, and the
`amendments` rows and `amended_since` they produce. Synthetic documents and chunks only."""
from ingest.chunk import noted_bylaws
from ingest.link import link, resolve


def chapter(ch, consolidated="2025-06-01", noted=()):
    return {"id": f"tmc:{ch}", "kind": "chapter", "title": f"Ch {ch} Widgets",
            "consolidated_as_of": consolidated, "noted_bylaws": list(noted)}


def code(section, part=""):
    ch = section.split("-")[0]
    return {"id": f"tmc:{section}{part}", "document_id": f"tmc:{ch}", "kind": "chapter", "chapter": ch,
            "section": section, "amended_since": [],
            "breadcrumb": f"[Toronto Municipal Code › Ch {ch} Widgets › § {section}]\n[consolidated as of 2025-06-01]"}


def bylaw(number, title_chapters=("999",), enacted="2026-05-21", in_force=None):
    return {"id": f"bl:{number}", "kind": "amending_bylaw", "number": number, "enacted": enacted,
            "in_force": in_force, "short_title": "To amend " + ", ".join(f"Chapter {c}" for c in title_chapters)}


def clause(number, n, amends, chapters=("999",), schedule_only=False):
    return {"id": f"bl:{number}:cl{n}", "document_id": f"bl:{number}", "kind": "amending_bylaw",
            "amends": list(amends), "chapters": list(chapters), "schedule_only": schedule_only,
            "body": "…", "breadcrumb": "", "sublabel": ""}


def code_chunks():
    return [code("999-4", ":A-I"), code("999-4", ":J"), code("999-7"), code("999-1316B")]


def run(docs, chunks):
    documents, out, amendments, skipped = link([chapter("999"), *docs], [*code_chunks(), *chunks])
    return {d["id"] for d in documents}, {c["id"]: c for c in out}, amendments, skipped


def test_an_amended_section_gets_amendments_rows_and_amended_since_on_every_chunk():
    _, chunks, amendments, skipped = run([bylaw("470-2026")], [clause("470-2026", 1, ["999-4(J)"])])
    assert amendments == [{"amending_chunk_id": "bl:470-2026:cl1", "target_section": "999-4"}]
    assert chunks["tmc:999-4:A-I"]["amended_since"] == chunks["tmc:999-4:J"]["amended_since"] == ["470-2026"]
    assert chunks["tmc:999-7"]["amended_since"] == []
    assert chunks["tmc:999-4:J"]["breadcrumb"].endswith(
        "[consolidated as of 2025-06-01 · amended since by By-law 470-2026]")
    c = chunks["bl:470-2026:cl1"]
    assert c["amends"] == [{"chapter": "999", "section": "999-4", "sub": "(J)"}]
    assert c["sublabel"] == "amends § 999-4(J) · in force 2026-05-21"
    assert c["breadcrumb"] == ("[By-law 470-2026 › To amend Chapter 999]\n"
                               "[amends Ch 999 Widgets § 999-4(J) · enacted 2026-05-21 · in force on enactment]")
    assert skipped == []


def test_a_bylaw_already_in_the_chapters_notes_is_not_amended_since():
    docs, chunks, amendments, skipped = link(
        [chapter("999", noted=["470-2026"]), bylaw("470-2026")],
        [*code_chunks(), clause("470-2026", 1, ["999-4J"])])
    assert "bl:470-2026" not in {d["id"] for d in docs} and "bl:470-2026:cl1" not in {c["id"] for c in chunks}
    assert amendments == [] and all(c["amended_since"] == [] for c in chunks)
    assert skipped == [{"ref": "bylaw-470-2026", "reason": "already folded into Ch 999"}]


def test_notes_are_read_across_wrapped_lines_and_footnotes():
    lines = [{"kind": "line", "text": t} for t in
             ["[History: Adopted 2023-06-18 by By-law 600-", "2023]", "B. Text. [Amended 2026-05-21 by",
              "By-law 470-2026]", "See By-law 1-2020 for background."]]
    assert noted_bylaws(lines) == ["470-2026", "600-2023"]


def test_a_bylaw_that_took_effect_by_the_consolidation_date_is_already_in_it():
    for enacted, in_force, linked in [("2025-05-01", None, False), ("2025-06-01", None, False),
                                      ("2025-05-01", "2025-07-01", True), ("2025-06-02", None, True)]:
        _, _, amendments, _ = run([bylaw("9-2025", enacted=enacted, in_force=in_force)],
                                  [clause("9-2025", 1, ["999-7"])])
        assert bool(amendments) is linked, (enacted, in_force)


def test_schedule_only_bylaws_are_dropped_and_schedule_clauses_of_others_too():
    docs, chunks, _, skipped = run(
        [bylaw("18-2026"), bylaw("19-2026")],
        [clause("18-2026", 1, [], schedule_only=True),
         clause("19-2026", 1, [], schedule_only=True), clause("19-2026", 2, ["999-7"])])
    assert "bl:18-2026" not in docs and "bl:19-2026" in docs
    assert skipped == [{"ref": "bylaw-18-2026", "reason": "amends schedules only"}]
    assert "bl:19-2026:cl1" not in chunks and "bl:19-2026:cl2" in chunks


def test_only_chapters_the_bylaw_names_are_linked_and_unknown_sections_are_ignored():
    # "1-3" is a street address in a vending by-law, not § 1-3; § 999-99 isn't in the snapshot
    _, chunks, amendments, _ = run([bylaw("522-2022", enacted="2026-01-01")],
                                   [clause("522-2022", 1, ["1-3", "999-99", "999-7"])])
    assert amendments == [{"amending_chunk_id": "bl:522-2022:cl1", "target_section": "999-7"}]
    assert chunks["bl:522-2022:cl1"]["sublabel"] == "amends § 999-7 · in force 2026-01-01"


def test_a_clause_with_no_resolvable_section_is_kept_and_names_its_chapter():
    _, chunks, amendments, _ = run([bylaw("5-2026", in_force="2027-01-01")], [clause("5-2026", 1, [])])
    assert amendments == []
    assert chunks["bl:5-2026:cl1"]["sublabel"] == "amends Ch 999 · enacted 2026-05-21 · in force 2027-01-01"


def test_resolve_prefers_a_real_section_over_a_subsection_letter():
    known = {"999-4", "999-1316B", "999-6.2"}
    assert resolve("999-4J", known) == ("999-4", "J")
    assert resolve("999-1316B", known) == ("999-1316B", "")
    assert resolve("999-6.2.A", known) == ("999-6.2", "A")
    assert resolve("999-4(J)(2)", known) == ("999-4", "(J)(2)")
    assert resolve("999-5", known) is None
