# 2026-10-31-shipped-dev-231639

Rung `shipped` · split `dev` · 3 runs · https://ask-the-city.vercel.app  
Git `76e80b0` · deployed `76e80b0` · snapshot `2026-10-28-30ada68a` · prompt `default-7` (0855e7b1f685) · threshold 0.35

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 5 | 0.00 |
| full@20 | 1.00 | 5 | 0.00 |
| hit@ctx | 1.00 | 5 | 0.00 |
| full@ctx | 1.00 | 5 | 0.00 |
| cite_precision | 0.62 | 5 | 0.13 |
| cite_full | 1.00 | 5 | 0.00 |
| coverage | 0.96 | 5 | 0.11 |
| refusal_recall | 0.87 | 5 | 0.20 |
| false_refusals | 0.00 | 5 | 0.00 |
| passages_p50 | 559 ms | 30 | 190 ms |
| total_p50 | 2,054 ms | 17 | 209 ms |
| total_p95 | 2,700 ms | 17 | 199 ms |

Answer correctness (judge) is not scored yet.

Gateway spend (tag `eval:2026-10-31-shipped-dev-231639`): $0.0298 over 81 requests
Harness wall-clock p50: 2,256 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-driverless-tickets`
- `dev-fireworks-backyard`
- `dev-refuse-landlord-entry`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

- `dev-refuse-landlord-entry`: refusal:model_declined → answer → answer

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 1: `tmc:466-7`
- `dev-fireworks-backyard` run 2: `tmc:466-7`
- `dev-fireworks-backyard` run 3: `tmc:466-7`
- `dev-pool-permit` run 1: `tmc:681-11:T`
- `dev-pool-permit` run 1: `tmc:681-11:U-W`
- `dev-lawn-height` run 1: `tmc:629-11`
- `dev-lawn-height` run 1: `tmc:918-23`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 2: `tmc:918-23`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-park-bonfire` run 1: `tmc:608-5`
- `dev-park-bonfire` run 2: `tmc:608-11`
- `dev-park-bonfire` run 3: `tmc:608-5`
- `dev-park-bonfire` run 3: `tmc:608-11`

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 10, answer × 2, below_threshold × 3

## Pinned questions (a § number matched)

None.
