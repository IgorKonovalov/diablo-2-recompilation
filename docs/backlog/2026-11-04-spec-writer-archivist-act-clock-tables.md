---
from: spec-writer
to: archivist
date: 2026-11-04
status: open
context: []
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

Please document `g_ActClockTable0`, `g_ActClockTable1`, `g_ActClockTable2` (`0x007443F0`, `0x00744438`, `0x00744480`; six rows of three dwords each: start, type, a colour word) for [sim/frame § G](../specs/sim/frame.md#g-the-other-per-frame-passes). `ActClockTick` needs them and they live in no game file. [frame/0001 § 3.1](../findings/frame/0001-tick-and-messages.md#31-actsclockpass-the-act-light-clock) deliberately did not copy them, and the spec lane does not read the image for a statement. ADR-0031 applies: a rule the survey checks where one exists, else a short listed table with address and reader. The spec's G1b then links the table.
