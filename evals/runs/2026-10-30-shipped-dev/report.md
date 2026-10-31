# 2026-10-30-shipped-dev-221801

Rung `shipped` · split `dev` · 3 runs · https://ask-the-city.vercel.app  
Git `f5553f8` · deployed `f5553f8` · snapshot `2026-10-28-fcb37dce` · prompt `default-5` (c95eecdc87c9) · threshold 0.35

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 4 | 0.00 |
| full@20 | 1.00 | 4 | 0.00 |
| hit@ctx | 1.00 | 4 | 0.00 |
| full@ctx | 1.00 | 4 | 0.00 |
| cite_precision | 0.70 | 3 | 0.19 |
| cite_full | 1.00 | 3 | 0.00 |
| coverage | 1.00 | 3 | 0.00 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.40 | 5 | 0.00 |
| passages_p50 | 538 ms | 30 | 89 ms |
| total_p50 | 2,494 ms | 9 | 448 ms |
| total_p95 | 2,715 ms | 9 | 122 ms |

Answer correctness (judge) is not scored yet.

Gateway spend (tag `eval:2026-10-30-shipped-dev-221801`): $0.0251 over 72 requests
Harness wall-clock p50: 2,030 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-refuse-landlord-entry`
- `dev-refuse-leafs`

## Stale gold (dropped from retrieval and citation columns)

- `dev-driverless-tickets`: sr:287415:*

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 2: `tmc:466-7`
- `dev-lawn-height` run 1: `tmc:629-11`
- `dev-lawn-height` run 1: `tmc:918-23`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 2: `bl:1512-2025:629-4.2`
- `dev-lawn-height` run 2: `bl:1512-2025:629-4.3`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:918-23`
- `dev-lawn-height` run 3: `bl:1512-2025:629-4.2`
- `dev-lawn-height` run 3: `bl:1512-2025:629-4.3`

## Refusal reasons

- Answer questions refused: model_declined × 6
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
