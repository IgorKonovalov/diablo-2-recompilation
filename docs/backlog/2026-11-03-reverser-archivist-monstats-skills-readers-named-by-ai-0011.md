---
from: reverser
to: archivist
date: 2026-11-03
status: open
context:
  - ../findings/ai/0011-batch10.md
resolution: ""
---

Link the readers found by [ai/0011](../findings/ai/0011-batch10.md) from the table docs: MonStats aip slots per row as § 1 and § 2 read them (rows 126, 127, 129-134, 136, 137, 139, 141; row 126 leaves aip3 unread, row 129 aip2; rows 130 (aip3, aip4) and 139 (aip1, aip2) read slots that differ per record; row 133's three records each feed their own class think, so the same slot means a different thing per Ancient; rows 131 and 132 read none; § 1, [I]); MonStats genericSpawn (+0x00E bit 5) read through the mask 0x006CE27C by row 129's class pick 0x005E6020, which takes a random entry of the level's monster region with that bit, else the first, else 496 (§ 2.3, [I]; MonStats § bit columns has it [L] 'name'); MonStats Skill1/Sk1mode for rows 130, 133, 134 (Skill2..4 unread), 141, and the constant skills that replace the records' slots in rows 126 (0x006E3514), 129, 132, 136, 137 (§ 1, [I]); Skills aurastate (+0x080) and auratargetstate (+0x082) as AI readers in rows 133 (ancientbarb2, admitted in (0, States count]) and 134 (admitted in [0, States count)) (§§ 2.8, 2.9, [I]). [C] for the maps up to their first boundary by run:2026-11-03-ai-cat-emu-10 where § 2 says so. No column meaning changes; links only.
