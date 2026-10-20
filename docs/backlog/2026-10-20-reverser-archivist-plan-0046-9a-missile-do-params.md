---
from: reverser
to: archivist
date: 2026-10-20
status: open
context:
  - ../findings/skills/0004-missile-do-1-18.md
  - ../tables/Missiles.md
resolution: ""
---

Plan 0046 batch 9a ([skills/0004](../findings/skills/0004-missile-do-1-18.md)) settles which Missiles columns the missile server do functions 2 and 6-18 read; please link them in [Missiles](../tables/Missiles.md) (meaning cells, `[C]` or `[I]` as the finding tags them, not blocking). `SubMissile1` (+0x018): read by do 2, 6, 8, 9, 10, 12, 15, 17 (§§ 3-7). `Param1` (+0x038): period of do 7, 11, 14, 15; the radius base of do 8; the window and portal bound of do 17; the opening frame of do 18 (`Range − Param1`); the elapsed bound of do 16. `Param2` (+0x03C): period of do 8 (base), 16 and 17, gold period of do 18 (`4·Param2`), distance cap of do 11, direction step of do 15, the skill do-table entry of do 14 (already). `Param3` (+0x040): level divisor of do 8, step of do 11, scatter radius of do 17 and gold offset of do 18. `Param4` (+0x044): do 17's portal level (already noted for PermPortalAtUnit). `Param5` (+0x048): do 17's portal frame bound. `Range` (+0x096): do 17 and 18 read the raw column, not the creation range. `Size` (+0x18A): the edge distance of do 7 and 11 (§ 9). Skills `calc1`/`calc2` (+0x138/+0x13C): do 10's radius and period (Blizzard). Stock values in workspace/logs/skills-cat-9a/rows.txt.
