# 2026-11-02-shipped-2-dev-fix3-171213

Rung `shipped-2` · split `dev` · 3 runs · http://localhost:3124  
Git `dbc0e90` · deployed `unknown` · snapshot `2026-10-28-30ada68a` · prompt `fix-3` (5198b172b231) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 12 | 0.00 |
| full@20 | 0.92 | 12 | 0.00 |
| hit@ctx | 1.00 | 12 | 0.00 |
| full@ctx | 0.92 | 12 | 0.00 |
| cite_precision | 0.69 | 12 | 0.01 |
| cite_full | 0.78 | 12 | 0.08 |
| coverage | 0.98 | 12 | 0.04 |
| answer_correct | 0.86 | 12 | 0.08 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.00 | 12 | 0.00 |
| passages_p50 | 747 ms | 51 | 27 ms |
| total_p50 | 2,621 ms | 36 | 529 ms |
| total_p95 | 6,811 ms | 36 | 4,426 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.10 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-shipped-2-dev-fix3-171213`): $0.0604 over 150 requests
Harness wall-clock p50: 2,526 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-deleted-dealer-hours`
- `dev-exception-park-drinking`
- `dev-fireworks-backyard`
- `dev-leaf-blower`
- `dev-refuse-landlord-entry`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 1: `tmc:466-7`
- `dev-fireworks-backyard` run 2: `tmc:466-7`
- `dev-fireworks-backyard` run 3: `tmc:466-7`
- `dev-pool-permit` run 1: `tmc:681-11:T`
- `dev-pool-permit` run 1: `tmc:681-11:U-W`
- `dev-lawn-height` run 1: `tmc:629-11`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 2: `tmc:918-23`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:918-23`
- `dev-park-bonfire` run 1: `tmc:608-11`
- `dev-park-bonfire` run 2: `tmc:608-11`
- `dev-park-bonfire` run 3: `tmc:608-11`
- `dev-amended-park-fine` run 1: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 2: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 3: `tmc:610:schedule-a:p1`
- `dev-amended-vendor-street` run 2: `tmc:740-2`
- `dev-amended-vendor-street` run 3: `tmc:740-2`
- `dev-exception-park-drinking` run 1: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 2: `tmc:608:schedule-a`
- `dev-exception-park-drinking` run 3: `tmc:608:schedule-a`
- `dev-exception-park-night` run 1: `tmc:349-12.1`
- `dev-exception-park-night` run 1: `tmc:608-34`
- `dev-exception-park-night` run 2: `tmc:608-34`
- `dev-exception-park-night` run 2: `tmc:349-12.1`
- `dev-exception-park-night` run 3: `tmc:608-34`
- `dev-exception-park-night` run 3: `tmc:349-12.1`

## Contradicted key facts (answer correct 0 for that answer)

- `dev-deleted-dealer-hours` run 3 fact 1: “No. Under the Second-Hand Goods licence rules”

## Judge spans not found word for word in the answer (check the verdict)

- `dev-fireworks-backyard` run 2 fact 1 (present): “only be discharged in the City on Victoria Day or Canada Day...and not after 11:00 p.m. on those days”

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
