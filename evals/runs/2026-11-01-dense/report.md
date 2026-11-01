# 2026-11-01-dense-130002

Rung `dense` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `e818f4d` · deployed `e818f4d` · snapshot `2026-10-28-30ada68a` · prompt `default-9` (90d2a516850e) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 0.87 | 15 | 0.00 |
| full@20 | 0.87 | 15 | 0.00 |
| hit@ctx | 0.87 | 15 | 0.00 |
| full@ctx | 0.87 | 15 | 0.00 |
| cite_precision | 0.72 | 13 | 0.02 |
| cite_full | 1.00 | 13 | 0.00 |
| coverage | 0.99 | 15 | 0.02 |
| answer_correct | 0.81 | 15 | 0.06 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.12 | 17 | 0.00 |
| passages_p50 | 370 ms | 72 | 92 ms |
| total_p50 | 2,010 ms | 45 | 205 ms |
| total_p95 | 2,807 ms | 45 | 1,662 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.13 on the judge's own key.

Gateway spend (tag `eval:2026-11-01-dense-130002`): $0.0457 over 148 requests
Harness wall-clock p50: 2,090 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `decisions-electricity-referred`
- `decisions-laneway-snow`
- `decisions-tree-size`
- `lookup-591-2-1`
- `lookup-709-3`
- `multi-reno-hours-idling`
- `refuse-laneway-setback`
- `refuse-parking-side`
- `refuse-rent-increase`
- `refuse-tax-rate`
- `rules-apartment-heat`
- `rules-car-idling`
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

- `rules-saturday-drilling` run 1: `tmc:591-2.6`
- `rules-saturday-drilling` run 2: `tmc:591-2.6`
- `rules-apartment-heat` run 1: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 1: `tmc:629-38`
- `rules-apartment-heat` run 2: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 2: `tmc:629-38`
- `rules-apartment-heat` run 3: `tmc:629-38`
- `rules-apartment-heat` run 3: `bl:1512-2025:629-4.25`
- `rules-sidewalk-snow` run 2: `sr:260413:comments:1`
- `rules-sidewalk-snow` run 2: `sr:261102:comments:1`
- `rules-sidewalk-snow` run 3: `sr:260413:comments:1`
- `rules-sidewalk-snow` run 3: `sr:261102:comments:1`
- `rules-dogs-limit` run 1: `tmc:349-12.1`
- `rules-dogs-limit` run 1: `tmc:608-34.1`
- `rules-dogs-limit` run 2: `tmc:349-12.1`
- `rules-dogs-limit` run 2: `tmc:608-34.1`
- `rules-dogs-limit` run 3: `tmc:608-34.1`
- `rules-dogs-limit` run 3: `tmc:349-12.1`
- `multi-reno-hours-idling` run 1: `tmc:591-2.6`
- `multi-reno-hours-idling` run 2: `tmc:591-2.6`
- `multi-reno-hours-idling` run 3: `tmc:591-2.6`
- `amended-summer-cooling` run 1: `tmc:629-38`
- `amended-summer-cooling` run 2: `tmc:629-38`
- `amended-summer-cooling` run 3: `tmc:629-38`
- `decisions-tree-size` run 1: `sr:284390:comments:12`
- `decisions-tree-size` run 3: `sr:284390:comments:12`
- `decisions-laneway-snow` run 1: `sr:286719:comments:12`
- `decisions-laneway-snow` run 1: `ie:2026.IE27.15:committee`
- `decisions-laneway-snow` run 2: `sr:286719:comments:12`
- `decisions-laneway-snow` run 3: `sr:286719:comments:12`

## Contradicted key facts (answer correct 0 for that answer)

- `rules-saturday-drilling` run 2 fact 1: “drilling that is clearly audible at 7:30 a.m. on a Saturday falls outside the prohibited hours and is not barred by that rule”
- `amended-summer-cooling` run 1 fact 3: “Chapter 629 also requires all air-conditioning systems to be operated from June 1 to September 30 to maintain not more than 26 degrees Celsius, and this amended rule is already in force”
- `amended-summer-cooling` run 2 fact 3: “Chapter 629 likewise requires all air-conditioning systems to be operated from June 1 to September 30”
- `amended-summer-cooling` run 3 fact 3: “The same rule for air-conditioning systems appears in the Chapter 629 property standards [3]; a by-law amendment changed that section in 2024 [3].”

## Judge spans not found word for word in the answer (check the verdict)

- `rules-car-idling` run 1 fact 1 (present): “no more than one minute in a sixty-minute period”
- `rules-car-idling` run 3 fact 1 (present): “not cause or permit a vehicle to idle for more than one minute in a sixty-minute period”

## Refusal reasons

- Answer questions refused: model_declined × 6
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

None.
