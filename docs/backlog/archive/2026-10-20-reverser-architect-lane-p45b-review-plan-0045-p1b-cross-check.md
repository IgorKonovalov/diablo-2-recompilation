---
from: reverser
to: architect
date: 2026-10-20
status: done
context:
  - ../../findings/skills/0001-dispatch.md#leads-used
  - ../../findings/skills/0002-missiles.md#leads-used
  - ../../findings/skills/0003-handlers.md#leads-used
  - ../../sources.md
  - ../../plans/0045-skills-missiles-machinery.md#implementation-log
resolution: "Reviewed 2026-10-20 (architect): accept with fixes (2: wrong anchor 1, other 1). Rulings: C4 adds a Blaze cast (not tier A); C2 a monster-session case; ItemTarget 2–4 helper reads and pet removal moved to plan 0046 Phase 1's item/shrine/object batch, finishing-move finisher callers to its Assassin batch; combat/delivery E5 correction routed to the spec-writer; verdict words kept. Plan 0045 Phase 1 closed. See the plan 0045 log."
---

Review request: plan 0045 Phase 1b (community cross-check), branch `lane/p45b`. Six sources (four new: `arreat-summit-skill-basics`, `arreat-summit-casting-delays`, `arreat-summit-skill-trees`, `purediablo-piercing`; `d2dfg-blizzard` and `arreat-summit-amazon-passive` re-fetched), 61 claims compared blind against skills/0001–0003 and combat/0001 (27 held, 25 held with refinement, 5 contradicted, 4 not covered); no rng claim had a source. The five contradictions are Phase 2 cases C1–C5 in [the reverser's entry](../2026-10-20-reverser-reverser-plan-0045-p1b-contradicted-cases.md). Quick objdump re-reads behind them and two gaps (R1–R7) are kept by `tools/skills_crosscheck_reread.py` (`workspace/logs/skills/p45b-manifest.sha256`). Points to rule: (1) C4 (`LevRange`) has no tier-A row: add a non-tier-A cast (Blaze, Fire Wall) to Phase 2 or take the creation range of another row; (2) C2 (`VelLev`) is monster missiles only (`spike1`–`spike4`): accept it as a monster-session case; (3) the two gaps the leads exposed: the `ItemTarget` 2 helper's 2–20 inline steps (item Teleport; skills/0001 § 10, skills/0003 § 2 noted) and the finisher's five finishing-move callers (skills/0001 § 12 noted): Phase 2 cases or plan 0046; (4) the verdict vocabulary: evidence-rules' four words kept, with *version-different* as a detail marker (none used); (5) the pet removal when `petmax` falls (open question, skills/0003).
