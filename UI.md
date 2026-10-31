# Answer UI

How an answer, its citations, a refusal, a limit and the eval table look. Chosen from three
throwaway prototype variants. The response shape is in [`CONTRACT.md`](CONTRACT.md); terms are defined in
[`CONTEXT.md`](CONTEXT.md).

## Shape

- **Single-turn Q&A, two panes.** Not a chat thread: each question replaces the last, no
  follow-ups, no query rewriting. Left: question box, example chips, the question, the
  answer. Right: the sources panel, sticky. Below 860 px the panel stacks under the answer.
- **Header:** `Ask the City` · nav `Ask` | `Evals · 7/7 trick questions refused` (the number
  comes from the same data as `evals/RESULTS.md`) · `documents as of <snapshot date>`.
- **Scope band** under the header: the short line ("Toronto Municipal Code + Infrastructure
  & Environment Committee decisions, as of <date>.") with a "What's included" expander
  holding the full scope sentence. A refusal always shows the full sentence.
- **Question box:** textarea with a live `n / 300` counter that turns red past 300; Enter
  submits.
- **Example chips:** four, one of them a trick question (dashed border, "· try a trick")
  that is refused. Their responses are cached, so they work in every limit state.

## Answer

- Answer text in a larger reading size. Inline markers are small numbered tags after the
  sentence. Hover or tap highlights and scrolls to the passage card.
- **Gap sentence** (the final uncited sentence): italic, muted, no icon. Other uncited
  sentences (a lead "No.") render plainly.
- **Sources panel:**
  - **"Cited (n)":** one card per cited passage, in marker order. Card: number tag, label in
    bold, badges, sublabel line (breadcrumb · dates · page), `source ↗` to the PDF
    `#page=` or item page, body clamped to ~6 lines with "show full passage". Markdown
    tables render as tables. No span highlighting: the whole chunk is the citation.
  - **"N more retrieved, not cited":** collapsed by default; expands to the same cards,
    dimmed.
- **Badges:** `amended since by By-law …` (amber) on a § with `amendedSince`; `amendment to
  a retrieved §` (violet) on a companion; `adopted` (green) or `no decision` (amber) from a
  Decisions chunk's status stamp; `not yet law` (red) on a replacement § not yet in force.

## Waiting

Buffered, not streamed. On submit: a skeleton in both panes. When the `passages` event
arrives, the panel fills under "Passages found" and the left says "Found N passages.
Writing an answer from them…" above a skeleton. The final `AskResponse` splits the panel
into cited and not cited.

## Refusal

Left: headline **"The documents don't cover this."**, the reason's line from `CONTRACT.md`,
then the full scope sentence in muted text. Right: the reason's nearest-passages heading
over the nearest passages, dimmed cards. No model-written text.

## Limit

A neutral blue notice in the left pane, never styled like a refusal: the limit's headline
and line, then "The example questions and the eval results still work." The panel says no
search was run.

| Limit | Headline | Line |
| --- | --- | --- |
| `ip_daily` | You've asked 30 questions today. | That's the per-visitor limit for this demo. It resets at midnight Toronto time. |
| `global_daily` | The demo is resting until tomorrow. | It has answered its 500 questions for today. It resets at midnight Toronto time. |
| `budget` | The demo is resting until tomorrow. | This month's model budget is used up. |
| `burst` | Too many questions at once. | Wait a few seconds and try again. |
| `too_long` | That question is over 300 characters. | Shorten it and ask again. |
| `unavailable` | The demo can't answer right now. | A service it relies on didn't respond. Try again in a minute. |

An HTTP 429 from the firewall's burst rule (no NDJSON body) renders as `burst`; any other
failed request, or a dropped connection, as `unavailable`.

## `/evals`

A real route, static, rendered from the same data as `evals/RESULTS.md`, so it costs $0 and
works in every limit state. Full width, no sources panel. One-line intro (24 questions
written before the build, 7 meant to be refused), the main ladder table with `shipped`
highlighted, one muted "why" line under each rung name, `n` under each column heading,
then the judge/human agreement line and the spread rule, then the side-rung table. The
words are in [`STORY.md`](STORY.md).
