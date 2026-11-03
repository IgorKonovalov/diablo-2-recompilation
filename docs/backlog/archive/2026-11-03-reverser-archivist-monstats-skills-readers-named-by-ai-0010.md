---
from: reverser
to: archivist
date: 2026-11-03
status: done
context:
  - ../../findings/ai/0010-batch9.md
resolution: "MonStats: pool-F readers block (aip slots per row, row 122 shared parameter table, Skill1..5/Sk1mode..Sk5mode by row and state 16, Sk1lvl of row 124, count guards), genericSpawn and the 13-rows bullet; [I] as ai/0010 gives, [C] only for the maps to their first boundary [MonStats](../../tables/MonStats.md)"
---

Link the readers found by [ai/0010](../../findings/ai/0010-batch9.md) from the table docs: MonStats aip slots per row as § 1 and § 2 read them (rows 116-125; row 122 reads none of its own aip slots but the slots of the fixed records 492-495 imp1..imp4, which settles the row 122 slot disagreement of MonStats § AI columns as a shared parameter table; row 119's aip3 0/0/0 in succubuswitch1 is the curse and step-away chance; rows 116, 117 and 121 leave aip5 (and 117 aip1, aip4) unread; § 1, [I]); MonStats Skill1..Skill5 with Sk1mode..Sk5mode for rows 118-125 and state 16 (the > 0 sign tests of rows 118/119, Skill3 tested != 0 by row 120, row 125 using Skill1 with the constant mode 5 and no sign test, state 16 using imp1's Skill3 or Skill5 by slot; § 1, §§ 2.3-2.13, [I]); MonStats Sk1lvl as the skill-level range of row 124 (through SKILLS_GetSkillLevel, clamped at 0; § 2.12, [I]); the MonStats count guards on the records 492-495 and the base ids 453/461 of the two callbacks (§§ 2.5, 2.6, 2.8). [C] for the maps up to their first boundary by run:2026-11-03-ai-cat-emu-9 where § 2 says so. No column meaning changes; links only.
