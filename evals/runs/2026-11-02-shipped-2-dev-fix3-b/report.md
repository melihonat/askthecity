# 2026-11-02-shipped-2-dev-fix3-b-195943

Rung `shipped-2` · split `dev` · 3 runs · http://localhost:3124  
Git `90fb348` · deployed `unknown` · snapshot `2026-10-28-30ada68a` · prompt `fix-3` (5198b172b231) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 12 | 0.00 |
| full@20 | 0.92 | 12 | 0.00 |
| hit@ctx | 1.00 | 12 | 0.00 |
| full@ctx | 0.92 | 12 | 0.00 |
| cite_precision | 0.68 | 12 | 0.08 |
| cite_full | 0.75 | 12 | 0.17 |
| coverage | 0.96 | 12 | 0.05 |
| answer_correct | 0.83 | 12 | 0.04 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.00 | 12 | 0.00 |
| passages_p50 | 725 ms | 51 | 103 ms |
| total_p50 | 2,489 ms | 36 | 228 ms |
| total_p95 | 3,528 ms | 36 | 1,408 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.11 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-shipped-2-dev-fix3-b-195943`): $0.0606 over 150 requests
Harness wall-clock p50: 2,416 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-amended-park-fine`
- `dev-deleted-dealer-hours`
- `dev-driverless-tickets`
- `dev-exception-park-drinking`
- `dev-leaf-blower`
- `dev-refuse-landlord-entry`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 1: `tmc:466-7`
- `dev-fireworks-backyard` run 2: `tmc:466-7`
- `dev-fireworks-backyard` run 3: `tmc:466-7`
- `dev-pool-permit` run 3: `tmc:681-11:T`
- `dev-pool-permit` run 3: `tmc:681-11:U-W`
- `dev-lawn-height` run 1: `tmc:918-23`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-park-bonfire` run 1: `tmc:608-11`
- `dev-park-bonfire` run 2: `tmc:608-11`
- `dev-park-bonfire` run 3: `tmc:608-11`
- `dev-amended-park-fine` run 1: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 2: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 3: `tmc:610:schedule-a:p1`
- `dev-amended-vendor-street` run 1: `tmc:740-2`
- `dev-amended-vendor-street` run 2: `tmc:740-2`
- `dev-amended-vendor-street` run 3: `tmc:740-2`
- `dev-exception-park-drinking` run 1: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 2: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 2: `tmc:608-9`
- `dev-exception-park-drinking` run 3: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 3: `tmc:608-9`
- `dev-exception-park-night` run 1: `bl:1482-2025:cl1:O-Y`
- `dev-exception-park-night` run 1: `tmc:608-34`
- `dev-exception-park-night` run 2: `tmc:608-34`
- `dev-exception-park-night` run 3: `tmc:608-34`
- `dev-exception-park-night` run 3: `tmc:349-12.1`

## Contradicted key facts (answer correct 0 for that answer)

- `dev-deleted-dealer-hours` run 1 fact 1: “No. Under the second-hand goods licence rules, you may not transact business between 11:00 p.m. and 7:00 a.m.”
- `dev-deleted-dealer-hours` run 2 fact 1: “No.”
- `dev-deleted-dealer-hours` run 3 fact 1: “No. Under the Code's second-hand goods rules, no licensee may transact business between 11:00 p.m. and 7:00 a.m.”

## Judge spans not found word for word in the answer (check the verdict)

- `dev-deleted-holistic-fees` run 2 fact 2 (present): “By-law 1108-2025 deleted § 545-181... that deletion took effect on 2026-01-01”

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
