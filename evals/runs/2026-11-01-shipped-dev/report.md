# 2026-11-01-shipped-dev-000003

Rung `shipped` · split `dev` · 3 runs · https://ask-the-city.vercel.app  
Git `64e61bb` · deployed `64e61bb` · snapshot `2026-10-28-30ada68a` · prompt `default-7` (0855e7b1f685) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 5 | 0.00 |
| full@20 | 1.00 | 5 | 0.00 |
| hit@ctx | 1.00 | 5 | 0.00 |
| full@ctx | 1.00 | 5 | 0.00 |
| cite_precision | 0.75 | 4 | 0.13 |
| cite_full | 1.00 | 4 | 0.00 |
| coverage | 0.98 | 4 | 0.05 |
| refusal_recall | 0.87 | 5 | 0.20 |
| false_refusals | 0.13 | 5 | 0.20 |
| passages_p50 | 661 ms | 30 | 212 ms |
| total_p50 | 2,532 ms | 15 | 506 ms |
| total_p95 | 3,510 ms | 15 | 694 ms |

Answer correctness (judge) is not scored yet.

Gateway spend (tag `eval:2026-11-01-shipped-dev-000003`): $0.0277 over 77 requests
Harness wall-clock p50: 2,510 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-driverless-tickets`
- `dev-fireworks-backyard`
- `dev-refuse-landlord-entry`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

- `dev-park-bonfire`: refusal:model_declined → answer → refusal:model_declined
- `dev-refuse-landlord-entry`: answer → answer → refusal:model_declined

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 2: `tmc:466-7`
- `dev-fireworks-backyard` run 3: `tmc:466-7`
- `dev-lawn-height` run 1: `tmc:629-11`
- `dev-lawn-height` run 1: `tmc:918-23`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:918-23`
- `dev-park-bonfire` run 2: `tmc:608-11`

## Refusal reasons

- Answer questions refused: model_declined × 2
- Refuse questions: model_declined × 7, answer × 2, below_threshold × 6

## Pinned questions (a § number matched)

None.
