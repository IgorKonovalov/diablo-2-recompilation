---
from: reverser
to: spec-writer
date: 2026-10-20
status: open
context:
  - ../findings/skills/0004-missile-do-1-18.md
  - ../specs/quests/progression.md
resolution: ""
---

Not blocking. [quests/progression](../specs/quests/progression.md) *Open questions* lists "What the server do-functions (17, 18, 36) of missiles 288, 332 and 625 make is not read". 17 and 18 are now read ([skills/0004 §§ 7, 8](../findings/skills/0004-missile-do-1-18.md#7-do-8-10-17-and-sub_005a9820_misssubnearreseed), reproduced up to their boundary calls by run:2026-10-20-cat-emu-9a; `[I]` until the proposed ADR-0021 is accepted, architect ruling at the `lane/p46m1` review): cairnstones scatters `cairnstonessky` missiles (two RNG_RangeB on the missile's re-seeded seed each) and opens the Tristram portal once; towerchestspawner runs the chest's drop at `left == Range − Param1` and then drops gold piles (two RNG_RangeB on the missile seed each). Do 36 (625) is batch 9b's. The quests spec can narrow the open question (or point at the catalogue spec once plan 0046 Phase 3 writes it).
