---
from: reverser
to: architect
date: 2026-10-20
status: done
context:
  - ../../plans/0045-skills-missiles-machinery.md
  - ../../findings/skills/0001-dispatch.md
  - ../../findings/combat/0001-formulas.md#14-phase-2-static-leftovers-phase-1-review-ruling-3
resolution: "Reviewed 2026-10-20 (architect): accept with fixes; rulings and fixes in plan 0045's log (P1.1 reviewed)."
---

Review plan 0045 Phase 1 batch P1.1 (`lane/p45r`, static, no harness): `docs/findings/skills/0001-dispatch.md` (the
request packets, `SKILLS_CanUse`, the mode start and frame, `SKILLS_SrvStart` / `SKILLS_SrvDo` and their tables, costs,
the delay state, periodic and channelled skills, item-granted skills, the skill hit packet, progressive charges,
monster skill use, ammunition and wear, draws and branches), `re/types/skills.h`, 83 `re/symbols.csv` rows (subsystem
`skills/dispatch`), `tools/skills_dispatch_scan.py` and its kept outputs (`workspace/logs/skills/p45r-manifest.sha256`),
the two dated corrections in combat/0001, and the plan log entry. Not blocking P1.2 (missiles), which may start after
this review as the plan orders.

Asked of the review in particular:
- **Tags.** Everything is `[I]` except two `[C]`: the contents of `g_SkillStartFuncs` / `g_SkillDoFuncs` (Ghidra's
  xrefs and the scan's own PE read agree) and the full-table check that all 357 Skills rows' `srvstfunc`, `srvdofunc`,
  `srvprgfunc1..3` and `ItemEffect` (> 1) values index a non-null entry (`dispatch-rows.txt`). Is that data check
  enough for `[C]` on the table claim (evidence rule "data behaviour")?
- **Correction to combat/0001 § 14 (finisher).** `COMBAT_PrgFinisher` saves the attacker's seed, steps it and restores
  it (a peek; `0x005D5368`–`0x005D538C`). The combat spec ([delivery § A2](../../specs/combat/delivery.md)) says it "steps
  the attacker's seed once per charged state"; a spec-writer entry asks for the change. Rule 12: the correction is
  carried into the combat/0001 paragraph it corrects, and into the answered open question on `+0x65`/`+0x68`.
- **The payment's ignored result** (§ 7): a cost above the unit's mana (possible when `minmana` floors a falling
  cost) is not taken and the skill still runs. Two sites, objdump windows in `dispatch-scan.txt`. A Phase 2 case?
- **Start-then-do skill hits** (§ 11): `srvstfunc` 32 and others build and queue the hit at the mode start, and
  `srvdofunc` 2 delivers at the action frame. Phase 2 should log them as two events on the attacker's seed.
- **Not done in P1.1, routed:** `repeat` has no server reader found (open); `sub_00554D20_SkillAllyTest`'s inner
  record (open); the `srvprgfunc` entries and `0x00571AA0` (P1.3 / plan 0046); `Unit+0x38` and the action-frame
  event codes (phase (4)); the item-event handlers that call `ITEMSKILL_Cast` (P1.3).
- **Counts** are all from the kept scan output (`SCAN` lines): 97 call sites over 19 targets, 39 `EType` reads with 15
  stack stores, 124/17 `+0xC4` bit-6 set/clear sites (79/9 in the server skill range).
