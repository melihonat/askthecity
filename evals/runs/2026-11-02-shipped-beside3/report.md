# 2026-11-02-shipped-beside3-220317

Rung `shipped` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `c186da4` · deployed `c186da4` · snapshot `2026-10-28-30ada68a` · prompt `default-9` (90d2a516850e) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 15 | 0.00 |
| full@20 | 1.00 | 15 | 0.00 |
| hit@ctx | 1.00 | 15 | 0.00 |
| full@ctx | 1.00 | 15 | 0.00 |
| cite_precision | 1.00 | 15 | 0.00 |
| cite_full | 0.98 | 15 | 0.07 |
| coverage | 0.97 | 17 | 0.04 |
| answer_correct | 0.89 | 17 | 0.06 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.00 | 17 | 0.00 |
| passages_p50 | 568 ms | 72 | 38 ms |
| total_p50 | 2,421 ms | 51 | 82 ms |
| total_p95 | 3,171 ms | 51 | 851 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.16 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-shipped-beside3-220317`): $0.0933 over 219 requests
Harness wall-clock p50: 2,548 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `amended-manganese-limit`
- `decisions-electricity-referred`
- `decisions-tree-size`
- `lookup-591-2-1`
- `lookup-709-3`
- `multi-dead-tree`
- `refuse-after-snapshot`
- `refuse-demerit-points`
- `refuse-laneway-setback`
- `refuse-parking-side`
- `refuse-rent-increase`
- `rules-apartment-heat`
- `rules-car-idling`
- `rules-dogs-limit`
- `rules-drone-park`
- `rules-yard-sales`

## Stale gold (dropped from retrieval and citation columns)

- `multi-dead-tree`: bl:402-2026:cl1*
- `amended-manganese-limit`: bl:470-2026:cl1

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

None.

## Contradicted key facts (answer correct 0 for that answer)

- `rules-saturday-drilling` run 2 fact 1: “So drilling at 7:30 a.m. on a Saturday is not restricted by that rule, since it runs until 9 a.m. on Saturdays”
- `amended-summer-cooling` run 1 fact 3: “The current rule for air-conditioning operation is in § 629-38F, but By-law 67-2026 deletes that subsection, effective 2026-06-01”

## Judge spans not found word for word in the answer (check the verdict)

None.

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

- `lookup-591-2-1`
- `lookup-709-3`
