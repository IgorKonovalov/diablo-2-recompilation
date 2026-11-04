---
from: spec-writer
to: archivist
date: 2026-11-04
status: open
context:
  - ../specs/path/search.md
  - ../findings/path/0003-short-planners.md
  - ../tables/PathTypes.md
resolution: ""
---

From lane/s54 (plan 0054 Phase 3). docs/specs/path/search.md names the planners' direction tables by address and shape but not their values: g_DirOctant 0x006F1518 (all three columns; drlg/outdoor reads column 0), g_PathDistNear 0x006F1698, g_PathStep8Long 0x006F1798, g_PathSearchTurnRows 0x006F17D8 (rows beyond those path/0002 tabulates), g_PathDirTriples 0x006F1648, g_T15DirFromStep 0x006F1E28, g_T15TurnA/NextA/TurnB/NextB 0x006F1EC0.. and g_PathDirTable 0x006EB7E0. tools/path_scan.py tables prints some of them; tools/path_emu3.py reads the rest from the pinned image. Please add them to tools/path_survey.py and to docs/tables/PathTypes.md (or a table doc of its own), by script, so a reimplementer without the image has them. Not blocking: the spec's statements hold without them.
