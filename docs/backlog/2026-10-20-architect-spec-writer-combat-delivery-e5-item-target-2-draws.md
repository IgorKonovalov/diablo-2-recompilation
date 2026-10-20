---
from: architect
to: spec-writer
date: 2026-10-20
status: open
context:
  - ../specs/combat/delivery.md
  - ../findings/skills/0001-dispatch.md#10-item-granted-skills
  - ../findings/skills/0003-handlers.md#2-item-event-casts
  - ../plans/0045-skills-missiles-machinery.md#implementation-log
resolution: ""
---

Correction to [combat/delivery](../specs/combat/delivery.md) § E5 (lane/cfix2, now on main), from the plan 0045 Phase 1b review (lane/p45b). E5 says "An item cast draws nothing of its own: the cast helpers and `ITEMSKILL_Cast` hold no draw". That misses a path: `ITEMSKILL_Cast` calls the `ItemTarget` helpers (2 at `0x005FDB9F` → `0x005FD850`, 3 at `0x005FDBE1` → `0x005FD9C0`, 4 at `0x005FDBF3` → `0x005FDA10`; objdump, review 2026-10-20), and helper 2 steps the seed at `+0x20` of the unit it is given twice per try, inline (`low % 40 − 20` added to x and to y), at most 10 tries until `0x0064D870` returns 0: 2 to 20 steps (skills/0001 § 10 and skills/0003 § 2 dated notes, `p45b-reread.txt` R5). The one stock `ItemTarget` 2 row is Teleport. Which unit the helper is given (caster or target) is unfollowed, and whether 3 (a corpse pick through `0x0056E390`) and 4 draw is unread (plan 0046 Phase 1, item batch). Requested: scope the E5 sentence to `ItemTarget` blank or 1 (and the cast helpers `0x005FDCA0`/`0x005FDD60`), add an `[I]` statement for helper 2 (anchors `0x005FD900`–`0x005FD98A`, fn:ITEMSKILL_Cast@0x005FDA80), and an `[L]` under *Open questions* for its unit and for helpers 3 and 4; check combat/README B6 and rng/seeds for the same claim. No tag raised; the spec stays reviewed if only this scoping and `[I]`/`[L]` are added.
