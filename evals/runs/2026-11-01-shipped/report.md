# 2026-11-01-shipped-131142

Rung `shipped` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `e818f4d` · deployed `e818f4d` · snapshot `2026-10-28-30ada68a` · prompt `default-9` (90d2a516850e) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 15 | 0.00 |
| full@20 | 1.00 | 15 | 0.00 |
| hit@ctx | 1.00 | 15 | 0.00 |
| full@ctx | 1.00 | 15 | 0.00 |
| cite_precision | 0.80 | 15 | 0.05 |
| cite_full | 0.96 | 15 | 0.07 |
| coverage | 0.98 | 17 | 0.02 |
| answer_correct | 0.93 | 17 | 0.06 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.00 | 17 | 0.00 |
| passages_p50 | 575 ms | 72 | 97 ms |
| total_p50 | 2,213 ms | 51 | 673 ms |
| total_p95 | 4,387 ms | 51 | 5,704 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.16 on the judge's own key.

Gateway spend (tag `eval:2026-11-01-shipped-131142`): $0.0951 over 222 requests
Harness wall-clock p50: 2,346 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `amended-manganese-limit`
- `decisions-laneway-snow`
- `decisions-tree-size`
- `lookup-591-2-1`
- `lookup-709-3`
- `refuse-after-snapshot`
- `refuse-demerit-points`
- `refuse-parking-side`
- `refuse-rent-increase`
- `rules-apartment-heat`
- `rules-yard-sales`

## Stale gold (dropped from retrieval and citation columns)

- `multi-dead-tree`: bl:402-2026:cl1*
- `amended-manganese-limit`: bl:470-2026:cl1

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `rules-saturday-drilling` run 1: `tmc:519:schedule-a:1`
- `rules-saturday-drilling` run 2: `tmc:519:schedule-a:1`
- `rules-saturday-drilling` run 3: `tmc:519:schedule-a:1`
- `rules-apartment-heat` run 1: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 1: `tmc:629-38`
- `rules-apartment-heat` run 2: `tmc:629-38`
- `rules-apartment-heat` run 3: `bl:1512-2025:629-4.25`
- `rules-car-idling` run 2: `tmc:591-2.5`
- `rules-dogs-limit` run 1: `tmc:608-34.1`
- `rules-dogs-limit` run 1: `tmc:349-12.1`
- `rules-dogs-limit` run 1: `tmc:349-11`
- `rules-dogs-limit` run 2: `tmc:608-34.1`
- `rules-dogs-limit` run 2: `tmc:349-11`
- `rules-dogs-limit` run 3: `tmc:349-12.1`
- `rules-dogs-limit` run 3: `tmc:608-34.1`
- `rules-dogs-limit` run 3: `tmc:349-11`
- `multi-reno-hours-idling` run 1: `tmc:519:schedule-a:1`
- `multi-reno-hours-idling` run 2: `tmc:519:schedule-a:1`
- `multi-reno-hours-idling` run 3: `tmc:519:schedule-a:1`
- `amended-summer-cooling` run 1: `tmc:629-38`
- `amended-summer-cooling` run 1: `bl:1512-2025:629-4.25`
- `amended-summer-cooling` run 2: `tmc:629-38`
- `amended-summer-cooling` run 2: `bl:1512-2025:629-4.25`
- `amended-summer-cooling` run 3: `bl:1512-2025:629-4.25`
- `decisions-tree-size` run 3: `sr:284390:comments:12`
- `decisions-laneway-snow` run 1: `sr:286719:comments:12`
- `decisions-laneway-snow` run 2: `sr:286719:comments:12`
- `decisions-laneway-snow` run 2: `ie:2026.IE27.15:committee`
- `decisions-laneway-snow` run 3: `sr:286719:comments:12`

## Contradicted key facts (answer correct 0 for that answer)

None.

## Judge spans not found word for word in the answer (check the verdict)

- `rules-car-idling` run 1 fact 1 (present): “not cause or permit a vehicle to idle for more than one minute in a sixty-minute period”
- `rules-car-idling` run 3 fact 1 (present): “no more than one minute in a sixty-minute period”

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

- `lookup-591-2-1`
- `lookup-709-3`
