---
from: spec-writer
to: reverser
date: 2026-11-04
status: done
context:
  - ../../specs/sim/frame.md#g-the-other-per-frame-passes
resolution: "Read (plan 0063 P2a, lane/n63r): on the server k = 128 and flag 0 from DUNGEON_ActCreate, and k = 4 with flag 1 during Act II's eclipse (A2Q3); 0x0061C240 is client code, 0x0061C180 unreferenced. ActsClockPass sends 0x53 on 26 frames per day; the longest gap is 2 176 frames (136 in act index 3, 68 in the eclipse); tools/act_clock.py. A clock change alters no item's usability on stock data; the refresh reaches AuraSelect through sub_0055DA70_PlayerSkillReselect only when a wanted skill differs from the current one and is usable. The remainder (which events leave that state; a set item with a book skill) stays under the finding's open question 1. [frame/0001 § 3.1a](../../findings/frame/0001-tick-and-messages.md#31a-the-servers-clock-scale-flag-and-the-send-rate-plan-0063-phase-2a-lanen63r-2026-11-10)"
---

Not blocking plan 0055's close (ruled at the `lane/s55` review, 2026-11-04): the route is named in § J's rank 1 and under *Open questions*.

[frame/0001](../../findings/frame/0001-tick-and-messages.md#open-questions) open questions 1 and 2, which [sim/frame § G](../../specs/sim/frame.md#g-the-other-per-frame-passes) restates as open: the server's values of the clock scale `k` (`+0x28`) and flag (`+0x30`), set at act load (`0x0061C240`, `0x0061C180`), so how often `ActsClockPass` sends 0x53 and refreshes every player; and whether that refresh can change a usable item and so run `AuraSelect`, a draw route at rank 1. A static reading or a window across a 0x53 packet settles it. No frame spec statement waits on it above *Open questions*.
