# 2026-11-02-shipped-2-fix3-203432

Rung `shipped-2` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `27ce4d1` · deployed `27ce4d1` · snapshot `2026-10-28-30ada68a` · prompt `fix-3` (5198b172b231) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 15 | 0.00 |
| full@20 | 1.00 | 15 | 0.00 |
| hit@ctx | 1.00 | 15 | 0.00 |
| full@ctx | 1.00 | 15 | 0.00 |
| cite_precision | 1.00 | 15 | 0.00 |
| cite_full | 0.91 | 15 | 0.07 |
| coverage | 0.99 | 17 | 0.02 |
| answer_correct | 0.89 | 17 | 0.12 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.00 | 17 | 0.00 |
| passages_p50 | 580 ms | 72 | 96 ms |
| total_p50 | 2,197 ms | 51 | 320 ms |
| total_p95 | 3,258 ms | 51 | 3,895 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.15 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-shipped-2-fix3-203432`): $0.0972 over 219 requests
Harness wall-clock p50: 2,307 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `amended-manganese-limit`
- `decisions-electricity-referred`
- `decisions-laneway-snow`
- `decisions-tree-size`
- `lookup-709-3`
- `multi-dead-tree`
- `refuse-after-snapshot`
- `refuse-demerit-points`
- `refuse-laneway-setback`
- `refuse-parking-side`
- `rules-apartment-heat`
- `rules-car-idling`
- `rules-dogs-limit`
- `rules-yard-sales`

## Stale gold (dropped from retrieval and citation columns)

- `multi-dead-tree`: bl:402-2026:cl1*
- `amended-manganese-limit`: bl:470-2026:cl1

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

None.

## Contradicted key facts (answer correct 0 for that answer)

- `amended-summer-cooling` run 1 fact 3: “the requirement that air-conditioning systems be operated June 1 to September 30 to keep indoor temperature at or below 26 degrees Celsius was deleted by By-law 67-2026, in force since 2026-06-01”
- `amended-summer-cooling` run 2 fact 3: “The current Chapter 629 rule on keeping a unit in good repair and working order still applies”

## Judge spans not found word for word in the answer (check the verdict)

- `rules-car-idling` run 3 fact 1 (present): “no more than one minute in any sixty-minute period”

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

- `lookup-591-2-1`
- `lookup-709-3`
