# 2026-11-01-shipped-audit-224526

Rung `shipped` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `42abe4e` · deployed `a2ca877` · snapshot `2026-10-28-30ada68a` · prompt `default-9` (90d2a516850e) · threshold 0.359

> **The deployed SHA differs from the local one:** this run measures the deployed code.

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 15 | 0.00 |
| full@20 | 1.00 | 15 | 0.00 |
| hit@ctx | 1.00 | 15 | 0.00 |
| full@ctx | 1.00 | 15 | 0.00 |
| cite_precision | 0.99 | 15 | 0.02 |
| cite_full | 0.96 | 15 | 0.07 |
| coverage | 0.97 | 17 | 0.08 |
| answer_correct | 0.91 | 17 | 0.09 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.00 | 17 | 0.00 |
| passages_p50 | 584 ms | 72 | 105 ms |
| total_p50 | 2,371 ms | 51 | 329 ms |
| total_p95 | 4,024 ms | 51 | 1,377 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.16 on the judge's own key.

Gateway spend (tag `eval:2026-11-01-shipped-audit-224526`): $0.0951 over 222 requests
Harness wall-clock p50: 2,494 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `amended-manganese-limit`
- `decisions-laneway-snow`
- `decisions-tree-size`
- `lookup-709-3`
- `refuse-demerit-points`
- `refuse-laneway-setback`
- `refuse-rent-increase`
- `rules-apartment-heat`
- `rules-dogs-limit`
- `rules-drone-park`
- `rules-yard-sales`

## Stale gold (dropped from retrieval and citation columns)

- `multi-dead-tree`: bl:402-2026:cl1*
- `amended-manganese-limit`: bl:470-2026:cl1

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `rules-sidewalk-snow` run 1: `tmc:719-3`
- `rules-dogs-limit` run 3: `bl:1105-2025:cl1:G-J`

## Contradicted key facts (answer correct 0 for that answer)

- `amended-manganese-limit` run 3 fact 2: “The passages do not state the exact in-force date of the amendment, so confirm the current effective date with Toronto Water.”

## Judge spans not found word for word in the answer (check the verdict)

- `decisions-ebikes` run 1 fact 1 (present): “supports the proposed two-class definition for power-assisted bicycles (e-bikes): speed limited to 32 km/h, 500 watts or less, functional hand cranks or pedals, no footrest or platform, adjustable saddle, minimum operator age of 16, passengers allowed in a seat, and helmets required for all operators”

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

- `lookup-591-2-1`
- `lookup-709-3`
