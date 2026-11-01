# Title

Hand-written text above.

<!-- headline:start (generated from evals/runs, do not edit) -->
| | refuses trick questions | cite precision | answer correct |
| --- | --- | --- | --- |
| vector search only | 3 / 7 | 0.71 | – |
| **shipped** | **7 / 7** | **0.93** | **0.88** |

24 questions written before the first build; full ladder below.
<!-- headline:end -->

Hand-written text between.

<!-- ladder:start (generated from evals/runs, do not edit) -->
24 questions written before the first build, 7 of them meant to be refused. Each row adds one thing to the row above, all run on the same final code.

| Rung | trick questions refused<br><sub>n 7</sub> | false refusals<br><sub>n 17</sub> | hit@ctx<br><sub>n 17</sub> | cite precision<br><sub>n 15–17</sub> | answer correct<br><sub>n 16–17</sub> | total p50<br><sub>n 48–51</sub> |
| --- | --- | --- | --- | --- | --- | --- |
| `dense`<br><sub>Vector search only: embed the question, take the 5 closest passages.</sub> | 3 / 7 | 1 / 17 | 0.76 | 0.71 | – | 2.1 s |
| `hybrid`<br><sub>Adds keyword search and exact section-number matching, so "591-2.1" finds § 591-2.1.</sub> | 3 / 7 | 1 / 17 | **0.94** | **0.80** | 0.70 | 2.1 s |
| `rerank`<br><sub>A reranker scores every passage against the question; if none scores high enough, it refuses before the model writes anything.</sub> | **6.7 / 7** | 1 / 17 | 0.94 | ≈ 0.81 | 0.70 | 2.1 s |
| **`shipped`** ✓ ship bar<br><sub>Brings in the by-laws that amended a cited section after the Code was last consolidated.</sub> | **7 / 7** | **0 / 17** | 0.94 | **0.93** | **0.88** | 2.3 s |

Generation columns are the mean of 3 runs. A row only counts as better when the gain is bigger than its own run-to-run spread; ≈ marks changes inside it. Answers were graded by Sonnet 5 against key facts written with the questions; on the first full run a human grader, blind to its verdicts, agreed with it on 47 of 52 facts (90%), and marked 1 fact contradicted that the judge passed, which the ship bar's contradicted check doesn't see. Cite precision counts a cited definition the app attached as correct; that rule was added after the first full run, when the citations outside gold turned out to be mostly definitions written after the gold was (0.69 → 0.78 for shipped), and applies to every row.

Alternatives tried against `shipped`, one change each.

| Rung | trick questions refused<br><sub>n 7</sub> | false refusals<br><sub>n 17</sub> | hit@ctx<br><sub>n 17</sub> | cite precision<br><sub>n 15–17</sub> | answer correct<br><sub>n 16–17</sub> | total p50<br><sub>n 48–51</sub> |
| --- | --- | --- | --- | --- | --- | --- |
| `side-sonnet`<br><sub>Sonnet 5.5 instead of Haiku 5.5, at ~20× the generation cost — no measurable gain.</sub> | 7 / 7 | 0 / 17 | 0.94 | ≈ 0.92 | ≈ 0.86 | 4.1 s |
| `side-quoted`<br><sub>Asks the model to quote the supporting sentence for every citation.</sub> | 7 / 7 | 0 / 17 | 0.94 | **0.97** | ≈ 0.87 | 2.6 s |

<!-- ladder:end -->

Hand-written text below.
