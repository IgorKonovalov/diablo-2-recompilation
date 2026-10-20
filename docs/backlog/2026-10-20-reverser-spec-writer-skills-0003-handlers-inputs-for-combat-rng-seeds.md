---
from: reverser
to: spec-writer
date: 2026-10-20
status: open
context:
  - ../findings/skills/0003-handlers.md
  - ../plans/0045-skills-missiles-machinery.md#phase-3--spec-skills
resolution: ""
---

From plan 0045 P1.3 (`lane/p45h`), for Phase 3 and the specs that cite these oracles; not blocking, all `[I]`. (1) [combat/delivery](../specs/combat/delivery.md) and combat/README: state 52 is applied inside `COMBAT_ToHitRoll` on success by `sub_0057D810_PreventHealHook` (no draw), so it sits between the to-hit draw and the defence roll; the kill-event handler at `0x005C01D0` is handler 28 (heal after kill, no draw); handlers 7, 14–16, 20, 30 step the handler unit's seed inline and 8, 9, 21, 31 call the RNG once ([skills/0003 § 3](../findings/skills/0003-handlers.md#3-the-stat-event-handlers)). (2) combat/delivery A2 (the finisher): its `srvprgfunc` entries 37, 39, 41, 143 step the attacker's seed once at entry, 38 draws `RangeB` on it twice (three for `EType` 10) plus the area's defence rolls; `0x00571AA0` is a client message, so the existing `[L]` on it can go ([§ 1](../findings/skills/0003-handlers.md#1-progressive-entries-srvprgfunc-and-the-finishers-tail)). (3) [rng/seeds](../specs/rng/seeds.md) *Open questions*: the server re-seed sites of rng/0002 are read ([§ 9](../findings/skills/0003-handlers.md#9-re-seed-sites-rng0002--the-other-initialiser-sites)): every reached one re-seeds a missile or a stack seed except Armageddon's do 146, which re-seeds the caster's `+0x20` from `SkillEntry+0x18`; `0x00645390` is unreferenced. (4) For skills/missiles (Phase 3): P1.2's hit function 22 is `0x005ADD20`, its `CallDoFunc` caller is hit 23 (unused on stock data); the frame pass runs missiles before players and monsters (§ 11); the pet limit (§ 7).
