# 2026-11-02-side-sonnet-dev-fix5-214040

Rung `side-sonnet` · split `dev` · 3 runs · http://localhost:3124  
Git `1d86cd8` (dirty) · deployed `unknown` · snapshot `2026-10-28-30ada68a` · prompt `fix-5` (3c8fbfd1b525) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 13 | 0.00 |
| full@20 | 0.92 | 13 | 0.00 |
| hit@ctx | 1.00 | 13 | 0.00 |
| full@ctx | 0.92 | 13 | 0.00 |
| cite_precision | 0.89 | 13 | 0.09 |
| cite_full | 0.72 | 13 | 0.08 |
| coverage | 0.91 | 13 | 0.06 |
| answer_correct | 0.88 | 13 | 0.04 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.00 | 13 | 0.00 |
| passages_p50 | 686 ms | 54 | 153 ms |
| total_p50 | 2,770 ms | 39 | 66 ms |
| total_p95 | 3,636 ms | 39 | 426 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.12 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-side-sonnet-dev-fix5-214040`): $0.6745 over 159 requests
Harness wall-clock p50: 2,574 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-amended-park-fine`
- `dev-deleted-holistic-fees`
- `dev-fireworks-backyard`
- `dev-moved-pet-sources`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 1: `tmc:466-7`
- `dev-fireworks-backyard` run 2: `tmc:466-7`
- `dev-fireworks-backyard` run 2: `tmc:466-9`
- `dev-fireworks-backyard` run 3: `tmc:466-7`
- `dev-amended-park-fine` run 1: `tmc:610:schedule-a:p1`
- `dev-amended-vendor-street` run 2: `tmc:740-2`
- `dev-exception-park-drinking` run 1: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 2: `tmc:608:schedule-a`
- `dev-exception-park-night` run 1: `bl:1482-2025:cl1:O-Y`
- `dev-exception-park-night` run 3: `bl:1482-2025:cl1:O-Y`

## Contradicted key facts (answer correct 0 for that answer)

None.

## Judge spans not found word for word in the answer (check the verdict)

- `dev-deleted-holistic-fees` run 1 fact 2 (present): “By-law 1108-2025 deleted 
dsection 545-181... the deletion has been in force since 2026-01-01”

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
