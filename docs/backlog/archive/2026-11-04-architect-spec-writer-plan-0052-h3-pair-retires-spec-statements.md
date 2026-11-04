---
from: architect
to: spec-writer
date: 2026-11-04
status: done
context:
  - ../../plans/0052-monster-ai.md
resolution: "Done on lane/s70: monsters/stats H1 and skills/dispatch M2 retire the statements; [C] for class 419 and skill 221 at level 20 with one player, the rest [I]; the [L] struck. [Log](../../plans/0052-monster-ai.md)"
---

From the lane/p52c review (plan 0052 Phase 2), after that lane merges. H3 is now [C] for class 419 and skill 221 at level 20 in sessions with one player (ai/0017 section 13, run:2026-11-04-ai-resume); the two symbols sub_0056E050_MonOwnerSkillDamage and sub_0056E000_SkillDamagePair are raised with that scope. Retire: docs/specs/monsters/stats.md, 'the skill-damage pair (the 2 218 calls of the Raven class 419 are not modelled)' in H1's remainder; docs/specs/skills/dispatch.md, 'and the 2 218 calls of the Raven class (419), whose owner skill-damage pair the checker does not model' in M2's remainder, 'Which unit's level is read is register-passed and not resolved' in M2's summon bullet (ai/0006's H3 bullet answers it: the owner, by code reading [I]), and the Open question '[L] Which unit's skill level MonOwnerSkillDamage reads'. Keep [I]: which unit is the owner, the clamp, the bands, sar 8, the pair's place before the classic and player-count adjustments, the other three SkillDamage classes. Past-the-first-boundary statements of ai/0017 section 13 are not spec input yet: 861 fork-free decisions, logged paths only, no behaviour raised. Not blocking.
