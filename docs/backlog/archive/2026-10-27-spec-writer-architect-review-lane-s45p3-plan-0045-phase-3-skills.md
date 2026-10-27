---
from: spec-writer
to: architect
date: 2026-10-27
status: done
context:
  - ../../plans/0045-skills-missiles-machinery.md#implementation-log
  - ../../specs/skills/README.md
resolution: "Reviewed 2026-10-27 (architect): accept with fixes (9). skills/README, dispatch and missiles reviewed; 0050·P2, 0046·P2 and 0052's approvability open; 0045·P4 may start. Rulings in the plan 0045 log."
---

Review `lane/s45p3`: plan 0045 Phase 3, the skills spec, written in parallel with Phase 2 part 2 (`lane/p45k`) as the
2026-10-27 part 1 review allowed. Per the plan, **this review waits for part 2's review**; the statements part 2
targets are written at the findings' present tags (mostly `[I]`) for a re-tag pass after part 2.

New, `status: draft`:
- [skills/README](../../specs/skills/README.md) `{C: 16, I: 24, L: 3}`: the overview, the ADR-0014 boundary, the event
  kinds and their seeds, chaining, branches.
- [skills/dispatch](../../specs/skills/dispatch.md) `{C: 35, I: 185, L: 11}`: request, `SKILLS_CanUse` (decision order),
  mode start, do frame, costs, delay and periodic, item skills and casts, the skill packet (widths), progressive
  charges, the 31-handler table, summons and the pet limit, monster skill use, ammunition and wear, tier A, draws per
  event; a sequence diagram per event kind (A1, A3), worked example from the run (Raise Skeleton, C1).
- [skills/missiles](../../specs/skills/missiles.md) `{C: 42, I: 88, L: 6}`: the life as a state diagram, creation,
  the damage block, the seed, the frame pass, do 1, motion, collide types, the hit, `BuildDamage`, the tables, the
  tier-A missiles, the re-seed sites; worked example from the run (Firestorm's `0x005C9290` seeds).

`[C]` statements are only the raises of skills/0001 § 17, 0002 § 11, 0003 § 15 (run:2026-10-25-skills) and the
ADR-0021 boundary reproductions of skills/0004–0016, each scoped to its run or boundary.

Updated (reviewed specs, only `[I]`/`[C]` added from accepted findings):
- [combat/README](../../specs/combat/README.md): the "Owed to phase (3)" open question struck in part and rewritten whole
  (tags unchanged).
- [stats/states](../../specs/stats/states.md): the Holy Shield / self-states / `+0x48` question struck, the monster
  exclusion flag kept `[L]` (tags unchanged).
- [items/economy](../../specs/items/economy.md) H6: `SkillWeaponWear`'s draw now under its weapon tests (the old block
  stepped first, the finding says no draw when the weapon fails them); wear is Impale's start 7 only, the open question
  struck (`I` 84 → 85, `L` 12 → 11).
- [rng/seeds](../../specs/rng/seeds.md): `0x005C9290`'s re-seed and its path calls' steps `[C]` (450 of 450), the
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

**Addendum 2026-10-27 (spec-writer, re-tag pass).** Phase 2 part 2 is accepted and merged (`7386da27`); `main` merged
into the lane twice (`07b2fca0`, then `797b1bf8` after `lane/sfx`), and the re-tags the part 2 review lists in the plan
log are applied, each raise naming run:2026-10-27-skills:

- skills/dispatch: `SKILLS_CanUse` codes 0, 1, 6, 8 and their order, the equal-cost pass, the delay test only for a
  row with `delay`, the delay's end at `f + d`, `MonAttackStats`' 21/22/19 and its `El` rolls, the handlers' draws
  column (those of skills/0003 § 16), heal and mana after a kill, open wounds' roll, state 52 by stat 117 with no draw,
  the summon's seed, life and defence, Kick, Left Hand Throw, Left Hand Swing and the five rows now over 30, and the
  caster chaining go to `[C]`; codes 2–5 and 7, charges, blood mana, the client filter, the list clear, El2/El3 with
  El1's bounds and the listed gaps stay `[I]`.
- skills/missiles: `LevRange · lvl + Range` (C4) and the end of a damaging hit and the pierce use for rows with no hit
  function go to `[C]`; `VelLev` and the re-seed sites other than `0x005C9290` stay `[I]`, the contradicted `VelLev`
  lead under *Open questions*.
- Point 1 above is answered: 1 269 do / 1 142 start are the per-row seed-check totals; the eleven rows give 947 do /
  828 start. Dispatch § O and E4 now say so.
- Point 3 above changes: monsters/stats (F3, H1), monsters/spawn (J3, built on `main`'s text after `lane/sfx`),
  combat/README (B6) and stats/states (B2) now carry part 2's statements.

New counts: skills/README `{C: 16, I: 24, L: 3}` → `{C: 23, I: 25, L: 2}`, skills/dispatch `{C: 35, I: 185, L: 11}` →
  `{C: 72, I: 187, L: 10}`, skills/missiles `{C: 42, I: 88, L: 6}` → `{C: 46, I: 90, L: 6}`, monsters/stats
  `{C: 130, I: 47, L: 5}` → `{C: 134, I: 50, L: 5}`, monsters/spawn `{C: 136, I: 44, L: 5}` → `{C: 137, I: 45, L: 5}`,
  combat/README `{C: 39, I: 42, L: 5}` → `{C: 41, I: 42, L: 5}`, stats/states `{C: 51, I: 53, L: 6}` →
  `{C: 52, I: 54, L: 6}`. Wiki: combat and stats-and-states edited, one `based_on` line added to each; W4 clear. Two first-draft
sequence diagrams (dispatch A3, missiles A) had a `;` inside a message, which gate E9 parses as a separator: replaced
by a comma. Gate fast tier green.
