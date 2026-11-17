---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../findings/stats/0001-aggregate.md
resolution: "Applied in plan 0066 Phase 3, the stats/items cluster (lane/n66si): stats/aggregate F2 (corrected floor), C5 and the getters/op 3, 10, 12 lines [log](../../plans/done/0066-simulation-inferred-claims-sweep.md)"
---

Plan 0066 batch S4e part 1 (`lane/n66z`, run:2026-11-16-sweep2-s4e-emu,
[stats/0001 § 11](../../findings/stats/0001-aggregate.md#11-plan-0066-batch-s4e-part-1-the-stats-family-under-emulation-run2026-11-16-sweep2-s4e-emu))
corrects and refines [stats/aggregate](../../specs/stats/aggregate.md). Not blocking; for Phase 3's stats cluster (lines
at `b5999f5e`, match by text).

1. **F2 (line 338), contradicted in part.** The readers test `v < MinAccr` (signed, `MinAccr` unshifted) and then
   return `MinAccr << ValShift` (shift masked to 5 bits): a value at or above `MinAccr` but below the shifted floor is
   returned unchanged, so "floor the value at `MinAccr << ValShift`" is wrong for `maxhp` (`MinAccr` 1, `ValShift` 8:
   1..255 kept, 0 or less gives 256). The floor also needs a non-NULL record argument (the take test of ops 2/3 and
   `StatEvaluate`'s ops 2–5 base reads pass NULL) and the list's `+0x10` bit 31 (the base reader too); an absent entry
   returns 0 unfloored. `[C]` as code.
2. **C5 (line 210), refinements.** Ops 2/3 read `w` with no floor; ops 4/5 through `STATS_GetUnitStat` with it; an op
   byte above 13 takes (the `ja` at 0x006267A0), unreachable on loaded data (E1 zeroes such ops). The rest of C5 `[C]`.
3. **G1 (line 363), D1 (line 298), entry points (line 50).** The getters' bodies `[C]`: `StatListGetValue(unit +0x5C,
   stat << 16, record)`, 0 for a NULL unit or list or a DataTables count at or below the stat; they read no CharStats
   cell (the `tbl:CharStats.txt:LifePerVitality` anchor on that sentence is the op 8/9 factor's, not the getters').
   Op 3 `[C]` as code (op 2's gates, then `MulDiv(b0, term, 100)`), ops 10 and 12 skip; no stock row has op 3, 10 or 12.
