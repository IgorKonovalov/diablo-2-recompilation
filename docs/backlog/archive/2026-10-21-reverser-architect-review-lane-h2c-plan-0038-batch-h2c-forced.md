---
from: reverser
to: architect
date: 2026-10-21
status: done
context:
  - ../../plans/0038-inferred-claims-sweep.md#implementation-log
  - ../../findings/items/experiments.md#run2026-10-21-throw-forced
  - ../../findings/items/experiments.md#run2026-10-21-tcnamed-props-forced
  - ../../findings/items/0001-tc-resolution.md#plan-0038-batch-h2c-2026-10-21
  - ../../findings/items/0006-properties.md#plan-0038-batch-h2c-2026-10-21
resolution: "Reviewed 2026-10-21 (architect): accept with fixes (3: overclaim 1, under-claim 1, omission 1). Ledger stands: 4 raised, 2 raised in part, 1 shortfall; sub_00633680_ItemIndexByCode raised I to C at the review; totals unchanged (1 526). Plan 0038 log, review of lane/h2c."
---

Review plan 0038 batch H2c (forced; items/tc and items/properties; `lane/h2c`), run:2026-10-21-throw-forced and run:2026-10-21-tcnamed-props-forced. 12 launches on slot 2, 10 kept logs (2 dev logs, heph-a and heph-b, wrong waypoint row; no log has `internal-error:` or `LOGERR`). Each table is a loose `treasureclassex.bin` under `-direct` in its own game copy (variants A, B and tcn; hashes in `workspace/logs/h2c/h2c-tables.sha256`, `bindiff` with only the listed cells); the ADR-0013 read lists (items/0001 § 8, items/0006 § 4) were committed before any session (`fc6c7a6`) and re-taken with the final checker (`check-reads.txt`: 0 TC reads in every closure). Checks, all 0 mismatches: `sweep_h2c.py logs` 0 failed, `tc.py replay` 677/677, `items_chain.py both`, `uniques.py` and `props.py` 580/580, `quality.py` 1 496/1 496. Manifest `workspace/logs/h2c/h2c-manifest.sha256` (`sha256sum -c` from `workspace/logs/h2c`); outputs in `check/`, `h2c-check.sha256` (from `check/`), produced by `run-checks.sh` and re-run once with the same hashes.

Ledger of the 7 statements (6 rows): **raised 4** (tc 10 ×2, tc 55, prop 12 L390); **raised in part 2** (tc 56: the Long Sword half, `version ≥ 100` d-none per ruling 1; prop 14: func 23's make branch, the two skips not reached); **shortfall 1** (prop 15: no func-24 slot, Hephasto never met).

Points for the ruling:
- (a) **prop 14 filed in part, not raised** (the pause note proposed "raised"): all three func-23 entries took the make branch (not ethereal, `ItemHasDurability` 1), so the two skips are unseparated (review-fixes rule 8).
- (b) **tc 55's order claim** rests on 1 078 `THR` lines each right after the same item's `QOUT` with no `PICK` between, every one after a roll that stepped the seed, plus the replay's seed chain; the order test was added to `sweep_h2c.py` on the resume (no earlier revision's output is cited).
- (c) **"Classic only"** (tc 10, 55) rests on all `THR` lines carrying expansion flag 0 and the stock control (H2b's logs: 13 expansion creations of throwable types, 0 classic). The H2b logs have no `THR` lines (other logger), so the control is by creation, not by a logged branch.
- (d) **Func 24 route**: the resume spent one pilot attempt (heph-f, `explore --persist 25`); it died at hop 19 in the River of Flame. heph-c/heph-e stopped at "no target"; heph-d died. An owner-played Hellforge session is the open route.
- (e) **Symbols** `ITEMTYPES_IsThrowable`, `PROP_Func12_SkillRand`, `PROP_Func23_Ethereal` I → C. `sub_00633680_ItemIndexByCode` (evidence row in items/0011) is left I although its return (31 = `lsd`) was logged 141 times; the review may raise it.
- (f) **Totals** taken against `main` `3d1cc99` after merging it into the lane: no class move proposed; static 567, harness 526, blocked 414, deferred 2, raised 17: 1 526 (inventory § 2.6 H2c block).

Spec-writer entry filed: `2026-10-21-reverser-spec-writer-h2c-forced-throwables-and-tc-named-props-spec.md` (to be released with the review). Not blocking.
