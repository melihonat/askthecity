# 2026-11-02-shipped-2-dev-fix4-171629

Rung `shipped-2` · split `dev` · 3 runs · http://localhost:3124  
Git `fac1582` · deployed `unknown` · snapshot `2026-10-28-30ada68a` · prompt `fix-4` (2b65cf8acc06) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 12 | 0.00 |
| full@20 | 0.92 | 12 | 0.00 |
| hit@ctx | 1.00 | 12 | 0.00 |
| full@ctx | 0.92 | 12 | 0.00 |
| cite_precision | 0.78 | 12 | 0.06 |
| cite_full | 0.83 | 12 | 0.00 |
| coverage | 0.97 | 13 | 0.06 |
| answer_correct | 0.85 | 12 | 0.12 |
| refusal_recall | 0.80 | 5 | 0.00 |
| false_refusals | 0.00 | 12 | 0.00 |
| passages_p50 | 725 ms | 51 | 46 ms |
| total_p50 | 2,434 ms | 39 | 299 ms |
| total_p95 | 3,482 ms | 39 | 2,616 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.10 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-shipped-2-dev-fix4-171629`): $0.0605 over 150 requests
Harness wall-clock p50: 2,394 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-deleted-holistic-fees`
- `dev-driverless-tickets`
- `dev-refuse-landlord-entry`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 1: `tmc:466-7`
- `dev-fireworks-backyard` run 2: `tmc:466-7`
- `dev-fireworks-backyard` run 3: `tmc:466-7`
- `dev-lawn-height` run 1: `tmc:629-11`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 2: `tmc:489-3.3`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-lawn-height` run 3: `bl:1512-2025:629-4.2`
- `dev-lawn-height` run 3: `bl:1512-2025:629-4.3`
- `dev-amended-park-fine` run 2: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 3: `tmc:610:schedule-a:p1`
- `dev-amended-vendor-street` run 1: `tmc:740-2`
- `dev-exception-park-drinking` run 1: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 2: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 3: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 3: `tmc:608-9`
- `dev-exception-park-night` run 1: `tmc:349-12.1`
- `dev-exception-park-night` run 1: `tmc:608-34`
- `dev-exception-park-night` run 2: `tmc:349-12.1`
- `dev-exception-park-night` run 2: `tmc:608-34`
- `dev-exception-park-night` run 3: `tmc:349-12.1`
- `dev-exception-park-night` run 3: `bl:1482-2025:cl1:O-Y`

## Contradicted key facts (answer correct 0 for that answer)

- `dev-deleted-dealer-hours` run 1 fact 1: “No. Under the old rule, a second-hand goods licensee could not transact business between 11:00 p.m. and 7:00 a.m.”

## Judge spans not found word for word in the answer (check the verdict)

- `dev-deleted-holistic-fees` run 2 fact 2 (present): “By-law 1108-2025 deleted § 545-181... that by-law has been in force since 2026-01-01”

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 6, answer × 3, below_threshold × 6

## Pinned questions (a § number matched)

None.
