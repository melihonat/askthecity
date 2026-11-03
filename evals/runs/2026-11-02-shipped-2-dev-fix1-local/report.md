# 2026-11-02-shipped-2-dev-fix1-local-164246

Rung `shipped-2` · split `dev` · 3 runs · http://localhost:3124  
Git `a26b527` · deployed `unknown` · snapshot `2026-10-28-30ada68a` · prompt `fix-1` (09db545cdcc2) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 9 | 0.00 |
| full@20 | 0.89 | 9 | 0.00 |
| hit@ctx | 1.00 | 9 | 0.00 |
| full@ctx | 0.89 | 9 | 0.00 |
| cite_precision | 0.86 | 9 | 0.09 |
| cite_full | 0.74 | 9 | 0.11 |
| coverage | 0.99 | 9 | 0.04 |
| answer_correct | 0.81 | 9 | 0.06 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.00 | 9 | 0.00 |
| passages_p50 | 730 ms | 42 | 148 ms |
| total_p50 | 2,493 ms | 27 | 596 ms |
| total_p95 | 3,250 ms | 27 | 8,499 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.08 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-shipped-2-dev-fix1-local-164246`): $0.0485 over 123 requests
Harness wall-clock p50: 2,272 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-amended-park-fine`
- `dev-deleted-holistic-fees`
- `dev-driverless-tickets`
- `dev-fireworks-backyard`
- `dev-leaf-blower`
- `dev-refuse-landlord-entry`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 3: `tmc:466-7`
- `dev-lawn-height` run 1: `tmc:629-11`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:918-23`
- `dev-park-bonfire` run 3: `tmc:608-11`
- `dev-amended-park-fine` run 3: `tmc:610:schedule-a:p1`
- `dev-amended-vendor-street` run 1: `tmc:740-2`
- `dev-amended-vendor-street` run 2: `tmc:740-2`

## Contradicted key facts (answer correct 0 for that answer)

None.

## Judge spans not found word for word in the answer (check the verdict)

- `dev-fireworks-backyard` run 2 fact 1 (present): “only on Victoria Day or Canada Day... Victoria Day and Canada Day discharges must end by 11:00 p.m.”
- `dev-fireworks-backyard` run 3 fact 1 (present): “Consumer fireworks may only be discharged in the City on Victoria Day or Canada Day... never after 11:00 p.m. [2]. You may also discharge them on another day under a special occasions fireworks discharge permit issued by the Fire Chief”

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
