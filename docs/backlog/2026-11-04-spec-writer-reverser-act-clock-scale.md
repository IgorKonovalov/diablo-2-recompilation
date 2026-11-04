---
from: spec-writer
to: reverser
date: 2026-11-04
status: open
context: []
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

[frame/0001](../findings/frame/0001-tick-and-messages.md#open-questions) open questions 1 and 2, which [sim/frame § G](../specs/sim/frame.md#g-the-other-per-frame-passes) restates as open: the server's values of the clock scale `k` (`+0x28`) and flag (`+0x30`), set at act load (`0x0061C240`, `0x0061C180`), so how often `ActsClockPass` sends 0x53 and refreshes every player; and whether that refresh can change a usable item and so run `AuraSelect`, a draw route at rank 1. A static reading or a window across a 0x53 packet settles it. No frame spec statement waits on it above *Open questions*.
