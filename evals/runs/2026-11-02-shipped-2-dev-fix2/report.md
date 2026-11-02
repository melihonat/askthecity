# 2026-11-02-shipped-2-dev-fix2-170805

Rung `shipped-2` · split `dev` · 3 runs · http://localhost:3124  
Git `a8be0fc` · deployed `unknown` · snapshot `2026-10-28-30ada68a` · prompt `fix-2` (6dd18f5a0d13) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 12 | 0.00 |
| full@20 | 0.92 | 12 | 0.00 |
| hit@ctx | 1.00 | 12 | 0.00 |
| full@ctx | 0.92 | 12 | 0.00 |
| cite_precision | 0.75 | 10 | 0.10 |
| cite_full | 0.72 | 10 | 0.03 |
| coverage | 0.97 | 10 | 0.07 |
| answer_correct | 0.86 | 10 | 0.05 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.11 | 12 | 0.08 |
| passages_p50 | 721 ms | 51 | 78 ms |
| total_p50 | 2,375 ms | 32 | 234 ms |
| total_p95 | 3,084 ms | 32 | 224 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.09 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-shipped-2-dev-fix2-170805`): $0.0601 over 150 requests
Harness wall-clock p50: 2,307 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-amended-park-fine`
- `dev-deleted-holistic-fees`
- `dev-driverless-tickets`
- `dev-exception-park-drinking`
- `dev-fireworks-backyard`
- `dev-leaf-blower`
- `dev-refuse-landlord-entry`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

- `dev-exception-park-night`: refusal:model_declined → answer → answer

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 3: `tmc:466-7`
- `dev-lawn-height` run 1: `tmc:629-11`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-park-bonfire` run 1: `tmc:608-11`
- `dev-park-bonfire` run 2: `tmc:608-11`
- `dev-amended-park-fine` run 1: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 1: `tmc:813-29`
- `dev-amended-park-fine` run 3: `tmc:610:schedule-a:p1`
- `dev-amended-vendor-street` run 2: `tmc:740-2`
- `dev-amended-vendor-street` run 3: `tmc:740-2`
- `dev-exception-park-drinking` run 1: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 2: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 3: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 3: `tmc:608-9`
- `dev-exception-park-night` run 2: `tmc:608-34`
- `dev-exception-park-night` run 2: `tmc:349-12.1`
- `dev-exception-park-night` run 2: `bl:1482-2025:cl1:O-Y`
- `dev-exception-park-night` run 3: `tmc:608-34`
- `dev-exception-park-night` run 3: `tmc:349-12.1`

## Contradicted key facts (answer correct 0 for that answer)

None.

## Judge spans not found word for word in the answer (check the verdict)

- `dev-deleted-holistic-fees` run 2 fact 2 (present): “By-law 1108-2025 deleted § 545-181... that deletion has been in force since 2026-01-01”

## Refusal reasons

- Answer questions refused: model_declined × 4
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
