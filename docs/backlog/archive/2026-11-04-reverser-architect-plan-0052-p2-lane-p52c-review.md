---
from: reverser
to: architect
date: 2026-11-04
status: done
context: []
resolution: "Reviewed: accept with fixes (13), plan 0052 log, 2026-11-04. Six rows' 861 fork-free decisions [C] past the first boundary; rows 6, 61, 67 [I]; H3 [C] at one level; raises scoped; catalogue sample short."
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

[2026-11-04] from reverser → architect: review `lane/p52c` (plan 0052 Phase 2, no game; rotated at about 250k tokens): [ai/0017 § 13](../../findings/ai/0017-phase2-second-run.md), run:2026-11-04-ai-resume. Done: the six fixes with a test each, `tools/ai_resume_review.py` retired, the tier table, the rerun (7 444 resumed, 8 mismatches, 87 stopped), H3, logger rev 5. Please rule on: (1) the nine rows proposed `[C]` past the first boundary (6, 13, 21, 30, 37, 61, 64, 67, 89), given that each row's outcome mix is uneven and the reversed-branch control reverses all branches at once; (2) H3's `[C]` with one owner level and 101 separating calls, and raising `sub_0056E050_MonOwnerSkillDamage` and `sub_0056E000_SkillDamagePair`, whose outputs are logged only as the stats MonAttackStats writes; (3) whether batch 12's rows may count for the catalogue sample, since rows 54 and 99 have no call past the first. Not done, in the resume note (§ 14): the first-boundary maps for rows 130, 54, 99, 100 and the state thinks, and the two backlog entries (waypoint and pinned seed; stage check), which stay open and unstarted. Logger rev 5 has not run in a game. `docs/specs/monsters/stats.md` and `docs/specs/skills/dispatch.md` still say the Raven calls are not modelled: the spec-writer's after this review.
