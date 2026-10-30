---
from: reverser
to: architect
date: 2026-10-30
status: open
context:
  - ../findings/player/0001-creation.md
  - ../plans/0038-inferred-claims-sweep.md
resolution: ""
---

Review of lane/h6gs (plan 0038 H6g shortfalls, static read; owner decision 2026-10-30). Finding: player/0001 § Plan 0038 H6g shortfalls, static read (2026-10-30). Proposed ledger: rows 2 and 29 stay open, class (b), batch H6g (no static second source for J2: the three amounts are immediates of 0x0058C5C0 only, three direct callers), routed to a corrected anc session (walk to the summit door + (-9, -49) until OBJS lists 546, operate it, no town portal on 120; a level 20-35 Normal character to reach the cut, which binds for L 1-35 in Normal per grant-cut.txt; a new EG0 logger line); not d-owner. Rows 3 and 30 stay raised in part, the remainder narrowed: proposed [C] by evidence rule 1 (writer/reader pair, the writer logged at CCX in run:2026-10-27-sweep-player): the pickup reads the corpse's stat 13 (0x0057FBBB) that CorpseCreate writes (0x0057F883) and the inventory owner id +0x24 (INV_GetOwnerId at 0x0057FBA1) that CorpseCreate writes with the dead player's id (INV_SetOwnerId at 0x0057F8B5); the pickup's run (zeroing, AddExperienceDirect into PLAYER_AddExperience) stays [I]. Row 33 unchanged. No class change: totals as main 8dddf4c5 stands (1 526). Symbols: 7 new [I], none raised. Refinement carried to player/0001 § 7, § P1c, the Functions row and quests/0001: the grant's cut is T(L+1) - T(L), the width of level L+1 (signed compare 0x0058C649). For you to rule on: (1) whether the writer/reader pair is enough to move part of the 3/30 remainder; (2) the spec J2 wording (spec-writer). The routing entry 2026-10-27-reverser-architect-plan-0038-h6g-shortfalls-ancients-altar-and-corpse.md is annotated, left open for this review to close.
