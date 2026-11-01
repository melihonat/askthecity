# 2026-11-01-shipped-2-162450

Rung `shipped` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `a0e67b2` · deployed `a0e67b2` · snapshot `2026-10-28-30ada68a` · prompt `default-9` (90d2a516850e) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 15 | 0.00 |
| full@20 | 1.00 | 15 | 0.00 |
| hit@ctx | 1.00 | 15 | 0.00 |
| full@ctx | 1.00 | 15 | 0.00 |
| cite_precision | 0.79 | 15 | 0.08 |
| cite_full | 0.96 | 15 | 0.07 |
| coverage | 0.98 | 17 | 0.01 |
| answer_correct | 0.87 | 17 | 0.15 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.00 | 17 | 0.00 |
| passages_p50 | 575 ms | 72 | 96 ms |
| total_p50 | 2,225 ms | 51 | 290 ms |
| total_p95 | 2,995 ms | 51 | 1,063 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.16 on the judge's own key.

Gateway spend (tag `eval:2026-11-01-shipped-2-162450`): $0.0934 over 219 requests
Harness wall-clock p50: 2,423 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `decisions-tree-size`
- `lookup-591-2-1`
- `multi-dead-tree`
- `refuse-after-snapshot`
- `refuse-demerit-points`
- `refuse-laneway-setback`
- `refuse-parking-side`
- `refuse-rent-increase`
- `rules-car-idling`
- `rules-drone-park`
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
- `rules-apartment-heat` run 2: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 3: `bl:1512-2025:629-4.25`
- `rules-sidewalk-snow` run 3: `sr:260413:comments:1`
- `rules-sidewalk-snow` run 3: `sr:261102:comments:1`
- `rules-car-idling` run 3: `tmc:591-2.5`
- `rules-dogs-limit` run 1: `tmc:608-34.1`
- `rules-dogs-limit` run 1: `tmc:349-12.1`
- `rules-dogs-limit` run 2: `tmc:349-12.1`
- `rules-dogs-limit` run 2: `tmc:608-34.1`
- `rules-dogs-limit` run 3: `tmc:608-34.1`
- `rules-dogs-limit` run 3: `tmc:349-12.1`
- `multi-reno-hours-idling` run 1: `tmc:519:schedule-a:1`
- `multi-reno-hours-idling` run 2: `tmc:519:schedule-a:1`
- `multi-reno-hours-idling` run 3: `tmc:519:schedule-a:1`
- `amended-summer-cooling` run 1: `tmc:629-38`
- `amended-summer-cooling` run 2: `tmc:629-38`
- `amended-summer-cooling` run 2: `bl:1512-2025:629-4.25`
- `amended-summer-cooling` run 3: `tmc:629-38`
- `amended-summer-cooling` run 3: `bl:1512-2025:629-4.25`
- `decisions-tree-size` run 1: `sr:284390:comments:12`
- `decisions-tree-size` run 2: `sr:284390:comments:12`
- `decisions-tree-size` run 3: `sr:284390:comments:12`
- `decisions-laneway-snow` run 1: `sr:286719:comments:12`
- `decisions-laneway-snow` run 1: `ie:2026.IE27.15:committee`
- `decisions-laneway-snow` run 2: `sr:286719:comments:12`
- `decisions-laneway-snow` run 3: `sr:286719:comments:12`

## Contradicted key facts (answer correct 0 for that answer)

- `amended-manganese-limit` run 2 fact 2: “amended by By-law 470-2026 from the earlier 0.05 mg/L”
- `amended-summer-cooling` run 2 fact 3: “By-law 67-2026 deletes that subsection in force from 2026-06-01 [6], and the replacement Chapter 629 text takes effect 2027-05-01”
- `amended-summer-cooling` run 3 fact 3: “This rule is also reflected in the current Chapter 629 provision [3]”

## Judge spans not found word for word in the answer (check the verdict)

None.

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

- `lookup-591-2-1`
- `lookup-709-3`
