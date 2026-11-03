# 2026-11-02-shipped-3-215817

Rung `shipped-3` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `c186da4` · deployed `c186da4` · snapshot `2026-10-28-30ada68a` · prompt `fix-5` (3c8fbfd1b525) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 15 | 0.00 |
| full@20 | 1.00 | 15 | 0.00 |
| hit@ctx | 1.00 | 15 | 0.00 |
| full@ctx | 1.00 | 15 | 0.00 |
| cite_precision | 1.00 | 15 | 0.00 |
| cite_full | 0.93 | 15 | 0.00 |
| coverage | 0.97 | 17 | 0.02 |
| answer_correct | 0.94 | 17 | 0.03 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.00 | 17 | 0.00 |
| passages_p50 | 600 ms | 72 | 71 ms |
| total_p50 | 2,686 ms | 51 | 304 ms |
| total_p95 | 4,215 ms | 51 | 567 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.15 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-shipped-3-215817`): $1.0708 over 219 requests
Harness wall-clock p50: 2,852 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `amended-manganese-limit`
- `decisions-electricity-referred`
- `decisions-tree-size`
- `multi-dead-tree`
- `refuse-after-snapshot`
- `refuse-demerit-points`
- `refuse-laneway-setback`
- `refuse-parking-side`
- `refuse-rent-increase`
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

None.

## Judge spans not found word for word in the answer (check the verdict)

- `multi-dead-tree` run 3 fact 2 (present): “a permit is not required to remove a dead ... tree, but it must be certified as such by the Executive Director”

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

- `lookup-591-2-1`
- `lookup-709-3`
