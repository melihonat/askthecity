# 2026-11-01-side-quoted-dev-012701

Rung `side-quoted` · split `dev` · 3 runs · https://ask-the-city.vercel.app  
Git `063fef1` (dirty) · deployed `063fef1` · snapshot `2026-10-28-30ada68a` · prompt `quoted-1` (438c5178fab7) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 6 | 0.00 |
| full@20 | 1.00 | 6 | 0.00 |
| hit@ctx | 1.00 | 6 | 0.00 |
| full@ctx | 1.00 | 6 | 0.00 |
| cite_precision | 0.76 | 6 | 0.12 |
| cite_full | 1.00 | 6 | 0.00 |
| coverage | 0.93 | 6 | 0.06 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.00 | 6 | 0.00 |
| passages_p50 | 518 ms | 33 | 42 ms |
| total_p50 | 2,586 ms | 18 | 255 ms |
| total_p95 | 5,778 ms | 18 | 2,711 ms |

Answer correctness (judge) is not scored yet.

Gateway spend (tag `eval:2026-11-01-side-quoted-dev-012701`): $0.0332 over 83 requests
Harness wall-clock p50: 2,610 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-fireworks-backyard`
- `dev-refuse-landlord-entry`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 1: `tmc:466-7`
- `dev-fireworks-backyard` run 2: `tmc:466-7`
- `dev-lawn-height` run 1: `tmc:629-11`
- `dev-lawn-height` run 1: `tmc:489-3.3`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-park-bonfire` run 1: `tmc:608-11`
- `dev-park-bonfire` run 2: `tmc:608-1:park`
- `dev-park-bonfire` run 2: `tmc:608-11`
- `dev-park-bonfire` run 2: `tmc:608-1:sign`
- `dev-park-bonfire` run 3: `tmc:608-1:park`

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
