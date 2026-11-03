# 2026-11-02-shipped-2-dev-fix3-moved-204251

Rung `shipped-2` · split `dev` · 3 runs · http://localhost:3124  
Git `b13cce9` · deployed `unknown` · snapshot `2026-10-28-30ada68a` · prompt `fix-3` (5198b172b231) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 13 | 0.00 |
| full@20 | 0.92 | 13 | 0.00 |
| hit@ctx | 1.00 | 13 | 0.00 |
| full@ctx | 0.92 | 13 | 0.00 |
| cite_precision | 0.79 | 12 | 0.04 |
| cite_full | 0.78 | 12 | 0.10 |
| coverage | 0.98 | 12 | 0.03 |
| answer_correct | 0.85 | 12 | 0.17 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.05 | 13 | 0.08 |
| passages_p50 | 682 ms | 54 | 139 ms |
| total_p50 | 2,504 ms | 37 | 604 ms |
| total_p95 | 3,411 ms | 37 | 745 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.11 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-shipped-2-dev-fix3-moved-204251`): $0.0645 over 159 requests
Harness wall-clock p50: 2,302 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-amended-park-fine`
- `dev-deleted-holistic-fees`
- `dev-driverless-tickets`
- `dev-exception-park-drinking`
- `dev-fireworks-backyard`
- `dev-leaf-blower`
- `dev-moved-pet-sources`
- `dev-refuse-landlord-entry`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

- `dev-exception-park-night`: refusal:model_declined → answer → refusal:model_declined

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 1: `tmc:466-7`
- `dev-fireworks-backyard` run 2: `tmc:466-7`
- `dev-lawn-height` run 1: `tmc:629-11`
- `dev-lawn-height` run 2: `tmc:918-23`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:918-23`
- `dev-lawn-height` run 3: `bl:1512-2025:629-4.2`
- `dev-park-bonfire` run 1: `tmc:608-11`
- `dev-amended-park-fine` run 1: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 2: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 3: `tmc:610:schedule-a:p1`
- `dev-amended-vendor-street` run 1: `tmc:740-2`
- `dev-exception-park-drinking` run 1: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 2: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 3: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 3: `tmc:608-9`
- `dev-exception-park-night` run 2: `tmc:608-34`
- `dev-exception-park-night` run 2: `bl:1482-2025:cl1:O-Y`
- `dev-exception-park-night` run 2: `tmc:349-12.1`
- `dev-moved-pet-sources` run 3: `tmc:545-253`

## Contradicted key facts (answer correct 0 for that answer)

- `dev-leaf-blower` run 1 fact 1: “until 9 p.m. on Saturdays, Sundays and statutory holidays”
- `dev-deleted-dealer-hours` run 2 fact 1: “No. Under the current rule, a second-hand goods licensee may not transact business between 11:00 p.m. and 7:00 a.m.”

## Judge spans not found word for word in the answer (check the verdict)

- `dev-deleted-holistic-fees` run 3 fact 2 (present): “By-law 1108-2025 deleted § 545-181... has been in force since 2026-01-01”

## Refusal reasons

- Answer questions refused: model_declined × 2
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
