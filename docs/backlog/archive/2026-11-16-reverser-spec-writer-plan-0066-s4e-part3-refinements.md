---
from: reverser
to: spec-writer
date: 2026-11-16
status: done
context:
  - ../../plans/done/0066-simulation-inferred-claims-sweep.md
  - ../../findings/items/0013-grids-belts-stacks.md
resolution: "Applied in plan 0066 Phase 3, the stats/items cluster (lane/n66si): items 1–6 in items/use and items/inventory; item 7 needs no text, no spec describes GameFindUnit's per-type lists [log](../../plans/done/0066-simulation-inferred-claims-sweep.md)"
---

Plan 0066 batch S4e part 3 (`lane/n66z`, run:2026-11-16-sweep2-s4e-emu part 3) ran the item request handlers and
`UnitInteract`'s item case under emulation to their first callee. Claims in
[items/0013 § 12](../../findings/items/0013-grids-belts-stacks.md#12-plan-0066-batch-s4e-part-3-the-request-handlers-and-the-pickup-under-emulation-run2026-11-16-sweep2-s4e-emu);
rows in the 0066 inventory (items/use 6, 18–20; items/inventory 1, 9, 10, 28–31, 40, 41, 43, 45, 64, 99). For Phase 3,
not blocking. Refinements to carry into the specs (no contradiction):

1. **items/use § B and Constants.** `PktPosFar`: the unit's position is the static path's dwords for types 2, 4, 5,
   else the dynamic path's `u16`, 0 with no path; per axis `|pos − u16(v)| > bound` signed, with a 32-bit `neg`, so a
   difference of −2³¹ passes. The 50 is the callers' EBX. `0x26`'s "holds with any input" holds for the player (a
   dynamic path); a static-path unit with a coordinate above `0xFFFF` can fail it. `0x27`: `PktOwnedItemBad` passes
   an owned item, or else the player's cursor item.
2. **items/inventory § D, `0x13`/`0x16`.** A type of 6 up returns 2; `0x16` with type 0 and the player's own guid
   returns 3.
3. **§ D `0x17` and § E1.** The interaction test runs only when `PlayerIsBusy` is non-zero (a non-player skips it), and
   `InteractIsPlayer` does not read its stack argument: the `(0)` and `(1)` select nothing; drop them.
4. **§ D `0x19`.** A non-empty cursor calls `NoManaMsg` (0x00549A60) before returning 2; a 0 from the trade test
   `0x00535610` returns 0 with nothing moved. The test's map: interaction flag set → partner (type `+0x68`, id
   `+0x64`) missing → `PlayerClearInteract`; NPC → 0x00573140; player → `TradeItemTest` (partner PlayerData `+0x5C`
   0 → 0, else 0x005B5810); other types pass; no interaction → PlayerData `+0x4C` non-zero → 0, else pass when
   PlayerData `+0x50 ≤ 4` signed.
5. **§ E1.** `InvPlaceItem` is called with ECX 0x006E1050 and EDX 0xBF6; the page byte is the low byte of the
   packet's dword; levels 1, 40, 75, 103, 109 are the towns `LevelIsTown` accepts.
6. **§ I1.** A missing item and a mode other than 3 return 1, as does `d > 50`; the walk is `InteractWalkTo`
   (0x00548A50) with the pushed word −2 for a non-zero action and −1 for 0 (EDI 4), which then starts
   `PLAYER_ModeCmdUnit` (items/0014 § 4, a reading after the boundary).
7. **GameFindUnit** (wherever the specs describe it): type 5 walks one list from game + 0x1B20, with no bucket.
