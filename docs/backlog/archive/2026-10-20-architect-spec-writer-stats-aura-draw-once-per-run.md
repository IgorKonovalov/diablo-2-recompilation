---
from: architect
to: spec-writer
date: 2026-10-20
status: done
context:
  - ../../findings/stats/0002-states.md
  - ../../findings/skills/0011-paladin.md
  - ../../specs/stats/states.md
  - ../../specs/stats/README.md
  - ../../plans/0046-skills-function-catalogue.md
resolution: "Carried on lane/s46a: [C] one RNG_RangeB per drawing run (865 runs, 865 steps), once per run whatever the number of units hit [I] from the reading, in [stats/README § Draw order](../../specs/stats/README.md#draw-order), [states § H](../../specs/stats/states.md#h-draws-per-event-kind) (table row split, step note, reimplementation note) and the wiki (stats-and-states Sanctuary's draw, how-we-know)."
---

Not blocking, but it changes what a reimplementation does. The `lane/p46m8` review (plan 0046 batch `pal`) narrowed stats/0002's `[C]` "one `RNG_RangeB` per hit" of a damaging aura (Answer, §§ 7, 8) to what run:2026-10-17-stats counted: one draw per run that draws (865 Sanctuary runs, 865 steps); the run does not say how many units each run hit. The code makes one `SKILLS_RollElemDamage` call per run of do 66, before its target pass, and copies the packet to every unit hit ([skills/0011](../../findings/skills/0011-paladin.md) § 3, 0x005CF5D5, `rep movs` at 0x005CF367; `[I]`). Please carry this into [stats/README](../../specs/stats/README.md) (line 85, "per hit"), [states](../../specs/stats/states.md) (the aura-run row near line 409, the paragraph near line 416 and the reimplementation note near line 470, "must consume one draw per hit"), and the wiki pages that repeat it (`docs/wiki/stats-and-states.md` "Sanctuary's draw", `docs/wiki/how-we-know.md` near line 180): `[C]` one draw per drawing run; once per run whatever the number of units hit `[I]` from the reading. A reimplementer who reads "per hit" as per unit would draw once per unit, which the code does not do.
