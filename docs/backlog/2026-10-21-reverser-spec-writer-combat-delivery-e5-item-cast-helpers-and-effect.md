---
from: reverser
to: spec-writer
date: 2026-10-21
status: open
context:
  - ../findings/skills/0015-item.md
  - ../specs/combat/delivery.md
resolution: ""
---

Not blocking; for review after the architect accepts plan 0046 batch `item` ([skills/0015](../findings/skills/0015-item.md)).
[combat/delivery](../specs/combat/delivery.md) E5 and its *Open questions* carry plan 0045's reading of the item cast;
the batch answers the open part and raises some of it:

- E5 "`ItemTarget` 2 draws in its target helper": the helper is given **the cast's caster** (`EDX = ESI` at
  `0x005FDB9B`; `[C]` under ADR-0021 with its two steps before the first collision test), and the caster is the
  handler's unit, or the event's other unit for handler 20 with `ItemTgtDo` (Teleport, the one stock `ItemTarget` 2 row,
  has it) (skills/0015 §§ 5, 6; the composition `[I]`). The *Open questions* `[L]` on the helpers can go: helpers 3 and
  4 make no draw before their boundaries and their static closures hold none.
- E5 "An item cast … draws nothing of its own": the handlers' chance draws are `[C]` now (20: one inline step of the
  unit's seed when there is no packet or its `+0x00` bit 5 is set; 21: `RNG_RangeB(unit, 100)` with packet `+0x04`
  bit 2; 30: one inline step always) (§ 6).
- New for the item effect: `ITEMSKILL_Cast`'s effect flag is 1 only from handler 20 without `ItemTgtDo`, so
  `ItemEffect` 36 and 151 replace the do function only for skill-on-attack/kill/hit stats (§ 6, `[I]`; no other call of
  `SKILLS_SrvDo` passes 1); do 151 passes `SkillMissileCreate` the target's offset from the caster (`[C]` up to that
  call), so the item Chain Lightning starts at the target unit (§ 4, after the boundary, `[I]`).
- `SKILLS_PayCost` returns 0 for a row with `mana` and `lvlmana` both 0, and none of its three calls (in `SKILLS_SrvStart`, in `SKILLS_SrvDo`, and `0x005D6B48`) tests the
  return (§ 7, `[I]`; `lane/p46m12` review): a zero-cost skill is not refused.
- `ItemCastAtUnit`/`ItemCastAtXY` take `EDX` the skill and the level as the first stack word (skills/0003 § 2's dated
  note corrects the reverse).
