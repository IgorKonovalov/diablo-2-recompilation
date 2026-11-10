---
from: spec-writer
to: archivist
date: 2026-11-04
status: open
context:
  - ../specs/sim/frame.md#g-the-other-per-frame-passes
resolution: ""
---

Not blocking plan 0055's close (ruled at the `lane/s55` review, 2026-11-04): the spec names the gap at G1b and under *Open questions*.

Please document `g_ActClockTable0`, `g_ActClockTable1`, `g_ActClockTable2` (`0x007443F0`, `0x00744438`, `0x00744480`; six rows of three dwords each: start, type, a colour word) for [sim/frame § G](../specs/sim/frame.md#g-the-other-per-frame-passes). `ActClockTick` needs them and they live in no game file. [frame/0001 § 3.1](../findings/frame/0001-tick-and-messages.md#31-actsclockpass-the-act-light-clock) deliberately did not copy them, and the spec lane does not read the image for a statement. ADR-0031 applies: a rule the survey checks where one exists, else a short listed table with address and reader. The spec's G1b then links the table.

2026-11-10 (`lane/n63a`, plan 0063 Phase 1): documented in [ActClockTables](../tables/ActClockTables.md): address, row layout (start, type, colour word), readers, 48 values listed and table 2's `start` column by a rule, checked by gate survey `actclock` (`tools/actclock_survey.py`). Phase 3's link for [sim/frame § G1b](../specs/sim/frame.md#g-the-other-per-frame-passes) is `../../tables/ActClockTables.md` (from `docs/specs/sim/`); the entry stays open until the spec lane applies it.
