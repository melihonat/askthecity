"""The coverage sentence splitter: never breaks on §, s., ss., No. or decimals; counts only sentences
of 6+ words and never the gap sentence."""
import pytest

from evals.sentences import coverage, split_sentences


@pytest.mark.parametrize("text", [
    "Under s. 5 of the by-law a permit is needed [1].",
    "Sections ss. 6 and 7 set the fee for the permit [1].",
    "By-law No. 1482-2025 rewrote the section on drones [2].",
    "The heat is measured 1.5 m above the floor [1].",
    "The rule in § 591-2.3 B applies to Saturdays [1].",
    "Work may start at 9 a.m. Monday through Friday [1].",
])
def test_does_not_split_inside_a_sentence(text):
    assert split_sentences(text) == [text]


def test_splits_on_stops_and_keeps_trailing_markers_with_their_sentence():
    text = 'No drilling before 9 a.m. on Saturdays. [1] "Quiet" hours run late! Is it allowed? § 591-2.3 says no [2].'
    assert split_sentences(text) == [
        "No drilling before 9 a.m. on Saturdays. [1]",
        '"Quiet" hours run late!',
        "Is it allowed?",
        "§ 591-2.3 says no [2].",
    ]


def test_coverage_counts_sentences_of_six_words_or_more():
    text = "Drilling before 9 a.m. on Saturdays is not allowed [1]. Yes, really. Some exemptions exist for emergency utility work."
    # "Yes, really." is under 6 words; the last, uncited after a cited one, is the gap sentence
    assert coverage(text) == (1, 1)


def test_coverage_skips_the_gap_sentence_but_not_an_uncited_sentence_before_a_cited_one():
    text = ("Some exemptions exist for emergency work by utilities. "
            "A permit is needed for any other early work [2]. "
            "The documents don't cover fines for provincial highways.")
    assert coverage(text) == (1, 2)


def test_coverage_of_an_answer_without_counted_sentences():
    assert coverage("Yes [1].") == (0, 0)
