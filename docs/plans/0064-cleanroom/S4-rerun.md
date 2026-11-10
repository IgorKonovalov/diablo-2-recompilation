# Plan 0064 Phase 5 clean-room re-run: S4 (DRLG)

- **Slice:** S4, DRLG: `drlg.maze.*` and `drlg.outdoor.*` (384 observed cases: 50 maze, 334 outdoor)
- **Date:** 2026-11-10
- **Sandbox:** `workspace/cleanroom/S4r/` (implementation in `impl/`, Python)
- **Runs of `score.sh`:** 2
- **First pass (run 1):** `cleanroom: slice S4 run 1 (first pass): 1820 fields compared, 47 different, 0 cases missing`

  ```
  drlg.maze.room_count                     50 compared      0 different
  drlg.maze.rooms_digest                   50 compared      0 different
  drlg.maze.seed_after                     50 compared      0 different
  drlg.outdoor.preset_count               334 compared      9 different
  drlg.outdoor.presets_digest             334 compared     10 different
  drlg.outdoor.room_count                 334 compared      9 different
  drlg.outdoor.rooms_digest               334 compared     10 different
  drlg.outdoor.seed_after                 334 compared      9 different
  ```

- **Final (run 2):** `cleanroom: slice S4 run 2: 1820 fields compared, 0 different, 0 cases missing`

  ```
  drlg.maze.room_count                     50 compared      0 different
  drlg.maze.rooms_digest                   50 compared      0 different
  drlg.maze.seed_after                     50 compared      0 different
  drlg.outdoor.preset_count               334 compared      0 different
  drlg.outdoor.presets_digest             334 compared      0 different
  drlg.outdoor.room_count                 334 compared      0 different
  drlg.outdoor.rooms_digest               334 compared      0 different
  drlg.outdoor.seed_after                 334 compared      0 different
  ```

The 47 first-pass differences were all in 10 cases of levels 111 and 112 (the Barricade levels): each had one Barricade stamp too few (2 presets fewer, 8 out rooms more, a different seed after). One change between the runs (row 1). Before the first pass, the worked examples of drlg/outdoor § Worked example (examples 1 to 5) were used as a self-check; rows 2 and 3 record two readings that this self-check corrected before run 1.

| # | Slice | Case kind | Field or spec section | What was missing or ambiguous | What you guessed | Pass |
|---|---|---|---|---|---|---|
| 1 | S4 | observed drlg outdoor (levels 111, 112) | `drlg.outdoor.seed_after`, `.presets_digest`, `.preset_count`, `.rooms_digest`, `.room_count`; drlg/outdoor § L5 (and *Open questions* (b)) | L5: "Whether the Act V match callback also refuses a seam opening, as G4's match does, is not in a finding". First pass: I refused openings as G4 does, and 10 of the 30 Barricade cases failed. I now read § G's call-site list ("Act V `Type` 12 with its own context (§ L5)") as replacing the G1 context, `OutCellNotOpening` included. § Worked example 5 (level 111, map seed 3101: 2376 draws, seed out `E645993C:40AF44A9`) reproduces only with no refusal (2361 draws with it). The diff pointed me at 111/112 first, so this is partly guessed from the diff, and the worked example confirmed it | the Act V match does not test `0x400` | run 1 fail, run 2 pass |
| 2 | S4 | observed drlg outdoor (Acts I, II, IV) | drlg/outdoor § G4, the match | G4: "a wall cell with bit 0 names the border piece … a floor cell with `F & 2` must be free". The stamp DS1s give most wall cells a floor too (`0xC2`), and the text does not say which rule a cell with both takes. My first draft applied both, so no `Border - Border` group could match. The worked examples' draw counts (levels 2, 3, 41, 104 were 2 to 3 draws short) showed it before run 1 | a wall cell takes the wall rule only; the floor rule applies to cells without wall bit 0 | pass |
| 3 | S4 | observed drlg outdoor (111) | drlg/outdoor § L6, the prisons | "Then two more `Range` draws, always, start a full scan for the rest": my first draft drew them only when fewer than 3 prisons had been found. Re-read before run 1 ("always") | the two draws are made after the attempt loop whatever its count | pass |
| 4 | S4 | observed drlg outdoor | drlg/outdoor § G4 (*Open questions* (a)): DS1 layer | which wall and floor layer the match and the stamp read | wall layer 0 and floor layer 0 (each border DS1 has one of each; `4x3barricade_rules.ds1` has no floor layer, so the floor rule never applies there) | pass |
| 5 | S4 | observed drlg outdoor | drlg/outdoor § G4: "the others are covered" | which cells of a replacement variant are covered | per cell, in order: wall bit 0 → place (file 0, `borderFlag` 1); else `F & 2` → `OutCellClear`; else (an empty cell) → `OutCellCover`. The worked examples do not separate "cover" from "leave as is" | pass |
| 6 | S4 | observed drlg outdoor | drlg/outdoor § G4: sub-index 63 in a replacement variant | what a wildcard wall cell writes | it writes nothing (the cell is kept) | pass |
| 7 | S4 | observed drlg outdoor | drlg/outdoor § G4: the wildcard in the match | whether "matches any `Def`" includes def 0, and whether a wildcard cell is still refused on an opening | any def, 0 included; the opening refusal still applies to wildcard cells in Acts I, II, IV (requiring def ≠ 0 broke worked example 5's level 41 count) | pass |
| 8 | S4 | observed drlg outdoor | drlg/outdoor § G3: `N < 0` | whether the `N = 0` exit also takes `N < 0` | `N ≤ 0` returns false with no draw | pass |
| 9 | S4 | observed drlg outdoor (Act V) | drlg/outdoor § L5, `g_A5SubDefMap` rows 8 and 9 in a replacement variant | what main 48 sub 30 (Def 0) and sub 31 (−5) write when they appear in a replacement | nothing is written; in the match, sub 30 requires def 0 and sub 31 matches any def | pass |
| 10 | S4 | observed drlg outdoor (Act V) | drlg/outdoor § G4 "Positions snap down to multiples of `GS`" | how the snap is applied to the shuffled `(px, py)` | `px − px mod GS`, `py − py mod GS`, applied to each shuffled position before the match | pass |
| 11 | S4 | observed drlg outdoor (Act V) | drlg/outdoor § L4 gates (*Open questions* (c)) | each edge's row or column and scan direction; the edge order | the order as listed (909 top, 908 bottom, 910 left, 907 right); top row 0 and bottom row `ch − 2` scanned by ascending x; left column 0 and right column `cw − 2` scanned by ascending y | pass |
| 12 | S4 | observed drlg outdoor (111) | drlg/outdoor § L6 fallback scan (*Open questions* (c)) | the scan's order | from `(x0, y0)` of the two extra draws: rows by `y0 + 2j` wrapping, columns by `x0 + 2i` wrapping, stopping at 3 prisons (the fallback may not have been reached in the set) | pass |
| 13 | S4 | observed drlg outdoor (80, 81) | drlg/outdoor § J5 (*Open questions* (d)) | the `hi`/`max` that 80's and 81's `Fill` calls leave out; `OutFillRandom`'s shuffle width and fit; the pad and sides of `PlaceRandom(630/631/647, i)` | 80: `Fill(635, 635, 4)`, `Fill(633, 634, 0)`, `Fill(632, 632, 0)`; 81: `Fill(651, 651, 4)`, `Fill(649, 650, 0)`, `Fill(648, 648, 0)` (by analogy with 79); the shuffle is `Shuffle(cw·ch, cw)` over unshifted cells, fit with pad 0 and no sides, and the loop stops at `max` placements; `PlaceRandom` with pad 0, sides `0xF` | pass |
| 14 | S4 | observed drlg outdoor (Act I) | drlg/outdoor § H3, A1BridgePlace (*Open questions* (e)) | which cells are "the free cells beside" the bridge row | `(x − 1, y)` free, and `(x + 2, y)` free when inside the grid (on the east river it is not) | pass |
| 15 | S4 | observed drlg outdoor (Act I, level 2) | drlg/outdoor § H6c, `A1BridgeFind` "y in 1 … cw − 2 (sic: the bound is cw)" | what is read past the last row | the scan stops at row `ch − 1` (out-of-grid rows never match) | pass |
| 16 | S4 | observed drlg outdoor | drlg/outdoor § C5 vertex merge (*Open questions* (f)) | which vertex survives and its `type` | the earlier vertex survives, flags OR-ed (no merge occurs in the set, as § C5 predicts) | pass |
| 17 | S4 | observed drlg outdoor (Act I) | drlg/warps § B2: `LinkAnchor` and `LinkPickFixed` | the `dir` value each stores (`LinkOutdoorFlags` reads `B.dir[i]` and `B.dir[i + 1]`) | the anchor leaves −1; the fixed pick stores 0 | pass |
| 18 | S4 | observed drlg outdoor (104) | drlg/warps § A1, § B2 `g_LinkPickOutdoorFlag` | which pick call's flag survives if the Outer Steppes entry were picked again | the value of the last call | pass |
| 19 | S4 | observed drlg outdoor (Act III) | drlg/outdoor § J2c–J2d | neighbours outside the `gw × gh` jungle grid | read as 0 (owner, order, marks, res) and never written | pass |
| 20 | S4 | observed drlg maze (level 10) | drlg/maze § F table, type 3 caves | the specials' order for level 10 ("8: Den of Evil, else Down; 9: + Coldcrow; 10: + Next") | Prev, Down, Next (the "+" special appended after Down, as level 9's worked example does for Coldcrow) | pass |
| 21 | S4 | observed drlg outdoor | drlg/outdoor § *Open questions* → `backlog/2026-11-10-spec-writer-reverser-plan-0064-outdoor-unstated-steps.md` | the link points outside the sandbox (dead), so the earlier clean-room guesses it holds as leads were not available | not followed; rows 4–16 are this run's own guesses | — |
