---
from: archivist
to: architect
date: 2026-11-17
status: done
context:
  - ../../plans/0070-redacted-public-export.md
resolution: "Tier A review 2026-11-17: accept with fixes 4; rulings 1-3 accepted (test tightened); done-when 'check passes' open on hex values in captions, see plan 0070 log"
---

Review request (plan says Tier A): Phase 2b, lane/x70s. Schematic mode of tools/maze_anim.py and tools/tc_anim.py, the marker and schematic.json, tools/test_anim_schematic.py. Rule on three points: (1) the no-art test admits one caller reading a preset DS1's floor0 values (the map-scan draw counts) where the done-when says ds1 tile layers are blocked; (2) the maze's warp lines are not in the schematic steps (they need the DS1 wall layer), so step equality is exact except the warp and icon lines; (3) the HTML marker is a comment and the page has no meta, to fit export_check.py (lane/x70c). See the plan's Implementation log entry of 2026-11-17.
