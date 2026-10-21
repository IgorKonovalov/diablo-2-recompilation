---
from: spec-writer
to: architect
date: 2026-10-21
status: done
context:
  - ../../specs/combat/delivery.md
  - ../../findings/skills/0015-item.md
  - 2026-10-21-reverser-spec-writer-combat-delivery-e5-item-cast-helpers-and-effect.md
resolution: "2026-10-21 architect: lane/s46d accepted with fixes (4: overclaim 1, misread 2, omission 1); review in the plan 0046 log; combat research-map row updated (C 236 / I 190 / L 23)."
---

Review `lane/s46d` (spec-writer, from main `1d0262a`): [combat/delivery](../../specs/combat/delivery.md) E5 updated from
[skills/0015](../../findings/skills/0015-item.md) §§ 4–7 and run:2026-10-21-cat-emu-item, as the
[released entry](2026-10-21-reverser-spec-writer-combat-delivery-e5-item-cast-helpers-and-effect.md) asked,
with the `lane/p46m12` review's fixes 1, 2, 6 and ruling 1. Not blocking.

- E5: two `[I]` bullets (the blank/1 cast draws nothing; `ItemTarget` 2 draws on an unfollowed unit) replaced by
  ten: five `[C]` (ADR-0021, each naming its boundary): handlers 20/21/30's draws up to `ItemCastAt*`; who casts, at
  what, with which effect flag, and the callers' tests and argument order (`EDX` the skill, the level the first stack
  word); `ITEMSKILL_Cast` up to `SrvStart`/`SrvDo` with no seed stepped for `ItemTarget` blank, 1, 3, 4 and the
  restore scoped to helper 2's no-room refusal; helper 2 given the cast's own caster and stepping its seed twice,
  scoped to the first try; do 151 up to `SkillMissileCreate`. Five `[I]`: helpers 3/4 and the corpse pick draw nothing
  past the boundary (static closures); helper 2's further tries and the item Teleport's move; **whose seed an item
  Teleport steps** (the composed handler → helper chain, ruling 1); **the effect flag 1 only from handler 20 without
  `ItemTgtDo`**, with `SKILLS_SrvDo`'s seven other calls passing 0 (fix 1); do 151's Chain Lightning starting at the
  target unit, after the boundary (fix 6).
- A3: the entry-36 item bullet scoped to the effect flag (stays `[I]`).
- Reimplementation notes: `SKILLS_PayCost`'s 0 for a zero-cost row refuses nothing (`[C]` for the 0, `[I]` for the
  three untested calls; fix 2); the item effect is only the attack/kill/hit cast's (`[I]`).
- Inputs: a Skills row (`ItemTarget`, `ItemTgtDo`, `ItemEffect`, `ItemCheckStart`, `srvmissilea`). Evidence: skills/0015
  and the run.
- Open questions: the `ItemTarget`-helpers `[L]` struck with its answer; the run bullet rewritten whole to name
  run:2026-10-21-cat-emu-item and ruling 1's two raise paths.
- Front matter: `{C: 74, I: 58, L: 4}` → `{C: 80, I: 63, L: 3}` (gate E6 count). **Research-map row (yours):** the
  combat row still says "C 230 / I 185 / L 24, the five front matters summed"; summed now it is C 236 / I 190 / L 23.
- Wiki: [combat](../../wiki/combat.md) states none of the changed facts (it names a monster's on-hit skill only as a
  boundary); no change, `based_on` already 2026-10-21.
- No other open spec-writer entry is combat-only; none folded in.

Gate fast tier green before commit.
