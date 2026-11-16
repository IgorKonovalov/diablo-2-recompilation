---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/0066-simulation-inferred-claims-sweep.md
  - ../../findings/items/0013-grids-belts-stacks.md
  - ../../findings/items/0012-use-inventory.md
resolution: "Applied in plan 0066 Phase 3, the stats/items cluster (lane/n66si): items 1–4 in items/use and items/inventory; item 5 needs no text [log](../../plans/0066-simulation-inferred-claims-sweep.md)"
---

Plan 0066 batch S4e part 5c (`lane/n66z`, run:2026-11-16-sweep2-s4e-emu part 5c) ran `Pkt61MercItem`, `ItemUse` with its
stock test and use entries, and `ItemSkillQtyAdjust` under emulation. Claims in
[items/0013 § 16](../../findings/items/0013-grids-belts-stacks.md#16-plan-0066-batch-s4e-part-5c-the-mercenary-button-itemuse-after-its-entries-itemskillqtyadjust-and-the-routes-past-invitemremove-run2026-11-16-sweep2-s4e-emu);
rows in the 0066 inventory (items/use 21, 22, 34, 54; items/inventory 20, 25–27, 39, 42, 45, 99). For Phase 3, not
blocking. Re-tags and refinements to carry into items/use and items/inventory (no contradiction):

1. **items/use B, the `0x61` row.** `[C]` (ADR-0021) to `MercGiveCursorItem` (0x0054D230) and `0x0054D130`. Add, in
   order: `PlayerIsBusy` and `InteractIsPlayer` both non-zero return 3 (after the expansion test); "a used skill" is the
   skill block at `player+0xA8` with a non-zero `+0x10`; "alive" is `UnitIsDead` (the `+0xC6` bit 0; a player in mode 0
   or 17, a monster in mode 0 or 12); the pet is the unit of the first type-7 node whose bit 0 is clear, and only when the
   pet-type count is above 7; the pet's room must be in the player's room's near list (`0x0065A590`); no inventory
   returns 3; with no cursor item a non-zero `u16` at `+1` calls `0x0054D130(player, u16)`, a zero returns 0; a quest item
   (Items `+0x12A`) returns 0.
2. **items/use C2.** `[C]` (ADR-0021) for: a test's non-zero leaves the marks and `ItemUse` returns 0; a use returning 0
   calls `InvClearUseMark`; a non-zero use's return is `ItemUse`'s (met for 1). Keep `[I]`: message `0x7C` after
   `InvClearUseMark` (0x005BF345, 0x005BF3B1); "a test returning 0" is a branch no stock entry takes (kind 1's test
   returns 1 on both paths, 0x005BE16F), worth saying so.
3. **items/inventory C2.** `[C]` (ADR-0021) to the message builder: Books `+8` for type 22 (a type-22 item that is also
   type 18 too), `+0xC` for type 18, else −1 → 0. Refinements: a tome with stat 70 = 0 returns 0 before the skill is
   looked up (0x0055C13E); `q` is stat 70 itself when non-zero (not `max(stat 70, 1)`; a negative value is used as is),
   1 for a non-tome with stat 70 = 0; a missing skill with `add ≠ 0` calls `UnitAddStat(unit, 5, q, 0)` then
   `0x00570080`; with `add = 0` it reaches the error routine (line `0x230`). Keep `[I]`: the send, the left and right
   resets, the grant and the 1.
4. **items/inventory C1.** `0x0055C270` calls `ItemSkillQtyAdjust(1)` for a player only, `[C]` (ADR-0021); the
   statement "`0x0055C110` holds no test of a page or a stash" is `[C]` (ADR-0021, page 4 against the others). The rest
   of C1 stays `[I]` (past the put, see 5).
5. **Routed to the harness, no spec change:** items/inventory B5's "After" (the page fill, page byte and location byte)
   and the rows past `InvItemRemove` (D `0x63`'s "then to that box", E2 after the remove, a refusal after
   `InvItemRemove`) cross `InvItemRemove` → `0x006277F0` → the owner's stat recompute (allocator 0x0040B4B0); items/use
   I's `useable` gate lies after `InvClearUseMarks` (`ClientQueuePacket`, allocator). They keep `[I]` until H4c/H4d.
