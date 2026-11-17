---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../findings/items/0013-grids-belts-stacks.md
  - ../../findings/items/0012-use-inventory.md
resolution: "Applied in plan 0066 Phase 3, the stats/items cluster (lane/n66si): items 1–4 in items/use and items/inventory; item 5 needs no text (G3's after stays [I], H4d) [log](../../plans/done/0066-simulation-inferred-claims-sweep.md)"
---

Plan 0066 batch S4e part 5b (`lane/n66z`, run:2026-11-16-sweep2-s4e-emu part 5b) ran `GolemHealShare` and
`GolemHeal`, `ItemUsePotion`'s doubling draw at chosen draws, kind 3's return for amounts at and below 0, and
`StackRequest` under emulation. Claims in
[items/0013 § 15](../../findings/items/0013-grids-belts-stacks.md#15-plan-0066-batch-s4e-part-5b-the-blood-golems-heal-the-doubling-draw-kind-3s-return-and-stackrequest-run2026-11-16-sweep2-s4e-emu);
rows in the 0066 inventory (items/use 34, 38, 52; items/inventory 57, 58). For Phase 3, not blocking. Re-tags and
refinements to carry into items/use and items/inventory (no contradiction):

1. **items/use H5 and its § H note.** "`v = 0` sets the golem to full" can be `[C]` (ADR-0021) to the
   `UnitSetStat(golem, 6, UnitGetMaxHp(golem), 0)` call, anchored at `GolemHealShare`'s branch 0x005C68AC → 0x005C68F0
   (fn:sub_005C6870_GolemHealShare@0x005C6870), not at `GolemHeal`: `GolemHeal` (0x005C5F10) itself returns 0 with no
   call at `v ≤ 0`. Add to H5: the heal's cap is a signed compare after an `i32` add, so a sum past `2³¹ − 1` is
   stored wrapped, not capped (no stock golem comes near it). The returns after the set stay `[I]`.
2. **items/use F1c.** The rule `r2 < r1 >> 1` is `[C]` (ADR-0021) at each pair over 146 `n`, for players and
   non-players; a stat of 0 or below makes no draw. The chance bullet can be `[C]` as the count of pairs, with the
   refinement that it weighs each `(r1, r2)` pair equally, which the generator's `low mod n` only approximates.
3. **items/use F1h.** "every amount ≤ 0 returns 0" and "len + rem ≤ 0 included" (the 1 of a refill slot that applied
   nothing, with no callee) are `[C]` (ADR-0021); the 1 after `UnitAddStat` or `STATLIST_SetStat` stays `[I]`
   (0x005BE6D4). Amounts the class scale, the doubling or the shift take to ≤ 0 as `i32` count as ≤ 0.
4. **items/inventory G4.** `[C]` (ADR-0021) to `StackMerge`. Add: a unit found that is not of type 4 returns 0 with the
   flag clear (like an unstackable pair, not like a missing unit); only the second (target) item's page is tested; the
   class compare at 0x0055E8A3 after `ItemsCanStack` is never unequal (its own compare, 0x0062C873), `[I]`.
5. **items/inventory G3 "After the first set".** Stays `[I]`; now routed to the harness (H4d) because each branch's
   stat message can allocate in `ClientQueuePacket` (0x0040B430 at 0x0053B2DD).
