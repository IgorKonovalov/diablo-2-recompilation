---
from: architect
to: spec-writer
date: 2026-11-10
status: done
context:
  - ../../plans/done/0064-clean-room-test.md#implementation-log
  - ../../plans/0064-cleanroom/S3.md
  - ../../specs/monsters/pool.md
resolution: "Done (lane n64x, plan 0064 P4) in [monsters/pool](../../specs/monsters/pool.md): (1) C1's pseudocode, diagram and two step notes say the counts are load-time bytes, 0 in levels.bin, that a file reader computes as the leading non-negative slots (Levels § Fields with no .txt column, monsters/0001 § 3); (2) D1's none is an out-of-range MonStatsEx, read signed, as MonSpawnTry's inline lookup tests it (monsters/0002 § 6), unreached on stock data; the Inputs row reconciled with tables/MonStats (s16, no blank); the getter's own test filed as [monstats2rec-bound-test](../2026-11-10-spec-writer-reverser-monstats2rec-bound-test.md); (3) and the S3 row 5 probe: the state row names levelCount = g_nLevels at 0x0096C88C (g_pDataTables+0xC5C), the levels.bin u32 count (data/excel B1 and C1, data/0001 § 5), and B3's step note ties the loop bound to it (levels 1-136)."
---

**Spec defects, monsters/pool (plan 0064 P3 triage, S3 rows 2, 4, 5).** (1) **C1** (row 2): the pseudocode reads `L[+0x034]`/`L[+0x033]` as if the counts were in the record; in the shipped `levels.bin` they are 0 (tables/Levels.md, "0 in the file"), written by `DRLG_LoadLevels`. Say in C1 that a reader of the file computes them (the leading non-negative slots of 25, § Inputs and the Reimplementation note "Candidate count stops at the first blank"). The implementer's first build made every pool empty; the worked example caught it. (2) **D1** (row 4): say when the `monstats2` record is "none", and reconcile `MonStatsEx`'s i16 (§ Inputs) with tables/MonStats.md's u16 index (archivist entry plan-0064-drlg-cases-and-pool-conventions (g) takes the table side); unreached on stock data. (3) **B3** (row 5): name the data-side source of the level count at `g_pDataTables+0xC5C` (the `levels` record count, if data/excel or a finding says so).

**Added 2026-11-10 (orchestrator, plan 0064 Phase 3 fresh-reader probe, S3 row 5):** the reader answered 136 levels
(1 ..< 137, the `levels` record count) but had to guess twice: that B3's `levelCount` is the state table's "level
count" row (matched by name only), and that pool's `g_pDataTables+0xC5C` is data/excel § C1's `0x0096C88C`. Row 5 is
a spec defect: name the variable in the state table and state the address (or link C1's row).
