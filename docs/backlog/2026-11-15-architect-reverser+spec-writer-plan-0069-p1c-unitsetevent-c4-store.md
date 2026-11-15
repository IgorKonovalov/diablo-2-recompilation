---
from: architect
to: reverser, spec-writer
date: 2026-11-15
status: open
context:
  - ../plans/0069-monster-ai-bestiary-tour.md#implementation-log
resolution: ""
---

UnitSetEvent (0x00553380) ends with 'or dword [esi+0xC4], 0x400' (0x005533B9, after its null-unit assert), found by plan 0069 Phase 1c (lane/n69c) from a logged c4 mismatch (R32, decision 1310 of 2026-11-03-ai-3-s2-5804-L4-fresh:a1-marsh.log). The ai findings name the call only: docs/findings/ai/0013-batch12.md line 311 ('What UnitSetEvent(U, 18, p) does on the player: not read') and the R32, R54 and R58 blocks (0013 line 150 and 178, R58's step 3) omit the store; the same holds for any block calling UnitSetEvent (0002 213, 0011 377, 0012 485, 0001 363). Reverser: add the store to those finding statements (and symbols row sub_00553380_UnitSetEvent is items/cube-owned: note the second reader). Spec-writer: carry it into the ai specs at plan 0066 Phase 3, where the calls are stated.
