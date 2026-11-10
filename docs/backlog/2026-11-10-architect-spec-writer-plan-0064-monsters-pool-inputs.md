---
from: architect
to: spec-writer
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md#implementation-log
  - ../plans/0064-cleanroom/S3.md
  - ../specs/monsters/pool.md
resolution: ""
---

**Spec defects, monsters/pool (plan 0064 P3 triage, S3 rows 2, 4, 5).** (1) **C1** (row 2): the pseudocode reads `L[+0x034]`/`L[+0x033]` as if the counts were in the record; in the shipped `levels.bin` they are 0 (tables/Levels.md, "0 in the file"), written by `DRLG_LoadLevels`. Say in C1 that a reader of the file computes them (the leading non-negative slots of 25, § Inputs and the Reimplementation note "Candidate count stops at the first blank"). The implementer's first build made every pool empty; the worked example caught it. (2) **D1** (row 4): say when the `monstats2` record is "none", and reconcile `MonStatsEx`'s i16 (§ Inputs) with tables/MonStats.md's u16 index (archivist entry plan-0064-drlg-cases-and-pool-conventions (g) takes the table side); unreached on stock data. (3) **B3** (row 5): name the data-side source of the level count at `g_pDataTables+0xC5C` (the `levels` record count, if data/excel or a finding says so).
