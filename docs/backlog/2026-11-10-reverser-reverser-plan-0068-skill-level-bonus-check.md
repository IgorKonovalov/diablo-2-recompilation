---
from: reverser
to: reverser
date: 2026-11-10
status: open
context: ["../findings/data/0006-loaded-tables-and-bundles.md", "../plans/0068-game-files-coverage.md"]
resolution: ""
---

**Harness piece (reverser, harness lane): check `sub_00644180_SkillLevelBonus` term by term.** Not blocking plan 0068
Phase 4, which carries the formula at `[I]`; it would raise it.

[data/0006 § 3.2](../findings/data/0006-loaded-tables-and-bundles.md#32-skilldesc-on-the-server-the-skill-level-bonus)
reads the bonus every effective skill level adds: `SkillEntry+0x2C`, 2 under state 134, stat 127, and for a player's
own-class skill stat 83 (class), stat 188 (`8·class + SkillPage − 1`, only when the skill's SkillDesc `SkillPage` is
non-zero) and stat 97 capped at 3; another class's skill takes stat 97 uncapped; then stat 126 by the skill's `EType`
and stat 107. The kept `CUL` lines (run:2026-10-27-skills) log the return only.

The piece: extend the `CUL` line (tools/gdb/skills.py) with the inputs at 0x00644180's entry: the unit's class and
type, `SkillEntry+0x28/+0x2C`, state 134, and `STATS_GetUnitStat` for 127, 83, 188 (the computed param), 97, 126,
107 with the skill's `charclass`, `SkillPage` and `EType`; then a model compares every logged return. The cases that
separate the terms need: a +class-skills item (83), a +skill-tab item on a page-1..3 skill and on a skill with
`SkillPage` 0 (188's gate), an oskill (97) above 3 on an own-class skill (the cap) and on another class's skill (no
cap), a +elemental skills item (126) and a shrine skill state (134). Any planned item or skills session with gear
that carries those stats can host it.
