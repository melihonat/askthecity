# 2026-11-01-dense-122752

Rung `dense` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `d8d00af` · deployed `d8d00af` · snapshot `2026-10-28-30ada68a` · prompt `default-9` (90d2a516850e) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 0.87 | 15 | 0.00 |
| full@20 | 0.87 | 15 | 0.00 |
| hit@ctx | 0.87 | 15 | 0.00 |
| full@ctx | 0.87 | 15 | 0.00 |
| cite_precision | 0.74 | 13 | 0.06 |
| cite_full | 1.00 | 13 | 0.00 |
| coverage | 0.99 | 15 | 0.03 |
| answer_correct | 0.82 | 15 | 0.03 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.12 | 17 | 0.00 |
| passages_p50 | 325 ms | 72 | 89 ms |
| total_p50 | 1,874 ms | 45 | 207 ms |
| total_p95 | 2,606 ms | 45 | 772 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.14 on the judge's own key.

Gateway spend (tag `eval:2026-11-01-dense-122752`): $0.0449 over 146 requests
Harness wall-clock p50: 2,052 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `amended-manganese-limit`
- `decisions-electricity-referred`
- `decisions-laneway-snow`
- `decisions-tree-size`
- `lookup-591-2-1`
- `multi-dead-tree`
- `multi-reno-hours-idling`
- `refuse-after-snapshot`
- `refuse-laneway-setback`
- `refuse-parking-side`
- `refuse-rent-increase`
- `rules-dogs-limit`
- `rules-drone-park`
- `rules-saturday-drilling`
- `rules-yard-sales`

## Stale gold (dropped from retrieval and citation columns)

- `multi-dead-tree`: bl:402-2026:cl1*
- `amended-manganese-limit`: bl:470-2026:cl1

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `rules-apartment-heat` run 1: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 1: `tmc:629-38`
- `rules-apartment-heat` run 2: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 3: `tmc:629-38`
- `rules-apartment-heat` run 3: `bl:1512-2025:629-4.25`
- `rules-sidewalk-snow` run 2: `sr:260413:comments:1`
- `rules-sidewalk-snow` run 2: `sr:261102:comments:1`
- `rules-sidewalk-snow` run 3: `sr:260413:comments:1`
- `rules-sidewalk-snow` run 3: `sr:261102:comments:1`
- `rules-dogs-limit` run 1: `tmc:608-34.1`
- `rules-dogs-limit` run 1: `tmc:349-12.1`
- `rules-dogs-limit` run 2: `tmc:608-34.1`
- `rules-dogs-limit` run 3: `tmc:349-12.1`
- `rules-dogs-limit` run 3: `tmc:608-34.1`
- `multi-reno-hours-idling` run 1: `tmc:591-2.6`
- `multi-reno-hours-idling` run 2: `tmc:591-2.6`
- `multi-reno-hours-idling` run 3: `tmc:591-2.6`
- `amended-summer-cooling` run 1: `tmc:629-38`
- `amended-summer-cooling` run 2: `tmc:629-38`
- `amended-summer-cooling` run 3: `tmc:629-38`
- `amended-summer-cooling` run 3: `bl:1512-2025:629-4.25`
- `decisions-electricity-referred` run 1: `sr:285809:decision-history`
- `decisions-tree-size` run 1: `sr:284390:comments:12`
- `decisions-tree-size` run 3: `sr:284390:comments:12`
- `decisions-laneway-snow` run 1: `sr:286719:comments:12`
- `decisions-laneway-snow` run 1: `ie:2026.IE27.15:committee`
- `decisions-laneway-snow` run 2: `sr:286719:comments:12`
- `decisions-laneway-snow` run 3: `sr:286719:comments:12`

## Contradicted key facts (answer correct 0 for that answer)

- `amended-summer-cooling` run 1 fact 3: “Chapter 629 also requires all air-conditioning systems to be operated June 1 to September 30”
- `amended-summer-cooling` run 2 fact 3: “The Chapter 629 rule that all air-conditioning systems must be operated June 1 to September 30 to keep indoor temperatures at or below 26 degrees Celsius is amended by By-law 1395-2024 and is in force”
- `amended-summer-cooling` run 3 fact 3: “Under the Chapter 629 provision, all air-conditioning systems must be operated June 1 to September 30”

## Judge spans not found word for word in the answer (check the verdict)

- `rules-car-idling` run 1 fact 1 (present): “not more than one minute in a sixty-minute period”
- `amended-manganese-limit` run 2 fact 2 (present): “By-law 470-2026 (in force since the 2026-05-21 consolidation)... replacing the former 0.05 mg/L limit”

## Refusal reasons

- Answer questions refused: model_declined × 6
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

None.
