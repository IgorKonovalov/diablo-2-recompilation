---
from: architect
to: spec-writer
date: 2026-10-30
status: open
context:
  - ../findings/skills/0003-handlers.md#17-plan-0046-phase-2-the-catalogue-sample-run2026-10-30-skills-catalogue
  - ../specs/rng/seeds.md
resolution: ""
---

From the lane/p46h check (plan 0046 P2). skills/0003 § 17 raised sub_005AC040_MissCbReseedPathX to [C] (36 of 36 creations: seed on the Init(path +0x10) stream, 10 steps past it; run:2026-10-30-skills-catalogue). docs/specs/rng/seeds.md (re-seed sites, the callbacks paragraph, ~lines 548-560) says the other sites of the table were not reached [I] and lists 0x005AC040 among the [I] callbacks; missiles.md § H likewise. Update at the next rng/skills spec change (0046 P3 reads it).
