# 2026-11-02-shipped-2-dev-fix5-211903

Rung `shipped-2` · split `dev` · 3 runs · http://localhost:3124  
Git `be29ac3` · deployed `unknown` · snapshot `2026-10-28-30ada68a` · prompt `fix-5` (3c8fbfd1b525) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 13 | 0.00 |
| full@20 | 0.92 | 13 | 0.00 |
| hit@ctx | 1.00 | 13 | 0.00 |
| full@ctx | 0.92 | 13 | 0.00 |
| cite_precision | 0.76 | 13 | 0.03 |
| cite_full | 0.82 | 13 | 0.08 |
| coverage | 0.97 | 13 | 0.05 |
| answer_correct | 0.81 | 13 | 0.10 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.00 | 13 | 0.00 |
| passages_p50 | 679 ms | 54 | 134 ms |
| total_p50 | 2,334 ms | 39 | 315 ms |
| total_p95 | 3,139 ms | 39 | 308 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.12 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-shipped-2-dev-fix5-211903`): $0.0645 over 159 requests
Harness wall-clock p50: 2,264 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-deleted-dealer-hours`
- `dev-driverless-tickets`
- `dev-fireworks-backyard`
- `dev-leaf-blower`
- `dev-moved-pet-sources`
- `dev-refuse-landlord-entry`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 1: `tmc:466-7`
- `dev-fireworks-backyard` run 2: `tmc:466-7`
- `dev-fireworks-backyard` run 3: `tmc:466-7`
- `dev-lawn-height` run 1: `tmc:918-23`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 2: `tmc:918-23`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:918-23`
- `dev-park-bonfire` run 1: `tmc:608-11`
- `dev-park-bonfire` run 2: `tmc:608-11`
- `dev-amended-park-fine` run 1: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 2: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 3: `tmc:610:schedule-a:p1`
- `dev-amended-vendor-street` run 1: `tmc:740-2`
- `dev-amended-vendor-street` run 3: `tmc:740-2`
- `dev-exception-park-drinking` run 1: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 2: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 3: `tmc:608:schedule-a`
- `dev-exception-park-night` run 1: `tmc:608-34`
- `dev-exception-park-night` run 1: `tmc:349-12.1`
- `dev-exception-park-night` run 2: `tmc:608-34`
- `dev-exception-park-night` run 2: `tmc:349-12.1`
- `dev-exception-park-night` run 3: `tmc:608-34`
- `dev-exception-park-night` run 3: `bl:1482-2025:cl1:O-Y`

## Contradicted key facts (answer correct 0 for that answer)

- `dev-deleted-dealer-hours` run 1 fact 1: “No.”
- `dev-deleted-dealer-hours` run 2 fact 1: “No. Under the Chapter 545 second-hand goods licence rule, a licensee may not transact business between 11:00 p.m. and 7:00 a.m. on any day except Saturdays and the day before a statutory holiday”

## Judge spans not found word for word in the answer (check the verdict)

- `dev-deleted-holistic-fees` run 2 fact 2 (present): “By-law 1108-2025 deleted § 545-181... has been in force since 2026-01-01”

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
