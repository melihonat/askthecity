# 2026-11-01-shipped-2-fix-162935

Rung `shipped-2` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `a0e67b2` · deployed `a0e67b2` · snapshot `2026-10-28-30ada68a` · prompt `fix-1` (09db545cdcc2) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 15 | 0.00 |
| full@20 | 1.00 | 15 | 0.00 |
| hit@ctx | 1.00 | 15 | 0.00 |
| full@ctx | 1.00 | 15 | 0.00 |
| cite_precision | 0.85 | 15 | 0.03 |
| cite_full | 0.93 | 15 | 0.00 |
| coverage | 0.99 | 17 | 0.03 |
| answer_correct | 0.90 | 17 | 0.11 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.00 | 17 | 0.00 |
| passages_p50 | 545 ms | 72 | 200 ms |
| total_p50 | 1,978 ms | 51 | 613 ms |
| total_p95 | 2,713 ms | 51 | 1,286 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.15 on the judge's own key.

Gateway spend (tag `eval:2026-11-01-shipped-2-fix-162935`): $0.0949 over 219 requests
Harness wall-clock p50: 2,182 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `amended-manganese-limit`
- `decisions-laneway-snow`
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
- `rules-drone-park`

## Stale gold (dropped from retrieval and citation columns)

- `multi-dead-tree`: bl:402-2026:cl1*
- `amended-manganese-limit`: bl:470-2026:cl1

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `rules-saturday-drilling` run 1: `tmc:519:schedule-a:1`
- `rules-saturday-drilling` run 2: `tmc:519:schedule-a:1`
- `rules-saturday-drilling` run 3: `tmc:519:schedule-a:1`
- `rules-apartment-heat` run 1: `tmc:629-38`
- `rules-apartment-heat` run 1: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 2: `tmc:629-38`
- `rules-apartment-heat` run 3: `tmc:629-38`
- `rules-dogs-limit` run 1: `tmc:608-34.1`
- `rules-dogs-limit` run 2: `tmc:349-12.1`
- `rules-dogs-limit` run 2: `tmc:608-34.1`
- `rules-dogs-limit` run 3: `tmc:349-12.1`
- `rules-dogs-limit` run 3: `tmc:608-34.1`
- `amended-summer-cooling` run 2: `tmc:629-38`
- `decisions-laneway-snow` run 1: `sr:286719:comments:12`
- `decisions-laneway-snow` run 2: `sr:286719:comments:12`
- `decisions-laneway-snow` run 3: `sr:286719:comments:12`

## Contradicted key facts (answer correct 0 for that answer)

- `rules-saturday-drilling` run 1 fact 1: “starting at 7:30 on a Saturday is not restricted by that rule”
- `rules-saturday-drilling` run 3 fact 1: “drilling that starts at 7:30 on a Saturday is not barred by the noise bylaw”

## Judge spans not found word for word in the answer (check the verdict)

- `rules-car-idling` run 1 fact 1 (present): “no more than one minute in a sixty-minute period”

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

- `lookup-591-2-1`
- `lookup-709-3`
