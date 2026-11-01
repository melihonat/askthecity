# 2026-11-01-side-quoted-132135

Rung `side-quoted` · split `test` · 3 runs · https://ask-the-city.vercel.app  
Git `e818f4d` · deployed `e818f4d` · snapshot `2026-10-28-30ada68a` · prompt `quoted-1` (438c5178fab7) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 15 | 0.00 |
| full@20 | 1.00 | 15 | 0.00 |
| hit@ctx | 1.00 | 15 | 0.00 |
| full@ctx | 1.00 | 15 | 0.00 |
| cite_precision | 0.81 | 14 | 0.04 |
| cite_full | 0.98 | 14 | 0.07 |
| coverage | 0.96 | 16 | 0.08 |
| answer_correct | 0.82 | 16 | 0.03 |
| refusal_recall | 1.00 | 7 | 0.00 |
| false_refusals | 0.06 | 17 | 0.00 |
| passages_p50 | 679 ms | 72 | 149 ms |
| total_p50 | 2,870 ms | 48 | 556 ms |
| total_p95 | 4,463 ms | 48 | 2,199 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.15 on the judge's own key.

Gateway spend (tag `eval:2026-11-01-side-quoted-132135`): $0.1002 over 219 requests
Harness wall-clock p50: 2,853 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `amended-manganese-limit`
- `decisions-electricity-referred`
- `decisions-laneway-snow`
- `decisions-tree-size`
- `lookup-591-2-1`
- `lookup-709-3`
- `multi-dead-tree`
- `refuse-after-snapshot`
- `refuse-demerit-points`
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

- `rules-saturday-drilling` run 2: `tmc:519:schedule-a:1`
- `rules-saturday-drilling` run 3: `tmc:519:schedule-a:1`
- `rules-apartment-heat` run 1: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 2: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 2: `tmc:629-38`
- `rules-apartment-heat` run 3: `bl:1512-2025:629-4.25`
- `rules-apartment-heat` run 3: `tmc:629-38`
- `rules-sidewalk-snow` run 2: `tmc:719-4.1`
- `rules-dogs-limit` run 1: `tmc:349-12.1`
- `rules-dogs-limit` run 1: `tmc:608-34.1`
- `rules-dogs-limit` run 1: `tmc:349-11`
- `rules-dogs-limit` run 2: `tmc:608-34.1`
- `rules-dogs-limit` run 2: `tmc:349-12.1`
- `rules-dogs-limit` run 2: `tmc:349-11`
- `rules-dogs-limit` run 3: `tmc:608-34.1`
- `rules-dogs-limit` run 3: `bl:1105-2025:cl1:G-J`
- `multi-reno-hours-idling` run 1: `tmc:519:schedule-a:1`
- `multi-reno-hours-idling` run 2: `tmc:519:schedule-a:1`
- `multi-reno-hours-idling` run 3: `tmc:519:schedule-a:1`
- `lookup-591-2-1` run 1: `tmc:591-2.10`
- `amended-summer-cooling` run 1: `bl:1512-2025:629-4.25`
- `amended-summer-cooling` run 2: `bl:1512-2025:629-4.25`
- `amended-summer-cooling` run 3: `tmc:629-38`
- `decisions-electricity-referred` run 1: `sr:285809:decision-history`

## Contradicted key facts (answer correct 0 for that answer)

- `rules-saturday-drilling` run 1 fact 1: “noisy construction starting at 7:30 a.m. on a Saturday is permitted under that rule”
- `rules-saturday-drilling` run 2 fact 1: “So on a Saturday, construction sound clearly audible from 7:30 a.m. is not prohibited by that rule.”
- `rules-saturday-drilling` run 3 fact 1: “So work on a Saturday at 7:30 a.m. is not barred by that rule”
- `amended-summer-cooling` run 1 fact 3: “By-law 67-2026 effective 2026-06-01”
- `amended-summer-cooling` run 2 fact 3: “the same requirement carries forward in Chapter 497 and in the replacement Chapter 629 provisions”

## Judge spans not found word for word in the answer (check the verdict)

- `rules-car-idling` run 2 fact 1 (present): “shall not cause or permit a vehicle to idle for more than one minute in a sixty-minute period”

## Refusal reasons

- Answer questions refused: model_declined × 3
- Refuse questions: model_declined × 21

## Pinned questions (a § number matched)

- `lookup-591-2-1`
- `lookup-709-3`
