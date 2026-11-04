---
from: spec-writer
to: reverser
date: 2026-11-04
status: open
context: []
resolution: ""
---

Four readings [monsters/ai/machinery](../specs/monsters/ai/machinery.md) needs and [ai/0003 § 2.12](../findings/ai/0003-pool-b.md) and [ai/0001 § 6](../findings/ai/0001-machinery.md#6-target-search) do not state. Not blocking P3a's review: the spec carries them under *Open questions*.

1. **Row 28 `Vampire` (0x005F4A70), its draw order.** The finding gives this think in prose. For "a draw above 30 or bit 0 clear" and "bit 0, a hostile and a draw ≤ 30": is the draw made when the other test already decides? And `T56`'s byte and flag at each "drawn-type walk", and each "wait 15" (`Idle` or `Delay`). A compact block in the form of § 2.13, with the anchored instructions, would do. H1 of monsters/ai covers 56 logged decisions only.
2. **Row 29's alt (0x005F4FD0).** "else state 4 becomes 1 with `SetModeAtUnit(10, 0)`": is that `AiCtl+0x14`? The spec reads it so.
3. **`MonAiFindTarget`'s range (0x005DD7F0).** Finding § 6 gives the range `aidist[difficulty]` (35 when 0) and "nearer than the best so far": how does the range enter that comparison (does the best start at it), and does it apply to list 8 and to list 9?
4. **`MonAiMove`'s refusal (0x005DEB60).** Finding § 7: "flag 2 steps the unit seed once and on `low mod 100 < 70` runs `MonAiWanderRing(4)` (1 returned), else `MonAiIdle(10)`". With flag 2 clear (`Walk(t, 0)`), does `MonAiIdle(10)` run, and with which return?
