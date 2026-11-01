# 2026-11-01-shipped-dev-2-002111

Rung `shipped` · split `dev` · 3 runs · https://ask-the-city.vercel.app  
Git `0b9edd8` · deployed `be00d85` · snapshot `2026-10-28-30ada68a` · prompt `default-8` (d4b5db849efd) · threshold 0.359

> **The deployed SHA differs from the local one:** this run measures the deployed code.

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 5 | 0.00 |
| full@20 | 1.00 | 5 | 0.00 |
| hit@ctx | 1.00 | 5 | 0.00 |
| full@ctx | 1.00 | 5 | 0.00 |
| cite_precision | 0.78 | 5 | 0.13 |
| cite_full | 1.00 | 5 | 0.00 |
| coverage | 0.93 | 5 | 0.10 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.00 | 5 | 0.00 |
| passages_p50 | 584 ms | 30 | 497 ms |
| total_p50 | 1,988 ms | 15 | 209 ms |
| total_p95 | 3,419 ms | 15 | 1,158 ms |

Answer correctness (judge) is not scored yet.

Gateway spend (tag `eval:2026-11-01-shipped-dev-2-002111`): $0.0265 over 74 requests
Harness wall-clock p50: 2,085 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-driverless-tickets`
- `dev-fireworks-backyard`
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
- `dev-lawn-height` run 3: `tmc:918-23`
- `dev-lawn-height` run 3: `tmc:489-3.3`
- `dev-park-bonfire` run 1: `tmc:608-11`

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
