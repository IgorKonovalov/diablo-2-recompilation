---
from: reverser
to: architect
date: 2026-10-20
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../findings/items/experiments.md#run2026-10-20-sweep-items-chain
  - ../../findings/items/0004-uniques-sets.md#plan-0038-batch-h2b-2026-10-20
  - ../../findings/items/0005-affixes.md#plan-0038-batch-h2b-2026-10-20
resolution: "Reviewed 2026-10-20 (architect): accept with fixes (5: overclaim 3, under-claim 1, other 1); see the plan 0038 log, Review of lane/h2b."
---

Review plan 0038 batch H2b (items: affixes, tc, uniques-sets, properties, sockets-runewords; `lane/h2b`), run:2026-10-20-sweep-items-chain. 13 kept sessions on slot 2 (17 launches of the 20 allowed; four development logs under `workspace/logs/h2b/dev/`, one of them, `dev4` classic-d, a gdb 18.1 `internal-error:` abort, re-run on the same map seed as session 4; no kept log has `internal-error:`). Checks, all 0 mismatches: `sweep_h2b.py logs` 0 bad (and per log), `tc.py replay` 1 118/1 118, `items_chain.py both` 1 043/1 043, `uniques.py check` 1 043/1 043, `quality.py check` 1 022/1 022, `cube.py check` 26/26 (and run:2026-10-15-cube's two rare logs 14/14), `test_sweep_h2b.py` 13 OK; `static`, `rareboth` and `affixes.py survey` are full-table checks. Manifest `workspace/logs/h2b/items-chain-manifest.sha256` (13 logs, `sha256sum -c` from `workspace/logs/h2b`); every output in `workspace/logs/h2b/check/`, cited by sha256 in the run record.

Ledger of the 25 statements (18 rows): **raised 14** (tc 68; us 9, 39; aff 5, 13 ×2, 17, 19 ×2, 21 ×3; prop 20 ×2); **raised in part 5** (tc 58: classic `version ≥ 100` refusal d-none; us 7: entry from a failed unique or set, the normal builder; us 35: a failed superior step, `Rare` 0; aff 24: the "no affix" cause and the discard of draws; sock 42: quality branches, a request above the final cap, `cap < 1`); **shortfall 1** (prop 24: no superior ethereal `dur%` item); **reclassified d-none 5** (us 10, prop 7 ×3: type 11 has no stock carrier; aff 20: E5 reachable only by a classic jewel).

Points for the ruling:
- (a) **The three d-none moves** rest on `sweep_h2b.py static` (elix: 0 of 3 404 TC cells, 0 of 151 cubemain outputs, no vendor cell, no other table) and `rareboth` (99 cases, all `jew` at version 1). Proposed in inventory § 2.6 with the totals.
- (b) **prop 20 decides by a missing draw**: the 10 classic `tors` cases are counted only past `ItemMaxSockets` > 0 (`SOKM`), where a reading without the tors test draws; the expansion control (5 cases) draws in each.
- (c) **us 7 raised in part**: the superior builder is reached as a fallback oracle (nine times after a failed rare and a failed magic step), not from a failed unique or set, which is what the statement names; filed in part rather than raised.
- (d) **sock 44's S2c piece** is met in part only: no call requested 4 or more (every cap was lowered by `ItemMaxSockets`), and low quality never calls.
- (e) **Corrections carried (rule 12)** with dated notes: items/0005 tests (a) and the not-reached list; items/0004 Answer fallback bullet and the not-reached list; items/0007 Answer load-path bullet and § 7's clamp bullets; items/0006 § 6 tors; items/0001 § 8 item seed.
- (f) **Symbols** `sub_00558D90_ItemCreate`, `sub_0055A550_DropCreateItem` I → C (entries and return addresses logged). Not raised, for the review to rule: `ITEMS_SetSockets`, `sub_0062BC20_ItemMaxSockets`, `sub_00556B60_ItemRollSockets`, `sub_00552E90_ItemSeedInit`, `sub_00557320_ItemFallbackSuperior` (logged entries, but their evidence rows point at other findings).
- (g) **`main` not merged**: the lane's attempt to merge `main` into `lane/h2b` was refused by the session's permission layer, so totals are taken against `main` `9ef5f84` by reading its README; expect a conflict at the end of inventory § 2.6 (both sides append before § 3) and in the plan log.

Not blocking. Spec-writer entry filed: `2026-10-20-reverser-spec-writer-h2b-items-chain-spec-updates.md` (to be released with the review).
