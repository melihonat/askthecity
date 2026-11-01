# 2026-11-01-hybrid-123137

Rung `hybrid` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `d8d00af` · deployed `d8d00af` · snapshot `2026-10-28-30ada68a` · prompt `default-9` (90d2a516850e) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 15 | 0.00 |
| full@20 | 1.00 | 15 | 0.00 |
| hit@ctx | 0.87 | 15 | 0.00 |
| full@ctx | 0.80 | 15 | 0.00 |
| cite_precision | 0.78 | 12 | 0.08 |
| cite_full | 0.74 | 12 | 0.08 |
| coverage | 0.99 | 12 | 0.04 |
| answer_correct | 0.77 | 12 | 0.29 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.22 | 17 | 0.12 |
| passages_p50 | 364 ms | 72 | 127 ms |
| total_p50 | 1,913 ms | 40 | 270 ms |
| total_p95 | 2,860 ms | 40 | 3,553 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.12 on the judge's own key.

Gateway spend (tag `eval:2026-11-01-hybrid-123137`): $0.0559 over 146 requests
Harness wall-clock p50: 2,096 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `amended-manganese-limit`
- `decisions-laneway-snow`
- `lookup-591-2-1`
- `lookup-709-3`
- `refuse-after-snapshot`
- `refuse-demerit-points`
- `refuse-laneway-setback`
- `refuse-parking-side`
- `refuse-rent-increase`
- `rules-apartment-heat`
- `rules-car-idling`
- `rules-dogs-limit`
- `rules-drone-park`

## Stale gold (dropped from retrieval and citation columns)

- `multi-dead-tree`: bl:402-2026:cl1*
- `amended-manganese-limit`: bl:470-2026:cl1

## Unstable questions (outcome differed across runs)

- `amended-manganese-limit`: answer → answer → refusal:model_declined
- `multi-reno-hours-idling`: answer → answer → refusal:model_declined

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `rules-sidewalk-snow` run 1: `sr:260413:comments:1`
- `rules-sidewalk-snow` run 2: `sr:260413:comments:1`
- `rules-sidewalk-snow` run 3: `sr:260413:comments:1`
- `rules-dogs-limit` run 1: `tmc:608-34.1`
- `rules-dogs-limit` run 1: `tmc:349-12.1`
- `rules-dogs-limit` run 2: `tmc:608-34.1`
- `rules-dogs-limit` run 2: `tmc:349-12.1`
- `rules-dogs-limit` run 3: `tmc:608-34.1`
- `rules-dogs-limit` run 3: `tmc:349-12.1`
- `decisions-electricity-referred` run 1: `sr:260642:summary:2`
- `decisions-electricity-referred` run 1: `sr:285809:decision-history`
- `decisions-electricity-referred` run 3: `sr:285809:decision-history`
- `decisions-tree-size` run 1: `sr:284390:comments:12`
- `decisions-tree-size` run 1: `sr:284390:comments:15`
- `decisions-tree-size` run 1: `sr:284390:summary:2`
- `decisions-tree-size` run 2: `sr:284390:comments:12`
- `decisions-tree-size` run 3: `sr:284390:comments:12`
- `decisions-tree-size` run 3: `sr:284390:summary:2`
- `decisions-tree-size` run 3: `sr:284390:comments:15`

## Contradicted key facts (answer correct 0 for that answer)

- `rules-saturday-drilling` run 2 fact 1: “So drilling at 7:30 a.m. on a Saturday is not prohibited by that section”
- `amended-manganese-limit` run 1 fact 2: “was raised from 0.05 mg/L to 2.0 mg/L by By-law 470-2026, adopted by City Council on 2026-05-21”
- `amended-manganese-limit` run 2 fact 2: “Council adopted this change on May 21, 2026, through By-law 470-2026”
- `decisions-tree-size` run 2 fact 1: “Staff recommended in principle reducing the Private Tree By-law threshold from 30 cm to 20 cm DBH”

## Judge spans not found word for word in the answer (check the verdict)

None.

## Refusal reasons

- Answer questions refused: model_declined × 11
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

- `lookup-591-2-1`
- `lookup-709-3`
