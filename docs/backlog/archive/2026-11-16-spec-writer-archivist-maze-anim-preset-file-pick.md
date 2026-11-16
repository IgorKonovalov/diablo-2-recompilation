---
from: spec-writer
to: archivist
date: 2026-11-16
status: done
context:
  - ../../specs/drlg/README.md#algorithm
  - ../../wiki/levels.md#maze-levels
resolution: "tools/maze_render.py convert() implements drlg/README step 9 (newest first; 9a Range(L.seed, Files) iff Files >= 1; 9b forced index, else the per-build rotation for MAZE_DEF_BASE < Def < base + 16; step 5a drop rolls and 5b room-create level draws between rooms), Files as the operand; maze_render gen and maze_anim use it. maze_anim's conversion steps run in conversion order, name the rule (forced index, rotation, level-seed draw), show the draws and count them (final frame: generator + conversion). Checked against the logged builds: 846 of 846 PRC lines (91 MZ1 builds in gen-12345-bloodmoor, gen-1-catacombs-owner and the six sweep-mazes logs, 454 rotations) match in Def, index, file and the level seed after 9b; generator outputs unchanged over 12 maze levels x 4 seeds. The wiki/levels caption sentence is the spec-writer's to drop."
---

Not blocking; it makes the first `illustration` block on wiki/levels (`drlg-maze-level36`) show a step the spec
contradicts, which ADR-0034 calls an illustration bug.

`tools/maze_anim.py` (its conversion steps, "Room N: Def D, preset file F (room seed lo % n files = k)") and
`tools/maze_render.py` (line ~195, `R.seed.lo % len(live)`) pick each maze room's DS1 file, when it has no forced index, as the maze room's own seed
lo mod the number of named files (not `Files`, which step 4's note 4 says is the operand). drlg/README step 9a/9b specifies otherwise: `PresetInstanceCreate` makes one draw on the **level
seed** when `Files` ≥ 1 (step 4), then `MazePresetFile` keeps a forced index, else, for a `Def` strictly between
`MAZE_DEF_BASE[levelType]` and that + 16, takes the per-build rotation (first use of a `Def` draws `RangeB(L.seed,
Files)`, every use advances `c ← (c + 1) mod Files` before taking it). Level 36 (Catacombs, type 10, base 257) shows
it: rooms with `Def` 258–272 rotate, and each conversion with `Files` ≥ 1 spends a level draw.

Asked: make the conversion steps follow step 9a/9b (draw order newest first, the level-seed draw, the rotation), say
in the step text which rule picked the file, and count those level draws if the step text counts draws. Until then the block's caption on
wiki/levels says the file pick is the tool's own and not the spec's; drop that sentence when this closes.
