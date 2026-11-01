# 2026-11-01-rerank-123521

Rung `rerank` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `d8d00af` · deployed `d8d00af` · snapshot `2026-10-28-30ada68a` · prompt `default-9` (90d2a516850e) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 15 | 0.00 |
| full@20 | 1.00 | 15 | 0.00 |
| hit@ctx | 1.00 | 15 | 0.00 |
| full@ctx | 1.00 | 15 | 0.00 |
| cite_precision | 0.76 | 15 | 0.02 |
| cite_full | 1.00 | 15 | 0.00 |
| coverage | 0.97 | 17 | 0.05 |
| answer_correct | 0.83 | 17 | 0.14 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.00 | 17 | 0.00 |
| passages_p50 | 542 ms | 72 | 27 ms |
| total_p50 | 2,112 ms | 51 | 24 ms |
| total_p95 | 3,001 ms | 51 | 1,707 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.15 on the judge's own key.

Gateway spend (tag `eval:2026-11-01-rerank-123521`): $0.0901 over 219 requests
Harness wall-clock p50: 2,392 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `amended-manganese-limit`
- `decisions-electricity-referred`
- `lookup-591-2-1`
- `multi-dead-tree`
- `refuse-after-snapshot`
- `refuse-laneway-setback`
- `refuse-parking-side`
- `refuse-rent-increase`
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

- `rules-saturday-drilling` run 1: `tmc:519:schedule-a:1`
- `rules-saturday-drilling` run 2: `tmc:519:schedule-a:1`
- `rules-saturday-drilling` run 3: `tmc:519:schedule-a:1`
- `rules-apartment-heat` run 1: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 1: `tmc:629-38`
- `rules-apartment-heat` run 2: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 3: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 3: `tmc:629-38`
- `rules-sidewalk-snow` run 2: `sr:260413:comments:1`
- `rules-sidewalk-snow` run 2: `sr:261102:comments:1`
- `rules-dogs-limit` run 1: `tmc:608-34.1`
- `rules-dogs-limit` run 1: `tmc:349-12.1`
- `rules-dogs-limit` run 2: `tmc:608-34.1`
- `rules-dogs-limit` run 3: `tmc:349-12.1`
- `rules-dogs-limit` run 3: `tmc:608-34.1`
- `multi-reno-hours-idling` run 3: `tmc:519:schedule-a:1`
- `amended-summer-cooling` run 1: `tmc:629-38`
- `amended-summer-cooling` run 1: `bl:1512-2025:629-4.25`
- `amended-summer-cooling` run 2: `tmc:629-38`
- `amended-summer-cooling` run 2: `bl:1512-2025:629-4.25`
- `amended-summer-cooling` run 3: `bl:1512-2025:629-4.25`
- `decisions-tree-size` run 1: `sr:284390:comments:12`
- `decisions-tree-size` run 2: `sr:284390:comments:12`
- `decisions-tree-size` run 3: `sr:284390:comments:12`
- `decisions-laneway-snow` run 1: `sr:286719:comments:12`
- `decisions-laneway-snow` run 2: `sr:286719:comments:12`
- `decisions-laneway-snow` run 3: `sr:286719:comments:12`
- `decisions-laneway-snow` run 3: `ie:2026.IE27.15:committee`

## Contradicted key facts (answer correct 0 for that answer)

- `rules-saturday-drilling` run 3 fact 1: “Drilling at 7:30 a.m. on a Saturday is therefore not prohibited by that rule, since the Saturday exception runs until 9 a.m.”
- `amended-manganese-limit` run 1 fact 2: “adopted by City Council on May 21, 2026”
- `amended-summer-cooling` run 2 fact 3: “Chapter 629 section 629-38 is replaced on 2027-05-01 by By-law 1512-2025”
- `amended-summer-cooling` run 3 fact 3: “which starts 2027-05-01”
- `decisions-ebikes` run 1 fact 1: “minimum age 16”

## Judge spans not found word for word in the answer (check the verdict)

- `rules-car-idling` run 3 fact 1 (present): “no more than one minute in a sixty-minute period”
- `decisions-ebikes` run 1 fact 1 (contradicted): “minimum age 16”

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

- `lookup-591-2-1`
- `lookup-709-3`
