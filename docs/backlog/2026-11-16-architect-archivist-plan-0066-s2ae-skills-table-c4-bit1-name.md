---
from: architect
to: archivist
date: 2026-11-16
status: open
context:
  - ../findings/skills/0002-missiles.md
  - ../findings/skills/0003-handlers.md
  - ../tables/Skills.md
resolution: ""
---

Raised at the Tier A review of plan 0066 batch S2ae (`lane/n66sa`). `docs/tables/Skills.md` row `TgtPlaceCheck` (the `[I]` meaning cell) says `sub_005FD470_MonSkillTargetOk` requires "the target must be dead". The test it reads is `+0xC4` bit 1 **set** (0x005FD4C5–0x005FD4D0, then `COLL_PatternTestBool(…, 0x3C01)`). S2ae part 5 emulated `SKILLS_TargetCheck` whole ([skills/0002 § 21](../findings/skills/0002-missiles.md#21-plan-0066-batch-s2ae-part-5-skills_targetcheck-and-two-re-seed-callbacks-emulated-2026-11-16-lanen66sa), run:2026-11-16-sweep2-s2ae5): a target with that bit clear is always cleared, and a target with it set that is not a type-1 unit in mode 12 is kept by a skill without `TargetCorpse`, so the bit is not "dead" there (no finding gives the bit a name). Please reword the cell to the test itself ("the target's `+0xC4` bit 1 set and its cell free for its pattern") unless a finding names the bit; skills/0003 § `TgtPlaceCheck` carries the same dated note. Not blocking.
