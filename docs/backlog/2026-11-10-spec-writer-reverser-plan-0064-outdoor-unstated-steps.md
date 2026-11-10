---
from: spec-writer
to: reverser
date: 2026-11-10
status: open
context:
  - ../plans/0064-clean-room-test.md#implementation-log
  - ../plans/0064-cleanroom/S4.md
  - ../specs/drlg/outdoor.md
  - ../findings/drlg/0008-outdoor.md
resolution: ""
---

**Steps of drlg/outdoor that no finding states (plan 0064 Phase 4, items 7–11 and 14 of
[plan-0064-drlg-outdoor](2026-11-10-architect-spec-writer-plan-0064-drlg-outdoor.md); S4 rows 9–12, 17, 21). Static only, no
slot.** The spec-writer wrote what [drlg/0008](../findings/drlg/0008-outdoor.md) holds and listed the rest under
drlg/outdoor *Open questions*; each point below needs a statement in drlg/0008 (address, reading, tag) before the spec can
say it. The clean-room S4 implementer's guess is given as a lead where it scored right (S4 ledger); it is not evidence.

- (a) **G4, `BorderSubFits` 0x0066F3B0 / `BorderSubStamp` 0x0066F520** (row 9): which DS1 wall and floor layer the match and
  the stamp read; what a replacement-variant wall cell with sub-index 63 does (lead: writes nothing); which cells "the
  others are covered" means (lead: every group cell with neither a wall bit 0 nor floor `& 2`); where the wildcard is
  compared (lead: the computed `Def` against `baseDef + C.wildcard`, i.e. sub-index 63); and whether `BorderSubGroup`'s
  `N = 0` test also returns on `N < 0` (0x0066F690).
- (b) **L5, `BarricadeSubMatch` 0x0067E080** (row 10): whether the Act V match callback applies a seam-opening test as
  G4's `OutCellNotOpening` does (lead: it does not; with the test, level 111 of map seed 3101 made 2 361 draws against the
  worked example's 2 376).
- (c) **L4 `BarricadeGates` 0x0067DB50 and L6 `BarricadePrisons` 0x0067E240** (row 11): which row or column is each edge,
  the scan direction along it, and the prisons' fallback scan order after its two `Range` draws (lead: edges at row 0, row
  `ch − 2`, column 0, column `cw − 2`, each scanned from 0 upward; the fallback rows outer over even cells).
- (d) **J5 `OutKurastLevel` 0x0067F190, `OutFillRandom` 0x0067EED0** (row 12): the omitted `hi`/`max` of `Fill(635 …)`,
  `Fill(633, 634)`, `Fill(632)` and level 81's `Fill(651 …)`, `Fill(649, 650)`, `Fill(648)`; `OutFillRandom`'s shuffle width
  and its fit test's pad and sides; `PlaceRandom(631, 0)`'s pad and sides (lead: `(635, 635, 4)`, `(633, 634, 0)`,
  `(632, 632, 0)` and 651/649–650/648 alike; shuffle width `cw`, fit pad 0 and sides 0; `PlaceRandom` pad 0, sides `0xF`).
- (e) **H3 `A1BridgePlace` 0x0067FD20** (row 17): which cells are "the free cells beside" row `y` (lead:
  `OutCellFree(x − 1, y)` and `OutCellFree(x + 2, y)`).
- (f) **C5 `OutVertsToCells` 0x00675080** (row 21): when a vertex equals its successor, which of the two survives and what
  its `type` byte becomes (lead: the successor survives, flags or-ed). Unreached on stock data in Acts I, II, IV, V.
- (g) **H0 `g_LinkOutdoorFlags` 0x006F1258** (probe row 20): drlg/0008 § 16.3 prints `—` for `not1`/`not2` of rows 6–14.
  The spec now gives the stored value 0, read through `tools/drlg.py`'s reader (`_lx_ints(0x6F1258, 90)`: rows 6–14
  `{2, 0, 0, …}`), the reader the § 16 tables are `[C]` by; print the zeros in the finding's table.
- (h) **`LevelAdjInsert` 0x0066B720** (probe row 7): with two or more nodes, where a node that sorts before the head goes
  (drlg/0008 § Plan 0038 batch S4a says only that the quirk skips the head). Lead: `tools/drlg.py` `adj_insert` walks from
  the second node, inserts before the first node the new one sorts before, else appends.

*Architect note (`lane/n64x` review, 2026-11-10):* for (g), r2 `pxw` at 0x006F1258 gives rows 6–14 as
`{2, 0, 0, dirI, dirNext, flag}`, the zeros the spec writes; only the finding's table needs them printed.
