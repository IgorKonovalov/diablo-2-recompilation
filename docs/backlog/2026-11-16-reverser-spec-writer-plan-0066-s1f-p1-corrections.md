---
from: reverser
to: spec-writer
date: 2026-11-16
status: open
context: [../plans/0066-simulation-inferred-claims-sweep.md, ../findings/ai/experiments.md]
resolution: ""
---

Plan 0066 batches S1f and S1o part 1 (`lane/n66x`, run:2026-11-16-sweep2-s1f in
[findings/ai/experiments.md](../findings/ai/experiments.md#run2026-11-16-sweep2-s1f)) found three statements of the
monsters/ai specs that the image does not support as written. For the Phase 3 re-tag of the AI cluster (spec-writer);
not blocking.

1. **machinery line 733 (T30a), "No writer of a kind-14 record with a unit was found in the batch."** Row 65's think
   builds a block with `+0x08` 14, `+0x0C` the unit's `[+0xC]` and `+0x10` 1 at `EBP−0x28` and passes it to
   `MonHelpBlock` (0x005F9C17–0x005F9C33), which ai/0005 § 2.18 already reads as the writer row 30 consumes. The sentence
   is a stale batch note: replace it with the writer (row 65's group call), or drop it. Inventory machinery row 82.
2. **catalogue line 4689, "Row 11 calls `UnitLifePct`, rows 4, 8 and 15 `AiLifePct`."** `AiLifePct` has four direct
   calls: rows 4, 8, 15 and 122 `Imp` (0x005E31BB, which the spec's own R122b names); `UnitLifePct` has 38, row 11's among
   them. With S1e's correction 3 (one map), the note becomes "rows 4, 8, 15 and 122 call it through `AiLifePct`". The
   source sentence is ai/0002's (dated note added). Inventory catalogue row 518 (the S1e remainder).
3. **catalogue line 3933 (R51a), "`Skill8` is set only on `diabloclone` and `uberdiablo` at stock."** MonStats also sets
   `Skill8` on 709 `uberbaal` (Chilling Armor, row 145). Scope it to the records of Diablo's block (rows 51 and 147).
   Observed in part 1; the row (catalogue 422) is settled in part 2.

*2026-11-16, part 2 (`lane/n66x`, same run record, `check-s1fo-p2.txt`):* two more.

4. **catalogue line 1559 (R71a), "its twelve stores write 0, 2, 3, 4 or 5".** Row 71's think stores `AiCtl+0x14` eleven
   times (0x005FA74B … 0x005FA9AA, objdump and r2 alike), none writing 1; the rest of the bullet stands. Write
   "its eleven stores". The source is ai/0005 § 2.8 (dated note added). Inventory catalogue row 171.
5. **machinery line 400 (§ F table, `UModTeleportTry`) and README F4's `; drlg/lifecycle`.** The row gives the seed as
   `SpawnPosPick`'s and no draws, but the function draws twice on the acting unit's seed (`ecx = unit+0x20`):
   `Range(100) < 15` at 0x005B12DB, then, with the life percentage below 30, `Range(100) < 25` at 0x005B1355; its
   `SpawnPosPick` call is 0x005B1318. Add the two draws to the *Draws* cell (acting unit, before and after the pick).
   The source is ai/0001 § 9's table (dated note added). Inventory machinery row 54.
