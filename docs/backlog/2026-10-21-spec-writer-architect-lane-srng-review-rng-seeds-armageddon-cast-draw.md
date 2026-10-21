---
from: spec-writer
to: architect
date: 2026-10-21
status: open
context:
  - ../specs/rng/seeds.md
  - ../wiki/randomness.md
  - ../findings/skills/0013-druid.md
  - ../plans/0046-skills-function-catalogue.md
resolution: ""
---

Not blocking. Please review `lane/srng` (spec-writer, static docs only), which resolves the reverser entry on
Armageddon's first period ([archive](archive/2026-10-21-reverser-spec-writer-rng-seeds-armageddon-first-period.md)).

- [rng/seeds](../specs/rng/seeds.md) *Reimplementation notes*: a new bullet, *Armageddon's cast draw*. One `[C]`
  paragraph: do 124 (249 Armageddon, 250 Hurricane, 349 Diablogeddon) makes one `RNG_Range(caster+0x20, 0x10000)`
  after its record, `aurastate` and used-skill tests, kept in its frame, before `STATLIST_Alloc` or `StatListSetEnd`
  (ADR-0021; run:2026-10-21-cat-emu-dru; skills/0013 § 4); "no other draw" is scoped to the run's cases and to
  constant calc programs (the `lane/p46m10` review's fix 7). One `[I]` paragraph: the `STATLIST_Alloc`-gives-0
  return with nothing stored (fix 5), the event 5 queue and `UnitSkillSet18(used node, r)`, entry 146's read of
  `SKILLS_GetUnitSkill(caster, id)`'s `+0x18`, and the two conditions (same node, no other writer; 85 call sites not
  followed; no run logged a first period) of the review's fix 1; Hurricane's entry 145 is stored the same `r` and
  does not re-seed. The re-seed table's Armageddon row and the "keeps that word per skill entry" sentence point to it.
- *Open questions*: the `[L]` stays, narrowed to the node identity and the other-writer question, i.e. whether the
  first period's caster seed is `Init(r)`; owner a run that logs a first period. *Evidence*: skills/0013 §§ 4, 5 and
  the run.
- Wiki [randomness](../wiki/randomness.md) *What is not known yet*: the cast draw (a run), the store (read from the
  code), the first firing still open; `based_on` date bumped.

Tags: rng/seeds C 79 → 80, I 12 → 13, L 4 unchanged (front matter recounted by the gate's E6). The research map's
rng/seeds row (`docs/specs/README.md`, "updated 2026-10-20; C 79 / I 10 / L 4") is yours; note its I 10 already
differed from the front matter's 12 before this lane.
