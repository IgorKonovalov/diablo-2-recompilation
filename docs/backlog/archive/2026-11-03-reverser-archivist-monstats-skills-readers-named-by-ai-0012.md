---
from: reverser
to: archivist
date: 2026-11-03
status: done
context:
  - ../../findings/ai/0012-batch11.md
resolution: "Linked in MonStats (threat, aip1..aip5 of row 128, aip1 of row 138, Skill1..Skill8 of rows 51, 128, 135, 140, new boss-B reader block) and Skills (attackrank, aurastate); tags are the finding's, Baal's curse sign tests [C] as the bact control row gives; [MonStats](../../tables/MonStats.md#ai-columns-plan-0052-phase-0), [Skills](../../tables/Skills.md)"
---

The request: what is needed, from whom, and why. Not blocking / blocking <what>.

Link the readers found by [ai/0012](../../findings/ai/0012-batch11.md) from the table docs: MonStats `threat` (`+0x4E`): both threat scores return 0 for a monster candidate at threat ≤ 1 (§ 2.4; the column's [L] "not looked for" notes in MonStats.md can name these readers, [I]); Skills `attackrank` (`+0x18E`): the scores' `K` term, skill level × rank over left and right skills (§ 2.4, [I]); MonStats `aip1`..`aip5` of row 128 and `aip1` of row 138 (§§ 1, 2.5, 2.6, [I]; Diablo's and Baal's rows read no aip slot, `b11-aip.txt`); MonStats `Skill1`..`Skill8` with `Sk1mode`..`Sk8mode` for rows 51 and 128 (§§ 2.2, 2.5), and `Skill5`..`Skill7` only for rows 135/140 whose four attack skills are constants in the action (§ 2.9); Skills `aurastate` as Diablo's `Skill8` gate (§ 2.2). Row 145 `UberBaal` and row 147 `UberDiablo` read nothing (`ret 4`, § 2.10). Tags are the finding's own; [C] only for the maps named in its § 4. No column meaning changes beyond `threat` and `attackrank` gaining a reader; links only.
