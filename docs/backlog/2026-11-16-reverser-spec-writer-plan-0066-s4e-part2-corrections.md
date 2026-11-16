---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context: [../plans/0066-simulation-inferred-claims-sweep.md, ../findings/items/0011-economy.md]
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

Plan 0066 batch S4e part 2 (`lane/n66z`, run:2026-11-16-sweep2-s4e-emu,
[items/0011 § S4e part 2](../findings/items/0011-economy.md#plan-0066-batch-s4e-part-2-the-price-core-under-emulation-run2026-11-16-sweep2-s4e-emu))
corrects and refines [items/economy](../specs/items/economy.md). Not blocking; for Phase 3's items cluster (lines at
`b5999f5e`, match by text). The raises themselves (27 rows whole, 6 in part) are listed in the inventory file
[items-economy](../plans/0066-inventory/items-economy.md).

1. **F (line 551), contradicted in part.** "difficulty 3 indexes past `Level(H)` and `max buy (H)`, neither of which
   mode 0 reads for an ordinary item": the price core reads `max buy [d]` (0x0062FCFA, `rec + 0x40 + 4d`; `d = 3` is
   `rec + 0x4C`, past the record) in every mode that reaches the NPC step and uses it in mode 1 only, so mode 0 reads it
   and does not use it. The `Level` read past `(H)` happens for a body part only. Suggested: "… neither of which enters
   mode 0's result for an ordinary item (`max buy [3]` is read, unused)". The caller half (`D2S_WriteCorpses` passing
   `d = 3`, class 513) stays `[I]`.
2. **G3 (line 562), refinement.** `v < 0` writes 0 for any unit and stat; the two caps are tested only for a player
   (unit type 0) and only for stats 14 and 15; otherwise the add goes to 0x006272B0 with `delta` (not a write of `v`).
3. **B2–B3 (lines 190–191), note.** B3 follows B2, so in mode 3 an unrepairable starting item prices 0, not 1.
4. **B6 (line 211), the missing Books row.** It reaches the error routine 0x00408090 with 0xBBA through the shared tail
   at 0x0062F288 (the same as D3's 0xCDC): `[C]` to the call.
5. **D5 (line 352), note.** The ethereal test never decides in the price core: B2 has already returned 0 for every
   ethereal item in mode 3. `[I]` (a consequence of B2 and F1).
6. **C5's Encode 4 row (line 307).** `x = (lo + hi) ÷ 2` (signed) with `lo = ((v >> 2) & 0x3FF) − 256`,
   `hi = ((v >> 12) & 0x3FF) − 256`, the values `STAT_ByTimeValue(v, 0, 0, …)` writes; ISC `Multiply`, `Add`, ÷ 1024
   for all three. `[C]`.
7. **H7 and H8 (the H7 line and line 839), the timer.** `ItemReplenishDurTimer` queues at `frame + 2500 ÷ r + 1` with a 32-bit
   `idiv` and **no** floor (the floor of 125 is `ReplenishStep`'s, after its write); it queues nothing when stat 252
   is 0 or a type-3 event with `+4 > 0` is already on the item's list. H8's written value `[C]`: stat 72 = `D + 1` up to
   `M`, at `M` nothing written and no quantity step; else stat 70 = `q + 1` up to `MaxStack`.
8. **H2 (line 778).** The classic throwable's early return, the version branches' first writes (`q − 1`; 0) and the
   break of an unbroken armour item `[C]` to the first write; what follows the write stays `[I]` (routed to H4b).
