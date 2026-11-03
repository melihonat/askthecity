# 2026-11-02-shipped-2-dev-fix3-c-200248

Rung `shipped-2` · split `dev` · 3 runs · http://localhost:3124  
Git `90fb348` · deployed `unknown` · snapshot `2026-10-28-30ada68a` · prompt `fix-3` (5198b172b231) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 12 | 0.00 |
| full@20 | 0.92 | 12 | 0.00 |
| hit@ctx | 1.00 | 12 | 0.00 |
| full@ctx | 0.92 | 12 | 0.00 |
| cite_precision | 0.74 | 11 | 0.05 |
| cite_full | 0.83 | 11 | 0.02 |
| coverage | 0.95 | 11 | 0.03 |
| answer_correct | 0.91 | 11 | 0.04 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.03 | 12 | 0.08 |
| passages_p50 | 729 ms | 51 | 34 ms |
| total_p50 | 2,521 ms | 35 | 265 ms |
| total_p95 | 4,680 ms | 35 | 1,898 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.10 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-shipped-2-dev-fix3-c-200248`): $0.0605 over 150 requests
Harness wall-clock p50: 2,255 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-amended-park-fine`
- `dev-deleted-dealer-hours`
- `dev-driverless-tickets`
- `dev-exception-park-drinking`
- `dev-fireworks-backyard`
- `dev-leaf-blower`
- `dev-refuse-landlord-entry`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

- `dev-exception-park-night`: answer → answer → refusal:model_declined

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 1: `tmc:466-7`
- `dev-fireworks-backyard` run 2: `tmc:466-7`
- `dev-pool-permit` run 3: `tmc:681-11:T`
- `dev-pool-permit` run 3: `tmc:681-11:U-W`
- `dev-lawn-height` run 1: `tmc:629-11`
- `dev-lawn-height` run 1: `bl:1512-2025:629-4.2`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:918-23`
- `dev-park-bonfire` run 3: `tmc:608-11`
- `dev-amended-park-fine` run 1: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 2: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 3: `tmc:610:schedule-a:p1`
- `dev-amended-vendor-street` run 1: `tmc:740-2`
- `dev-amended-vendor-street` run 2: `tmc:740-2`
- `dev-exception-park-drinking` run 1: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 1: `tmc:608-9`
- `dev-exception-park-drinking` run 2: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 2: `tmc:608-9`
- `dev-exception-park-drinking` run 3: `tmc:608:schedule-a`
- `dev-exception-park-night` run 1: `tmc:608-34`
- `dev-exception-park-night` run 1: `tmc:349-12.1`
- `dev-exception-park-night` run 2: `tmc:608-34`

## Contradicted key facts (answer correct 0 for that answer)

None.

## Judge spans not found word for word in the answer (check the verdict)

- `dev-fireworks-backyard` run 2 fact 1 (present): “Consumer fireworks may only be discharged on Victoria Day or Canada Day... and not after 11:00 p.m. on those days”

## Refusal reasons

- Answer questions refused: model_declined × 1
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
