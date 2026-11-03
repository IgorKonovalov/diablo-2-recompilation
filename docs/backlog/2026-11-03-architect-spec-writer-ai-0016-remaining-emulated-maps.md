---
from: architect
to: spec-writer
date: 2026-11-03
status: open
context:
  - ../findings/ai/0016-uber-event.md
  - ../plans/0052-monster-ai.md
resolution: ""
---

From the lane/s66 review (plan 0052 P1c). That lane's prompt forbade raises, and the review raised only the class-704 arm. ai/0016 holds other emulated maps at [C] by run:2026-11-03-ai-uber that specs still state at [I]; for the next spec touch, each scoped to its first callee (ADR-0021) and not to reach, none blocking: (a) monsters/special section J: the first ModAppendApply of MonPostCreateBoss for the uber classes and the non-uber first calls (ai/0016 section 6, postc); the later mods stay [I]. (b) items/quest-drops D7: the three flags and DropItemAtUnit(game, unit, 7, ...) of 0x005E0070 (drop), and the death handler's class map at 0x005A3250 (qdeath, with its tables read from the image); the std copies stay [I]. (c) drlg/preset's level 133-136 filter bullet (presets, up to the first PresetUnitSpawn). Also in drlg/preset: the note '(levels 133-136 are unreachable)' stated flat; scope it as items/quest-drops D7 now is, to the portal reading and the absence of a code path found. Read each statement against the family's declared scope in tools/ai_uber_emu.py's docstring.
