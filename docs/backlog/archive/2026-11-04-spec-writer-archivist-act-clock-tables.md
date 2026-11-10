---
from: spec-writer
to: archivist
date: 2026-11-04
status: done
context:
  - ../../specs/sim/frame.md#g-the-other-per-frame-passes
resolution: "documented in ActClockTables (lane/n63a), linked from sim/frame G1b by lane/n63w (plan 0063 P3) [sim/frame § G](../../specs/sim/frame.md#g-the-other-per-frame-passes)"
---

Not blocking plan 0055's close (ruled at the `lane/s55` review, 2026-11-04): the spec names the gap at G1b and under *Open questions*.

Please document `g_ActClockTable0`, `g_ActClockTable1`, `g_ActClockTable2` (`0x007443F0`, `0x00744438`, `0x00744480`; six rows of three dwords each: start, type, a colour word) for [sim/frame § G](../../specs/sim/frame.md#g-the-other-per-frame-passes). `ActClockTick` needs them and they live in no game file. [frame/0001 § 3.1](../../findings/frame/0001-tick-and-messages.md#31-actsclockpass-the-act-light-clock) deliberately did not copy them, and the spec lane does not read the image for a statement. ADR-0031 applies: a rule the survey checks where one exists, else a short listed table with address and reader. The spec's G1b then links the table.

2026-11-10 (`lane/n63a`, plan 0063 Phase 1): documented in [ActClockTables](../../tables/ActClockTables.md): address, row layout (start, type, colour word), readers, 42 values listed, and table 2's `start` and table 1's `type` columns by two rules (the second added at the review), checked by gate survey `actclock` (`tools/actclock_survey.py`). Phase 3's link for [sim/frame § G1b](../../specs/sim/frame.md#g-the-other-per-frame-passes) is `../../tables/ActClockTables.md` (from `docs/specs/sim/`); the entry stays open until the spec lane applies it.

2026-11-10 (`lane/n63w`, plan 0063 Phase 3): [sim/frame § G](../../specs/sim/frame.md#g-the-other-per-frame-passes) G1b now links [ActClockTables](../../tables/ActClockTables.md#values) (`[C]`, the 54 values, 42 listed and 12 by the two survey-checked rules), and the spec's *Open questions* no longer lists the tables. The request is satisfied; closed.
