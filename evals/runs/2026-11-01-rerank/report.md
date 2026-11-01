# 2026-11-01-rerank-130730

Rung `rerank` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `e818f4d` · deployed `e818f4d` · snapshot `2026-10-28-30ada68a` · prompt `default-9` (90d2a516850e) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 15 | 0.00 |
| full@20 | 1.00 | 15 | 0.00 |
| hit@ctx | 1.00 | 15 | 0.00 |
| full@ctx | 1.00 | 15 | 0.00 |
| cite_precision | 0.76 | 15 | 0.05 |
| cite_full | 1.00 | 15 | 0.00 |
| coverage | 0.98 | 17 | 0.05 |
| answer_correct | 0.86 | 17 | 0.06 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.00 | 17 | 0.00 |
| passages_p50 | 597 ms | 72 | 42 ms |
| total_p50 | 2,115 ms | 51 | 63 ms |
| total_p95 | 2,877 ms | 51 | 639 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.16 on the judge's own key.

Gateway spend (tag `eval:2026-11-01-rerank-130730`): $0.0902 over 219 requests
Harness wall-clock p50: 2,335 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `amended-manganese-limit`
- `decisions-electricity-referred`
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
- `rules-sidewalk-snow` run 1: `sr:260413:comments:1`
- `rules-sidewalk-snow` run 1: `sr:261102:comments:1`
- `rules-dogs-limit` run 1: `tmc:608-34.1`
- `rules-dogs-limit` run 2: `tmc:608-34.1`
- `rules-dogs-limit` run 3: `tmc:349-12.1`
- `rules-dogs-limit` run 3: `tmc:608-34.1`
- `multi-reno-hours-idling` run 1: `tmc:519:schedule-a:1`
- `amended-summer-cooling` run 1: `tmc:629-38`
- `amended-summer-cooling` run 2: `tmc:629-38`
- `amended-summer-cooling` run 2: `bl:1512-2025:629-4.25`
- `amended-summer-cooling` run 3: `bl:1512-2025:629-4.25`
- `amended-summer-cooling` run 3: `tmc:629-38`
- `decisions-electricity-referred` run 2: `sr:285809:decision-history`
- `decisions-tree-size` run 1: `sr:284390:comments:12`
- `decisions-tree-size` run 2: `sr:284390:comments:12`
- `decisions-tree-size` run 3: `sr:284390:comments:12`
- `decisions-laneway-snow` run 1: `sr:286719:comments:12`
- `decisions-laneway-snow` run 2: `sr:286719:comments:12`
- `decisions-laneway-snow` run 3: `sr:286719:comments:12`

## Contradicted key facts (answer correct 0 for that answer)

- `rules-saturday-drilling` run 1 fact 1: “starting at 7:30 a.m. on a Saturday is permitted under that rule”
- `rules-saturday-drilling` run 2 fact 1: “7:30 a.m. on a Saturday falls within the Saturday exemption window and is not prohibited by that rule”
- `amended-summer-cooling` run 2 fact 3: “a by-law (1512-2025) replacing Chapter 629 takes effect on 2027-05-01”
- `amended-summer-cooling` run 3 fact 3: “The current consolidated text of the same requirement is in the Chapter 629 section, which is being replaced by By-law 1512-2025 on 2027-05-01”

## Judge spans not found word for word in the answer (check the verdict)

None.

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

- `lookup-591-2-1`
- `lookup-709-3`
