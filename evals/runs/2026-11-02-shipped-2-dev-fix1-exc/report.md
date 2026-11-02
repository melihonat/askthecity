# 2026-11-02-shipped-2-dev-fix1-exc-165800

Rung `shipped-2` · split `dev` · 3 runs · http://localhost:3124  
Git `f719fd5` · deployed `unknown` · snapshot `2026-10-28-30ada68a` · prompt `fix-1` (09db545cdcc2) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 12 | 0.00 |
| full@20 | 0.92 | 12 | 0.00 |
| hit@ctx | 1.00 | 12 | 0.00 |
| full@ctx | 0.92 | 12 | 0.00 |
| cite_precision | 0.77 | 10 | 0.10 |
| cite_full | 0.73 | 10 | 0.10 |
| coverage | 0.98 | 10 | 0.05 |
| answer_correct | 0.83 | 10 | 0.05 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.17 | 12 | 0.00 |
| passages_p50 | 805 ms | 51 | 153 ms |
| total_p50 | 2,617 ms | 30 | 275 ms |
| total_p95 | 3,735 ms | 30 | 537 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.09 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-shipped-2-dev-fix1-exc-165800`): $0.0590 over 150 requests
Harness wall-clock p50: 2,607 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-amended-park-fine`
- `dev-deleted-dealer-hours`
- `dev-driverless-tickets`
- `dev-exception-park-drinking`
- `dev-fireworks-backyard`
- `dev-refuse-landlord-entry`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 2: `tmc:466-7`
- `dev-lawn-height` run 1: `tmc:629-11`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 2: `bl:1512-2025:629-4.2`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-park-bonfire` run 2: `tmc:608-11`
- `dev-amended-park-fine` run 1: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 2: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 3: `tmc:610:schedule-a:p1`
- `dev-amended-vendor-street` run 1: `tmc:740-2`
- `dev-amended-vendor-street` run 2: `tmc:740-2`
- `dev-amended-vendor-street` run 3: `tmc:740-2`
- `dev-exception-park-drinking` run 1: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 2: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 3: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 3: `tmc:608-9`

## Contradicted key facts (answer correct 0 for that answer)

None.

## Judge spans not found word for word in the answer (check the verdict)

None.

## Refusal reasons

- Answer questions refused: model_declined × 6
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
