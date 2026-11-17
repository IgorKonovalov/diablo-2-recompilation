---
from: archivist
to: architect
date: 2026-11-17
status: open
context: []
resolution: ""
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

**Review request (Opus, Tier A): ADR-0036 ruling on a second DS1 read in the schematic mode.** Branch `lane/x70w`,
plan 0070 log entry of 2026-11-17 (Phase 7 owner feedback: the maze's last frame lacked entry and exit marks).

Source of "which room holds warp slot m". No room-level fact exists in the specs: [warps.md § D](../specs/drlg/warps.md)
and [LvlPrest § Warp slots](../tables/LvlPrest.md#warp-slots-plan-0022-phase-2) give the slot per placed record by
DS1 survey, and the model's own room-flag grid (`drlg.py` `warp_grid`) is keyed by cell. A hand-copied Def-to-slot
table would be a data dump of that survey and would drift. So the lane chose the narrow helper:
`ds1.room_warp_slots(data)` reads the wall layer through `_scan_cells` and returns a `frozenset` of slot numbers
(0..7) only. `tools/maze_anim.py` `warp_rooms()` is its one caller: it maps (room, slot) through Levels `Vis` to a
destination and the drawing puts a cyan diamond at the room box's centre with the full mode's label. No coordinate,
cell or layer reaches drawing code.

Test (`tools/test_anim_schematic.py`): `_scan_cells` is blocked except under `room_warp_slots`; `parse` and the
`layers` key admit `room_warp_slots` and `_scan_cells` (reached only through it) as callers beside
`PresetUnitData.ds1`; the helper's return is checked to be a frozenset of ints below 8. The two warp lines of the
steps are now shared between the modes (the equality exceptions shrink to the icon and name-card lines).

Asks: (1) rule that this read stays inside ADR-0036 (it depicts no layout and shows no position, only which box); (2)
check that the position-free label ("position in room not shown") is enough; (3) the full mode is byte-identical
(rerun of the unchanged command on `main` and on the branch, all 46 files equal).
