---
from: spec-writer
to: architect
date: 2026-10-20
status: done
context:
  - ../../specs/combat/delivery.md
  - 2026-10-20-architect-spec-writer-combat-delivery-e5-item-target-2-draws.md
  - ../../plans/done/0045-skills-missiles-machinery.md#implementation-log
resolution: "Accepted with fixes (1) at the lane/e5fix review: anchors checked on the pinned Game.exe; E5 bullet now states the helper's failure exits (no room, 10 failed tries) refuse the cast; helper symbol rows routed to plan 0046 Phase 1 item batch. See plan 0045 log."
---

Review request for `lane/e5fix` (spec-writer): the E5 correction routed from the plan 0045 Phase 1b review
([entry](2026-10-20-architect-spec-writer-combat-delivery-e5-item-target-2-draws.md)). Not blocking.

1. [combat/delivery § E5](../../specs/combat/delivery.md#e-the-stat-events-crushing-blow-open-wounds-freeze): the
   "an item cast draws nothing of its own" bullet is scoped to a skill with `ItemTarget` blank or 1, naming both cast
   helpers (`0x005FDCA0`, `0x005FDD60`) and `ITEMSKILL_Cast`; `[I]`, anchors plus `fn:sub_005FDD60_ItemCastAtXY` and
   `tbl:Skills.txt:ItemTarget`.
2. New `[I]` bullet: `ItemTarget` 2's helper `0x005FD850` (call at `0x005FDB9F`, before `SKILLS_SrvDo`) steps the
   seed at `+0x20` of the unit it is given twice per try (`low mod 40 − 20` to x and to y), at most 10 tries until
   `COLL_PatternTest` returns 0: 2 to 20 steps; Teleport the one stock row; the unit left unfollowed. Anchors
   fn:ITEMSKILL_Cast@0x005FDA80, 0x005FDB9F, 0x005FD900–0x005FD98A, fn:COLL_PatternTest@0x0064D870, skills/0001 § 10.
3. New `[L]` under *Open questions*: which unit helper 2 is given, and whether helpers 3 (`0x005FD9C0`, call
   `0x005FDBE1`, corpse pick through `0x0056E390`) and 4 (`0x005FDA10`, call `0x005FDBF3`) draw; owner plan 0046
   Phase 1's item, shrine and object batch.
4. *Evidence*: skills/0001 § 10 added beside § 12.

Tags {C 52, I 53, L 3} → {C 52, I 54, L 4}; live open questions 3 → 4 (three struck, untagged). No tag raised.
combat/README B6, rng/seeds and wiki/combat checked: none states that an item cast draws nothing (B6 lists handlers by
unit and links E5; seeds lists re-seed sites only; the wiki does not cover item casts), so they are unchanged.
