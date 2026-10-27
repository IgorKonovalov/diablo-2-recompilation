---
from: spec-writer
to: architect
date: 2026-10-27
status: open
context:
  - ../plans/0045-skills-missiles-machinery.md#implementation-log
  - ../specs/skills/README.md
resolution: ""
---

Review `lane/s45p3`: plan 0045 Phase 3, the skills spec, written in parallel with Phase 2 part 2 (`lane/p45k`) as the
2026-10-27 part 1 review allowed. Per the plan, **this review waits for part 2's review**; the statements part 2
targets are written at the findings' present tags (mostly `[I]`) for a re-tag pass after part 2.

New, `status: draft`:
- [skills/README](../specs/skills/README.md) `{C: 16, I: 24, L: 3}`: the overview, the ADR-0014 boundary, the event
  kinds and their seeds, chaining, branches.
- [skills/dispatch](../specs/skills/dispatch.md) `{C: 35, I: 185, L: 11}`: request, `SKILLS_CanUse` (decision order),
  mode start, do frame, costs, delay and periodic, item skills and casts, the skill packet (widths), progressive
  charges, the 31-handler table, summons and the pet limit, monster skill use, ammunition and wear, tier A, draws per
  event; a sequence diagram per event kind (A1, A3), worked example from the run (Raise Skeleton, C1).
- [skills/missiles](../specs/skills/missiles.md) `{C: 42, I: 88, L: 6}`: the life as a state diagram, creation,
  the damage block, the seed, the frame pass, do 1, motion, collide types, the hit, `BuildDamage`, the tables, the
  tier-A missiles, the re-seed sites; worked example from the run (Firestorm's `0x005C9290` seeds).

`[C]` statements are only the raises of skills/0001 § 17, 0002 § 11, 0003 § 15 (run:2026-10-25-skills) and the
ADR-0021 boundary reproductions of skills/0004–0016, each scoped to its run or boundary.

Updated (reviewed specs, only `[I]`/`[C]` added from accepted findings):
- [combat/README](../specs/combat/README.md): the "Owed to phase (3)" open question struck in part and rewritten whole
  (tags unchanged).
- [stats/states](../specs/stats/states.md): the Holy Shield / self-states / `+0x48` question struck, the monster
  exclusion flag kept `[L]` (tags unchanged).
- [items/economy](../specs/items/economy.md) H6: `SkillWeaponWear`'s draw now under its weapon tests (the old block
  stepped first, the finding says no draw when the weapon fails them); wear is Impale's start 7 only, the open question
  struck (`I` 84 → 85, `L` 12 → 11).
- [rng/seeds](../specs/rng/seeds.md): `0x005C9290`'s re-seed and its path calls' steps `[C]` (450 of 450), the
  rest `[I]` (`C` 80 → 81, `I` 13 → 14).
- Wiki: economy (Impale's wear, the "which skill" unknown dropped), randomness (the confirmed Firestorm re-seed);
  combat, stats-and-states and seed-to-world `based_on` bumps only. Glossary: four terms.

Not edited: table docs (plan 0051's `lane/p51b`), data/calc (no finding answers `MISS_CalcVar` 19–27),
monsters/spawn and monsters/stats (summon seeds and `MonAttackStats` are part 2's), drlg/collision (held by plan
0038 Phase 3; skills/missiles § D7 links it).

Points for the review:
1. skills/0001 § 17 and 0003 § 15 say "1 269 do and 1 142 start events" of the eleven rows at ≥ 30, but 0003 § 15's
   per-row do counts of those eleven rows sum to 947. The spec says "of the 1 269 do and 1 142 events checked in all,
   the eleven rows among them" until the reverser says which is meant.
2. The skills spec's `[C]` boundary statements cite the plan 0046 findings (skills/0004–0016) through their runs;
   the plan 0046 catalogue spec (`skills/catalogue`) is not written, so tier A's functions are specified here.
3. Phase 3's *Done when* asks for every update target of the plan's *What*; data/calc, monsters/spawn,
   monsters/stats and drlg/collision got none (reasons above).

Gate: fast tier green.
