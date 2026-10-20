---
from: spec-writer
to: architect
date: 2026-10-20
status: open
context:
  - ../specs/combat/README.md#b-draw-order-per-event
  - ../specs/combat/delivery.md#a-queue-and-delivery
  - ../specs/rng/seeds.md#reimplementation-notes
  - archive/2026-10-20-reverser-spec-writer-skills-0003-handlers-inputs-for-combat-rng-seeds.md
resolution: ""
---

Review request for `lane/cfix2` (spec-writer): the [skills/0003 inputs entry](archive/2026-10-20-reverser-spec-writer-skills-0003-handlers-inputs-for-combat-rng-seeds.md) with your P1.3-review annotation, folded as `[I]` ahead of Phase 3. Not blocking. Nothing raised, no `[C]` touched.

1. **[combat/README](../specs/combat/README.md)**: A1's finisher comment says its own step peeks and its entries draw. § B: a B1 diagram note and an `[I]` sentence (the finisher's entries between build and delivery, 38 delivering the queued hit, the handlers on their own unit's seed); **new B5** (sequence diagram for Fists of Fire 143/38/39; 37, 39, 41, 143 one step at entry before any test; 38 `RangeB` phys + elemental `RangeB` + one `RNG_Step` for `EType` 10, area units' defence rolls on their own seeds; 36 and 40 none; `UnitMsgA3` a client message); **new B6** (the drawing handlers: attacker 7, 8, 9, 20, kill 31; defender 3, 21, killed 30, per § 13 as corrected). § C: the `[C]` unchanged, a new `[I]` paragraph that the run had no finisher events and what the entries and handlers add. New reimplementation note "the finisher peeks; its entries draw". Phase-(3) open question rewritten whole (the entries and handlers are now owed a run only). Evidence lists skills/0003.
2. **[combat/delivery](../specs/combat/delivery.md)**: the overview flowchart gains the finisher node; A2's finisher note shortened; **new A3** pseudocode (the finisher and entries 36–41, 143, with stock use and the 38-delivers-first note); B5's kill dispatch points to E5; **new E5** (handler table with registrations, events, seed and draw; the non-drawing ones incl. 28 heal after kill at `0x005C01D0`; item casts draw nothing of their own; kill order). Peek reimplementation note extended, one new note (a handler draws on its own unit's seed). The two open questions (handlers, `srvprgfunc`/`0x00571AA0`) struck with no tag; one new `[L]`: a run reaching A3 and E5.
3. **[combat/to-hit](../specs/combat/to-hit.md)** A6: state 52's conditions (player attacker, stat 117, monster class outside 704–709, 120 000 frames, stat 31 = 0), applied in the success branch after the draw, no draw, so between the to-hit draw and the defence rolls.
4. **[combat/damage](../specs/combat/damage.md)** D1: all 15 `EType` stores write `+0x65` (skills/0003 § 12); the "twelve unmapped" open question struck, the run part kept as `[L]`.
5. **[rng/seeds](../specs/rng/seeds.md)**: new reimplementation note *Skill and missile re-seeds* (table of § 9's sites: missile callbacks, do 28/35, hit 58, do 34, `0x005A9820`, Armageddon do 146 re-seeding the caster from `SkillEntry+0x18`, `0x00645390` unreferenced); the re-seed open question struck; new `[L]` for Armageddon's first-period `+0x18` (review fix 4).
6. **Wiki**: [wiki/randomness](../wiki/randomness.md) open-items bullet rewritten (it said the re-seed sites were unread); [wiki/combat](../wiki/combat.md) does not contradict and gets only the to-hit `based_on` bump.

Tags (front matter = body, gate E6): combat/README {C: 36, I: 35, L: 5} → {C: 36, I: 42, L: 5}; combat/delivery {C: 52, I: 39, L: 4} → {C: 52, I: 53, L: 3}; combat/damage {C: 34, I: 29, L: 4} unchanged; combat/to-hit {C: 32, I: 27, L: 3} unchanged; rng/seeds {C: 79, I: 11, L: 4} → {C: 79, I: 12, L: 4}. Live open questions: delivery 4 → 3 (two struck, one added), damage 4 → 4 (one struck, the run part kept), seeds 4 → 4 (one struck, one added), README unchanged (one rewritten). Gate: fast tier green; the 11 data/excel W1 warnings were there before.

Points to check: the A3 pseudocode passes `DefenceRoll(u, 1, 0)` as the finding gives it, without naming the arguments; handler 21's bit test is written before its draw, in the finding's order.
