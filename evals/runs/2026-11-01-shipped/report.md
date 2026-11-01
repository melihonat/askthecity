# 2026-11-01-shipped-123940

Rung `shipped` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `d8d00af` · deployed `d8d00af` · snapshot `2026-10-28-30ada68a` · prompt `default-9` (90d2a516850e) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 15 | 0.00 |
| full@20 | 1.00 | 15 | 0.00 |
| hit@ctx | 1.00 | 15 | 0.00 |
| full@ctx | 1.00 | 15 | 0.00 |
| cite_precision | 0.69 | 15 | 0.06 |
| cite_full | 1.00 | 15 | 0.00 |
| coverage | 0.97 | 17 | 0.02 |
| answer_correct | 0.90 | 17 | 0.14 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.00 | 17 | 0.00 |
| passages_p50 | 592 ms | 72 | 40 ms |
| total_p50 | 2,327 ms | 51 | 250 ms |
| total_p95 | 2,883 ms | 51 | 148 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.16 on the judge's own key.

Gateway spend (tag `eval:2026-11-01-shipped-123940`): $0.0967 over 225 requests
Harness wall-clock p50: 2,546 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `amended-manganese-limit`
- `decisions-electricity-referred`
- `decisions-tree-size`
- `lookup-591-2-1`
- `multi-dead-tree`
- `refuse-after-snapshot`
- `refuse-demerit-points`
- `refuse-parking-side`
- `rules-apartment-heat`
- `rules-car-idling`
- `rules-dogs-limit`
- `rules-drone-park`

## Stale gold (dropped from retrieval and citation columns)

- `multi-dead-tree`: bl:402-2026:cl1*
- `amended-manganese-limit`: bl:470-2026:cl1

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `rules-saturday-drilling` run 2: `tmc:519:schedule-a:1`
- `rules-saturday-drilling` run 3: `tmc:519:schedule-a:1`
- `rules-apartment-heat` run 1: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 2: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 2: `bl:1512-2025:629-1.1:basement`
- `rules-apartment-heat` run 3: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 3: `tmc:629-38`
- `rules-sidewalk-snow` run 1: `tmc:719-4.1`
- `rules-sidewalk-snow` run 2: `tmc:719-4.1`
- `rules-car-idling` run 3: `tmc:591-2.5`
- `rules-dogs-limit` run 1: `tmc:349-12.1`
- `rules-dogs-limit` run 1: `tmc:608-34.1`
- `rules-dogs-limit` run 2: `tmc:349-1:animal`
- `rules-dogs-limit` run 2: `tmc:349-1:guard-dog`
- `rules-dogs-limit` run 2: `tmc:608-34.1`
- `rules-dogs-limit` run 2: `tmc:349-12.1`
- `rules-dogs-limit` run 2: `tmc:349-11`
- `rules-dogs-limit` run 3: `tmc:349-12.1`
- `rules-dogs-limit` run 3: `tmc:608-34.1`
- `rules-dogs-limit` run 3: `tmc:349-11`
- `multi-reno-hours-idling` run 1: `tmc:519:schedule-a:1`
- `multi-reno-hours-idling` run 2: `tmc:519:schedule-a:1`
- `multi-reno-hours-idling` run 3: `tmc:591-1.1:ambient-sound-level`
- `multi-reno-hours-idling` run 3: `tmc:517-1`
- `multi-reno-hours-idling` run 3: `tmc:519:schedule-a:1`
- `lookup-591-2-1` run 1: `tmc:591-1.1:ambient-sound-level`
- `lookup-591-2-1` run 2: `tmc:591-1.1:ambient-sound-level`
- `lookup-591-2-1` run 3: `tmc:591-1.1:ambient-sound-level`
- `lookup-709-3` run 1: `tmc:709-1`
- `lookup-709-3` run 2: `tmc:709-1`
- `lookup-709-3` run 3: `tmc:709-1`
- `amended-summer-cooling` run 1: `tmc:629-38`
- `amended-summer-cooling` run 2: `tmc:629-38`
- `amended-summer-cooling` run 2: `bl:1512-2025:629-4.25`
- `amended-summer-cooling` run 3: `tmc:629-38`
- `decisions-tree-size` run 1: `sr:284390:comments:12`
- `decisions-laneway-snow` run 1: `sr:286719:comments:12`
- `decisions-laneway-snow` run 2: `sr:286719:comments:12`
- `decisions-laneway-snow` run 3: `sr:286719:comments:12`
- `decisions-laneway-snow` run 3: `ie:2026.IE27.15:committee`

## Contradicted key facts (answer correct 0 for that answer)

- `amended-summer-cooling` run 1 fact 3: “By-law 67-2026 deletes that subsection, in force 2026-06-01, so the requirement is removed from chapter 629 as of that date”

## Judge spans not found word for word in the answer (check the verdict)

- `amended-summer-cooling` run 1 fact 3 (contradicted): “By-law 67-2026 deletes that subsection, in force 2026-06-01, so the requirement is removed from chapter 629 as of that date”
- `decisions-electricity-referred` run 1 fact 1 (present): “referred the item to the Executive Director for consideration, with no decision on its recommendations”
- `decisions-laneway-snow` run 1 fact 2 (present): “no decision was made”

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

- `lookup-591-2-1`
- `lookup-709-3`
