# 2026-11-02-shipped-dev-default9-local-164556

Rung `shipped` · split `dev` · 3 runs · http://localhost:3124  
Git `a26b527` (dirty) · deployed `unknown` · snapshot `2026-10-28-30ada68a` · prompt `default-9` (90d2a516850e) · threshold 0.359

| Column | Value | n | Spread |
| --- | --- | --- | --- |
| recall@20 | 1.00 | 9 | 0.00 |
| full@20 | 0.89 | 9 | 0.00 |
| hit@ctx | 1.00 | 9 | 0.00 |
| full@ctx | 0.89 | 9 | 0.00 |
| cite_precision | 0.80 | 9 | 0.19 |
| cite_full | 0.89 | 9 | 0.00 |
| coverage | 1.00 | 9 | 0.00 |
| answer_correct | 0.81 | 9 | 0.22 |
| refusal_recall | 1.00 | 5 | 0.00 |
| false_refusals | 0.00 | 9 | 0.00 |
| passages_p50 | 703 ms | 42 | 58 ms |
| total_p50 | 2,718 ms | 27 | 111 ms |
| total_p95 | 3,761 ms | 27 | 5,003 ms |

Answer correct judged by `claude-sonnet-5`, prompt v1 (191341a6dcf3), ≈ $0.08 on the judge's own key.

Gateway spend (tag `eval:2026-11-02-shipped-dev-default9-local-164556`): $0.0476 over 123 requests
Harness wall-clock p50: 2,539 ms, from the machine that ran the harness (not the function region).

## Retrieval mismatch across runs (a bug, e.g. a non-deterministic tiebreak)

- `dev-amended-park-fine`
- `dev-deleted-holistic-fees`
- `dev-driverless-tickets`

## Stale gold (dropped from retrieval and citation columns)

None.

## Unstable questions (outcome differed across runs)

None.

## Citations outside required/acceptable (widen `acceptable` in a commit, or accept the miss)

- `dev-fireworks-backyard` run 1: `tmc:466-7`
- `dev-fireworks-backyard` run 3: `tmc:466-7`
- `dev-pool-permit` run 3: `tmc:681-11:T`
- `dev-pool-permit` run 3: `tmc:681-11:U-W`
- `dev-lawn-height` run 1: `tmc:629-11`
- `dev-lawn-height` run 2: `tmc:629-11`
- `dev-lawn-height` run 3: `tmc:629-11`
- `dev-lawn-height` run 3: `bl:1512-2025:629-4.2`
- `dev-lawn-height` run 3: `bl:1512-2025:629-4.3`
- `dev-park-bonfire` run 1: `tmc:608-11`
- `dev-park-bonfire` run 3: `tmc:608-11`
- `dev-leaf-blower` run 1: `tmc:591-2.1`
- `dev-leaf-blower` run 1: `tmc:591-2.8`
- `dev-amended-park-fine` run 2: `tmc:610:schedule-a:p1`
- `dev-amended-park-fine` run 3: `tmc:610:schedule-a:p1`
- `dev-amended-vendor-street` run 3: `tmc:740-2`

## Contradicted key facts (answer correct 0 for that answer)

- `dev-deleted-holistic-fees` run 1 fact 1: “Yes. Every owner must file with the Municipal Licensing and Standards Division a list of all services offered and their fees”
- `dev-deleted-holistic-fees` run 3 fact 1: “Yes. Every owner must file with the Municipal Licensing and Standards Division a list of all services offered at the holistic centre and the fees charged”

## Judge spans not found word for word in the answer (check the verdict)

- `dev-fireworks-backyard` run 1 fact 1 (present): “Consumer fireworks may be discharged in the City only on Victoria Day or Canada Day, or on a day covered by a special occasions fireworks discharge permit issued by the Fire Chief [2]. ... On Victoria Day or Canada Day, discharge is not allowed after 11:00 p.m. [2].”
- `dev-fireworks-backyard` run 2 fact 1 (present): “Consumer fireworks may be discharged in the City only on Victoria Day or Canada Day, or on a day covered by a special occasions fireworks discharge permit issued by the Fire Chief [2]...On Victoria Day or Canada Day, discharge is not allowed after 11:00 p.m. [2]”

## Refusal reasons

- Answer questions refused: none
- Refuse questions: model_declined × 9, below_threshold × 6

## Pinned questions (a § number matched)

None.
