# 2026-11-01-shipped-dev-3-005918

Rung `shipped` · split `dev` · 3 runs · https://ask-the-city.vercel.app  
Git `0a2ca35` · deployed `0a2ca35` · snapshot `2026-10-28-30ada68a` · prompt `default-9` (90d2a516850e) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 6 | 0.00 |
| full@20 | 1.00 | 6 | 0.00 |
| hit@ctx | 1.00 | 6 | 0.00 |
| full@ctx | 1.00 | 6 | 0.00 |
| cite_precision | 0.75 | 6 | 0.18 |
| cite_full | 1.00 | 6 | 0.00 |
| coverage | 0.95 | 6 | 0.08 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.00 | 6 | 0.00 |
| passages_p50 | 584 ms | 33 | 21 ms |
| total_p50 | 2,085 ms | 18 | 43 ms |
| total_p95 | 2,729 ms | 18 | 332 ms |

Answer correctness (judge) is not scored yet.

Gateway spend (tag `eval:2026-11-01-shipped-dev-3-005918`): $0.0316 over 84 requests
Harness wall-clock p50: 2,258 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-driverless-tickets`
- `dev-fireworks-backyard`
- `dev-leaf-blower`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 1: `tmc:466-7`
- `dev-fireworks-backyard` run 2: `tmc:466-7`
- `dev-fireworks-backyard` run 3: `tmc:466-7`
- `dev-pool-permit` run 1: `tmc:681-11:T`
- `dev-pool-permit` run 1: `tmc:681-11:U-W`
- `dev-lawn-height` run 1: `tmc:629-11`
- `dev-lawn-height` run 1: `bl:1512-2025:629-4.2`
- `dev-lawn-height` run 1: `bl:1512-2025:629-4.3`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:489-3.3`
- `dev-park-bonfire` run 1: `tmc:608-1:park`
- `dev-park-bonfire` run 2: `tmc:608-11`

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
