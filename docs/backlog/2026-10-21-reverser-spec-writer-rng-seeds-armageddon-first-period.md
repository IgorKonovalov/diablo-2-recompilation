---
from: reverser
to: spec-writer
date: 2026-10-21
status: open
context:
  - ../findings/skills/0013-druid.md
  - ../findings/skills/0003-handlers.md
  - ../specs/rng/seeds.md
resolution: ""
---

Not blocking. [rng/seeds](../specs/rng/seeds.md) *Open questions* asks what the skill entry's `+0x18` holds before
Armageddon's first period. Plan 0046 batch `dru` ([skills/0013](../findings/skills/0013-druid.md) §§ 4, 5;
[skills/0003 § 9](../findings/skills/0003-handlers.md#9-re-seed-sites-rng0002--the-other-initialiser-sites) dated
note) answers it in part:

- `[C]` (ADR-0021, up to do 124's `STATLIST_Alloc` or `StatListSetEnd`): srvdofunc 124 (249 Armageddon, 250
  Hurricane, 349 Diablogeddon) makes one `RNG_Range(caster+0x20, 0x10000)` after its record, `aurastate` and used-skill
  tests and keeps the value in its frame (run:2026-10-21-cat-emu-dru).
- `[I]` from the reading: after that boundary do 124 queues unit event 5 at `frame + Param4` with `(id, lvl)` and
  stores the value with `UnitSkillSet18(used node, r)` (0x005C8354–0x005C835C); do-table entry 146 reads
  `SKILLS_GetUnitSkill(caster, id)`'s node `+0x18` to re-seed the caster, so the first period uses `r` when that node
  is the used node (not run).

Please narrow the open question (the cast-time draw and its store), keeping the store and the node identity `[I]`
and the rest of the question open until a run logs a first period.
