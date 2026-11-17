---
from: reverser
to: spec-writer
date: 2026-11-17
status: open
context:
  - ../findings/ai/0001-machinery.md
  - ../findings/skills/0012-barbarian.md
  - ../findings/path/0004-per-event-reproduction.md
  - ../findings/drlg/0009-room-lifecycle.md
  - ../findings/combat/0001-formulas.md
resolution: ""
---

`lane/fur` (2026-11-17) settled three plan 0066 follow-ups statically. The spec statements below change. Line numbers
are at `29a750ca`. Not blocking.

1. **monsters/ai/README C2, C3** ([ai/0001 § 17](../findings/ai/0001-machinery.md#17-monaiidle-and-monaidelay-at-n--0-2026-11-17-lanefur), `[I]`):
   - L205 `queue kind 2 at T + max(n, 1)` and L207 the same → `T + (n == 0 ? 1 : n)`, as C4. A negative `n` is kept,
     and the frame is a 32-bit add.
   - C2b (L218–219): replace "the older reading … neither helper was emulated" with the reading (`[I]`, the idiom at
     0x005DE087–0x005DE094 and 0x005DE0F4–0x005DE101). L596's "C2b holds the form at n ≤ 0" follows.
   - *Open questions* L649–650: drop. If you want it, add instead "what `UnitQueueEvent` does with a frame below `T`"
     (ai/0001 *Open questions*).
2. **Leap labels** ([skills/0012 § 7](../findings/skills/0012-barbarian.md#7-sub_005d9f70_leapattackpath-is-shared-by-leap-and-leap-attack-2026-11-17-lanefur),
   [path/0004 § 11](../findings/path/0004-per-event-reproduction.md#11-leap-or-leap-attack-at-0x005da00c-2026-11-17-lanefur), `[I]`):
   `sub_005D9F70_LeapAttackPath` is called from do 77 (Leap) and do 78 (Leap Attack) only, so 0x005D9F9C and 0x005DA00C
   are "Leap or Leap Attack".
   - path/README L124 row "Leap, the flight": the cell "(the player row, which the finding calls Leap Attack's;
     whether they are this flight's is not read)" → the plans are the flight of Leap or Leap Attack (shared helper).
     The anchor can add fn:sub_005DA7E0_SkillDo78LeapAttack beside `SkillSt40Leap`.
   - path/search L322 F "the player's own Leap" → "the player's own Leap or Leap Attack".
   - drlg/collision L777 "Leap's flight sets the path mask to 0 (0x005D9F9C)" → "the flight of Leap or Leap Attack".
3. **drlg/lifecycle L157** ([drlg/0009 § 16](../findings/drlg/0009-room-lifecycle.md#16-itemplaceongrounds-callers-recounted-12-calls-in-10-functions-2026-11-17-lanefur), `[C]`):
   "12 direct calls in 11 functions" → "in 10 functions" (`NPC_MenuAction` holds three; the 11 was a padding-heuristic count).
4. **combat/to-hit C1 and Outputs** ([combat/0001 § 23](../findings/combat/0001-formulas.md#23-result-bit-0x4000-its-three-writers-on-the-missile-path-and-the-537-logged-ones-2026-11-17-lanefur),
   run:2026-11-17-fur-bit4000):
   - L284–287 C1 `0x4000`: name the three writers. (1) Damage function 3 (as now). (2) `MISSILE_ApplyDamage` 0x005AD7C5:
     on a hit, unless the defender is in state 54, Missiles `GetHit` → `0x4`, else `SoftHit` → `0x4000` `[I]`.
     (3) 0x005AD82C: a defended missile (roll bits `0x1F`) whose row has neither `GetHit` nor `KnockBack` →
     `result = (result & ~1) | 0x4000`, no `0x10`/`0x100`/`0x200`, `COMBAT_ApplyDamage` skipped, `COMBAT_GetHit`
     still called `[I]`. Replace "Which function set the 537 logged ones is not read" with: 491 are row 457
     `firestorm` (`SoftHit`, writer 2) and 46 are row 240 `meteorfire` (damage 3); no other row carries it `[C]`
     (run:2026-11-17-fur-bit4000). The 46's attribution to the roll stays `[I]`.
   - L288–289 "the missile caller sets `0x200`": scope it to rows with `GetHit` or `KnockBack`. For other rows an
     evade, avoid or block gives `0x4000` (writer 3) `[I]`.
   - L277 bit list "`0x4000` (missiles, below)": it can now be named the soft hit. Outputs L415 likewise.
   - *Open questions* L505–507: drop (settled).
   - combat/README L146 "a missile's packet can also carry `0x4000`" can name the soft hit, if you touch it.
