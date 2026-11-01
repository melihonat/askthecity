# 2026-11-01-hybrid-130354

Rung `hybrid` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `e818f4d` · deployed `e818f4d` · snapshot `2026-10-28-30ada68a` · prompt `default-9` (90d2a516850e) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 15 | 0.00 |
| full@20 | 1.00 | 15 | 0.00 |
| hit@ctx | 0.87 | 15 | 0.00 |
| full@ctx | 0.80 | 15 | 0.00 |
| cite_precision | 0.76 | 12 | 0.03 |
| cite_full | 0.74 | 12 | 0.14 |
| coverage | 0.98 | 13 | 0.07 |
| answer_correct | 0.79 | 13 | 0.17 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.20 | 17 | 0.06 |
| passages_p50 | 377 ms | 72 | 58 ms |
| total_p50 | 1,793 ms | 41 | 204 ms |
| total_p95 | 2,638 ms | 41 | 684 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.12 on the judge's own key.

Gateway spend (tag `eval:2026-11-01-hybrid-130354`): $0.0557 over 146 requests
Harness wall-clock p50: 1,930 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `amended-manganese-limit`
- `decisions-electricity-referred`
- `decisions-laneway-snow`
- `lookup-591-2-1`
- `lookup-709-3`
- `multi-dead-tree`
- `refuse-demerit-points`
- `refuse-laneway-setback`
- `refuse-parking-side`
- `rules-apartment-heat`
- `rules-car-idling`
- `rules-dogs-limit`
- `rules-drone-park`
- `rules-yard-sales`

## Stale gold (dropped from retrieval and citation columns)

- `multi-dead-tree`: bl:402-2026:cl1*
- `amended-manganese-limit`: bl:470-2026:cl1

## Unstable questions (outcome differed across runs)

- `multi-reno-hours-idling`: answer → refusal:model_declined → refusal:model_declined
- `rules-drone-park`: refusal:model_declined → refusal:model_declined → answer

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `rules-sidewalk-snow` run 1: `sr:260413:comments:1`
- `rules-sidewalk-snow` run 1: `sr:261102:comments:1`
- `rules-sidewalk-snow` run 2: `sr:260413:comments:1`
- `rules-sidewalk-snow` run 3: `sr:260413:comments:1`
- `rules-dogs-limit` run 1: `tmc:608-34.1`
- `rules-dogs-limit` run 2: `tmc:608-34.1`
- `rules-dogs-limit` run 2: `tmc:349-12.1`
- `rules-dogs-limit` run 3: `tmc:608-34.1`
- `rules-dogs-limit` run 3: `tmc:349-12.1`
- `decisions-electricity-referred` run 1: `sr:260642:summary:2`
- `decisions-electricity-referred` run 1: `sr:285809:decision-history`
- `decisions-electricity-referred` run 2: `sr:260642:summary:2`
- `decisions-electricity-referred` run 2: `sr:285809:decision-history`
- `decisions-electricity-referred` run 3: `sr:285809:decision-history`
- `decisions-electricity-referred` run 3: `sr:260642:summary:2`
- `decisions-tree-size` run 1: `sr:284390:comments:12`
- `decisions-tree-size` run 1: `sr:284390:comments:15`
- `decisions-tree-size` run 2: `sr:284390:comments:12`
- `decisions-tree-size` run 3: `sr:284390:comments:12`
- `decisions-tree-size` run 3: `sr:284390:summary:2`
- `decisions-tree-size` run 3: `sr:284390:comments:15`

## Contradicted key facts (answer correct 0 for that answer)

- `rules-saturday-drilling` run 2 fact 1: “drilling that is clearly audible at that time would not be prohibited by that provision”
- `rules-saturday-drilling` run 3 fact 1: “drilling at 7:30 a.m. on a Saturday, if clearly audible, would fall within the 7 a.m. to 9 a.m. Saturday window, which the rule does not restrict”
- `amended-manganese-limit` run 3 fact 2: “replacing the former 0.05 mg/L [4]. The by-law was adopted by City Council on May 21, 2026”
- `decisions-electricity-referred` run 2 fact 1: “City Council received for information the Advanced Plan for Community emission sources and directed staff to report back”
- `decisions-tree-size` run 3 fact 2: “a detailed analysis to be reported back in 2027”

## Judge spans not found word for word in the answer (check the verdict)

None.

## Refusal reasons

- Answer questions refused: model_declined × 10
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

- `lookup-591-2-1`
- `lookup-709-3`
