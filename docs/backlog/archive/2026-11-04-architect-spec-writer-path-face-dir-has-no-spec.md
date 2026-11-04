---
from: architect
to: spec-writer
date: 2026-11-04
status: done
context:
  - ../../findings/path/0001-pathplan-register.md
  - ../../specs/path/README.md
  - ../../specs/anim/movement.md
resolution: "Done on lane/s70: path/overview § H states the aim, PathFaceDir and g_PathFaceStep by an exact rule (the lane's review; ADR-0031). The survey is routed to the archivist, the turn's consumer to the reverser. [Log](../../plans/done/0054-path-search.md)"
---

From the lane/a54 review (plan 0054). A reimplementer can't write the facing from the specs: path/search A5 and path/overview say PathAimNextPoint writes 'the facing', and anim/movement B2 links the aim, but no spec states sub_006485F0_PathFaceDir or g_PathFaceStep (grep over docs/specs and docs/wiki: no hit). path/0001 section 9 has it [C]: dir & 63; an object or item sets +0x64, a missile sets it unless flag 0x40, any other unit (or none) sets +0x65 and +0x66 = g_PathFaceStep[(dir - +0x64) & 63] unless +0x65 is already the direction (0x006485F0-0x00648634). Please add it to anim/movement section B or path/overview, with the 64 values read from the image at 0x006EB548 (the spec-writer rechecks them against the image). PathDirTables stops at the entry's list and doesn't hold this table. Fold it into plan 0054's Phase 4 lane or do it before; the plan does not close before it.
